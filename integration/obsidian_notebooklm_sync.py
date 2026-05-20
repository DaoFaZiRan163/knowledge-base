"""
FDE Knowledge Hub - Obsidian → NotebookLM 同步模块

职责：
1. 扫描 Obsidian core/ 目录中的 Markdown 笔记
2. 将笔记转换为 NotebookLM 可导入的纯净格式（本地导出备用）
3. 将笔记向量化并写入 Qdrant，实现本地 RAG 搜索
4. 通过内容哈希维护增量同步状态（未变更的文档跳过）

NotebookLM 目前无公开 REST API，sync_document 的"上传"步骤会将
转换后的文档写到 sync_output/notebooklm/ 目录，可手动拖入 NotebookLM
或配合 Google Drive API 自动同步。
"""

import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import httpx
    import yaml
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as e:
    print(f"请安装依赖: pip install -r requirements.txt  (缺失: {e})")
    raise


# 常用模型的向量维度映射（与 knowledge_ingestion.py 保持同步）
_KNOWN_DIMS = {
    'embo-01': 1536,
    'text-embedding-3-small': 1536,
    'text-embedding-3-large': 3072,
    'text-embedding-ada-002': 1536,
    'BAAI/bge-m3': 1024,
    'BAAI/bge-large-zh-v1.5': 1024,
    'BAAI/bge-large-en-v1.5': 1024,
    'netease-youdao/bce-embedding-base_v1': 768,
    'Qwen/Qwen3-Embedding-0.6B': 1024,
    'Qwen/Qwen3-Embedding-4B': 2560,
    'Qwen/Qwen3-Embedding-8B': 4096,
}


class ObsidianNotebookLMSync:
    """Obsidian Vault → NotebookLM / Qdrant 同步器"""

    COLLECTION_NAME = "fde_knowledge"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.core_path = self.project_root / "core"
        self.output_path = self.project_root / "sync_output" / "notebooklm"
        self.state_file = self.project_root / "sync_output" / "sync_state.json"

        # ── 嵌入客户端初始化（优先级：SiliconFlow > MiniMax > OpenAI）────
        from openai import OpenAI as _OpenAIClient
        sf_key = config.get("SILICONFLOW_API_KEY")
        minimax_key = config.get("MINIMAX_API_KEY")

        if sf_key:
            # SiliconFlow：OpenAI 兼容，直接使用 openai 包
            self._use_minimax_embed = False
            self._embed_client = _OpenAIClient(
                api_key=sf_key,
                base_url=config.get("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
            )
            self._embedding_model = config.get("SILICONFLOW_EMBEDDING_MODEL", "BAAI/bge-m3")
        elif minimax_key:
            # MiniMax：嵌入接口格式特殊，使用 httpx 直接调用（见 _embed_texts_batch）
            self._use_minimax_embed = True
            self._minimax_api_key = minimax_key
            self._minimax_base_url = config.get("MINIMAX_BASE_URL", "https://api.minimaxi.chat/v1")
            self._embedding_model = config.get("MINIMAX_EMBEDDING_MODEL", "embo-01")
            self._embed_client = None
        else:
            # 回退到原生 OpenAI
            self._use_minimax_embed = False
            self._embed_client = _OpenAIClient(api_key=config.get("OPENAI_API_KEY"))
            self._embedding_model = "text-embedding-3-small"

        self.VECTOR_DIM = _KNOWN_DIMS.get(self._embedding_model, 1024)

        # ── Qdrant 客户端 ────────────────────────────────────────────────
        self.qdrant = QdrantClient(
            url=config.get("QDRANT_URL", "http://localhost:6333"),
            api_key=config.get("QDRANT_API_KEY") or None,
        )
        self._ensure_collection()

        # ── 文本分块器 ───────────────────────────────────────────────────
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            length_function=len,
        )

        # ── 同步状态（content hash → synced_at）────────────────────────
        self._state: Dict[str, str] = self._load_state()

    # ─────────────────────────────────────────────────────────────────────
    # 公开接口（由 cli.py sync 命令调用）
    # ─────────────────────────────────────────────────────────────────────

    def scan_core_documents(self) -> List[Dict[str, Any]]:
        """扫描 core/ 目录，返回待同步文档列表。

        每个文档 dict 包含：
          title, path, category, difficulty, tags, content_hash, content
        """
        if not self.core_path.exists():
            return []

        docs = []
        for md_file in sorted(self.core_path.rglob("*.md")):
            # 跳过 Obsidian 系统文件（00-* 前缀）
            if md_file.name.startswith("00-"):
                continue

            raw = md_file.read_text(encoding="utf-8", errors="replace")
            frontmatter, body = self._parse_frontmatter(raw)
            content_hash = hashlib.md5(raw.encode()).hexdigest()

            docs.append(
                {
                    "title": frontmatter.get("title", md_file.stem),
                    "path": str(md_file),
                    "relative_path": str(md_file.relative_to(self.project_root)),
                    "category": self._infer_category(md_file, frontmatter),
                    "difficulty": frontmatter.get("difficulty", "intermediate"),
                    "tags": frontmatter.get("tags", []),
                    "content_hash": content_hash,
                    "content": body,
                    "frontmatter": frontmatter,
                }
            )

        return docs

    def sync_document(self, doc: Dict[str, Any]) -> bool:
        """同步单个文档。

        步骤：
          1. 检查内容是否有变更（hash 比对），无变更则跳过
          2. 将 Obsidian markdown 转换为纯净文本
          3. 导出到 sync_output/notebooklm/ 目录
          4. 分块向量化后 upsert 到 Qdrant
          5. 更新同步状态

        Returns:
          True 表示实际执行了同步，False 表示内容未变更已跳过
        """
        content_hash = doc["content_hash"]
        if self._state.get(doc["path"]) == content_hash:
            return False

        import time

        clean_text = self._convert_obsidian_to_plain(doc["content"], doc["frontmatter"])
        self._export_for_notebooklm(doc, clean_text)

        try:
            self._index_to_qdrant(doc, clean_text)
            # 每次嵌入后等待 35s，将 RPM 控制在 MiniMax 免费版限额（2 RPM）之内
            if self._use_minimax_embed:
                time.sleep(35)
        except RuntimeError as e:
            # 嵌入限速或失败时，本地导出已完成，仅记录告警，不阻断同步流程
            print(f"[警告] {doc['title']} 向量索引失败（{e}），本地导出已保存，可稍后重新同步")

        self._state[doc["path"]] = content_hash
        self._save_state()
        return True

    # ─────────────────────────────────────────────────────────────────────
    # Obsidian → 纯净文本转换
    # ─────────────────────────────────────────────────────────────────────

    def _convert_obsidian_to_plain(
        self, body: str, frontmatter: Dict[str, Any]
    ) -> str:
        """将 Obsidian Markdown 转换为 NotebookLM 友好的纯净 Markdown。

        处理：
          - [[wikilinks]] → 普通文本
          - ![[embeds]]   → 移除
          - Mermaid 代码块 → 移除（NotebookLM 不支持）
          - Obsidian callout > [!NOTE] → 转为普通引用块
          - Dataview 代码块 → 移除
          - 多余空行压缩
        """
        text = body

        # 移除 Mermaid / Dataview 代码块
        text = re.sub(r"```(?:mermaid|dataview).*?```", "", text, flags=re.DOTALL)

        # 移除嵌入文件 ![[...]]
        text = re.sub(r"!\[\[.*?\]\]", "", text)

        # [[链接|显示文本]] → 显示文本
        text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", text)
        # [[链接]] → 链接文字
        text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

        # Obsidian callout: > [!NOTE] → > **NOTE**
        text = re.sub(
            r"^> \[!(\w+)\](.*)$",
            lambda m: f"> **{m.group(1)}**{m.group(2)}",
            text,
            flags=re.MULTILINE,
        )

        # 压缩连续空行（超过 2 行的压缩为 2 行）
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 拼接 frontmatter 摘要作为文档头
        header_parts = [f"# {frontmatter.get('title', '')}"] if frontmatter.get("title") else []
        if frontmatter.get("tags"):
            tags = frontmatter["tags"]
            if isinstance(tags, list):
                header_parts.append(f"**标签**: {', '.join(tags)}")
        if frontmatter.get("difficulty"):
            header_parts.append(f"**难度**: {frontmatter['difficulty']}")

        header = "\n".join(header_parts)
        return (header + "\n\n" + text).strip()

    # ─────────────────────────────────────────────────────────────────────
    # 导出到本地目录（供手动上传 NotebookLM）
    # ─────────────────────────────────────────────────────────────────────

    def _export_for_notebooklm(self, doc: Dict[str, Any], clean_text: str):
        """将纯净文档写入 sync_output/notebooklm/<category>/<title>.md"""
        category = doc.get("category", "uncategorized")
        category_dir = self.output_path / category
        category_dir.mkdir(parents=True, exist_ok=True)

        safe_title = re.sub(r'[\\/:*?"<>|]', "_", doc["title"])
        out_file = category_dir / f"{safe_title}.md"
        out_file.write_text(clean_text, encoding="utf-8")

    # ─────────────────────────────────────────────────────────────────────
    # Qdrant 向量索引
    # ─────────────────────────────────────────────────────────────────────

    def _index_to_qdrant(self, doc: Dict[str, Any], clean_text: str):
        """将文档分块向量化后 upsert 到 Qdrant。

        批量向量化：一次 API 调用处理文档所有 chunks，降低 RPM 消耗。
        """
        chunks = [c for c in self._splitter.split_text(clean_text) if len(c.strip()) >= 30]
        if not chunks:
            return

        vectors = self._embed_texts_batch(chunks, embed_type="document")

        synced_at = datetime.now().isoformat()
        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            point_id = int(
                hashlib.md5(f"{doc['path']}:{i}".encode()).hexdigest(), 16
            ) % (2**32)

            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "text": chunk,
                        "title": doc["title"],
                        "source": doc["path"],
                        "relative_path": doc["relative_path"],
                        "category": doc["category"],
                        "difficulty": doc.get("difficulty", "intermediate"),
                        "tags": doc.get("tags", []),
                        "chunk_index": i,
                        "synced_at": synced_at,
                    },
                )
            )

        self.qdrant.upsert(collection_name=self.COLLECTION_NAME, points=points)

    def _embed_texts_batch(
        self, texts: List[str], embed_type: str = "document", _retries: int = 3
    ) -> List[List[float]]:
        """批量向量化文本列表（一次 API 调用），失败时回退逐条处理。"""
        import time

        if self._use_minimax_embed:
            for attempt in range(_retries):
                resp = httpx.post(
                    f"{self._minimax_base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self._minimax_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"model": self._embedding_model, "texts": texts, "type": embed_type},
                    timeout=60,
                )
                data = resp.json()
                base = data.get("base_resp", {})
                if base.get("status_code", 0) == 0:
                    return data["vectors"]
                if "rate limit" in base.get("status_msg", "").lower() and attempt < _retries - 1:
                    # 固定等待 65s 确保跨过 60s RPM 窗口
                    print(f"[限速] MiniMax RPM 超限，等待 65s 后重试 ({attempt + 1}/{_retries})...")
                    time.sleep(65)
                    continue
                raise RuntimeError(f"MiniMax 嵌入失败: {base.get('status_msg')}")
            raise RuntimeError("MiniMax 嵌入：超出最大重试次数")
        else:
            response = self._embed_client.embeddings.create(
                model=self._embedding_model, input=texts
            )
            return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

    def _embed_text(
        self, text: str, embed_type: str = "query", _retries: int = 3
    ) -> List[float]:
        """向量化文本。MiniMax 与 OpenAI 采用不同接口路径（见 knowledge_ingestion.py 注释）。

        MiniMax 免费版有 RPM 限制，遇到限速时自动等待后重试（最多 _retries 次）。
        """
        import time

        if self._use_minimax_embed:
            for attempt in range(_retries):
                resp = httpx.post(
                    f"{self._minimax_base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self._minimax_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._embedding_model,
                        "texts": [text],
                        "type": embed_type,
                    },
                    timeout=30,
                )
                data = resp.json()
                base = data.get("base_resp", {})
                status_code = base.get("status_code", 0)
                if status_code == 0:
                    return data["vectors"][0]
                # 限速错误：等待后重试
                if "rate limit" in base.get("status_msg", "").lower() and attempt < _retries - 1:
                    # 固定等待 65s 确保跨过 60s RPM 窗口
                    print(f"[限速] MiniMax RPM 超限，等待 65s 后重试 ({attempt + 1}/{_retries})...")
                    time.sleep(65)
                    continue
                raise RuntimeError(f"MiniMax 嵌入失败: {base.get('status_msg')}")
            raise RuntimeError("MiniMax 嵌入：超出最大重试次数")
        else:
            response = self._embed_client.embeddings.create(
                model=self._embedding_model, input=text
            )
            return response.data[0].embedding

    # ─────────────────────────────────────────────────────────────────────
    # 辅助方法
    # ─────────────────────────────────────────────────────────────────────

    def _ensure_collection(self):
        """确保 Qdrant 集合存在且维度匹配，否则重建。"""
        existing = {c.name for c in self.qdrant.get_collections().collections}
        if self.COLLECTION_NAME not in existing:
            self.qdrant.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(size=self.VECTOR_DIM, distance=Distance.COSINE),
            )
        else:
            info = self.qdrant.get_collection(self.COLLECTION_NAME)
            existing_dim = info.config.params.vectors.size
            if existing_dim != self.VECTOR_DIM:
                print(f"[重建集合] 维度变更 {existing_dim} → {self.VECTOR_DIM}")
                self.qdrant.delete_collection(self.COLLECTION_NAME)
                self.qdrant.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(size=self.VECTOR_DIM, distance=Distance.COSINE),
                )

    def _parse_frontmatter(self, raw: str):
        """解析 YAML frontmatter，返回 (frontmatter_dict, body_str)。"""
        match = re.match(r"^---\n(.*?)\n---\n?", raw, re.DOTALL)
        if match:
            try:
                fm = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                fm = {}
            body = raw[match.end():]
        else:
            fm = {}
            body = raw
        return fm, body

    def _infer_category(self, md_file: Path, frontmatter: Dict[str, Any]) -> str:
        """从 frontmatter 或目录路径推断分类。"""
        fm_cat = frontmatter.get("category")
        if fm_cat:
            if isinstance(fm_cat, list):
                return fm_cat[0]
            return str(fm_cat)

        parts = md_file.relative_to(self.core_path).parts
        # parts[0] is a subdirectory only when there are at least 2 parts
        if len(parts) >= 2:
            return parts[0]
        return "uncategorized"

    def _load_state(self) -> Dict[str, str]:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
