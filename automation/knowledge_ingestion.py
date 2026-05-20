"""
FDE Knowledge Hub - Knowledge Ingestion System
智能知识摄取系统，支持多种格式的文档处理和知识提取
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import hashlib
from datetime import datetime

# ── Embedding 提供商优先级 ────────────────────────────────────────────────
# SiliconFlow（推荐）> MiniMax > OpenAI
#
# SiliconFlow / OpenAI：完全兼容 openai 包，直接调用即可。
# MiniMax：嵌入接口格式不同，使用 httpx 直接调用（见 _embed_text）：
#   - 参数名：texts（数组）而非 input（字符串）
#   - 额外参数：type 需传 "query" 或 "document"
#   - 响应格式：vectors（二维数组）而非 data[].embedding
#
# 向量维度随模型变化（_KNOWN_DIMS 维护常用模型→维度映射）：
#   SiliconFlow BAAI/bge-m3 → 1024，MiniMax embo-01 → 1536
try:
    import httpx
    from openai import OpenAI as _OpenAIClient
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    import fitz  # PyMuPDF for PDF text extraction
except ImportError as e:
    print(f"请安装依赖: pip install -r requirements.txt")
    print(f"缺失依赖: {e}")
    raise


@dataclass
class KnowledgeChunk:
    """知识块数据结构"""
    id: str
    text: str
    metadata: Dict[str, Any]
    source: str
    category: str
    difficulty: str
    embedding: List[float] = None


# 常用模型的向量维度映射（未列出的模型默认 1024）
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
    'local/sentence-transformers': 384,  # all-MiniLM-L6-v2
}


class FDEKnowledgeIngester:
    """FDE 知识摄取器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_root = Path(__file__).parent.parent

        # ── 嵌入客户端初始化（优先级：SiliconFlow > MiniMax > OpenAI）────
        sf_key = config.get('SILICONFLOW_API_KEY')
        minimax_key = config.get('MINIMAX_API_KEY')

        if sf_key:
            # SiliconFlow：OpenAI 兼容，直接使用 openai 包
            self._use_minimax_embed = False
            self._embed_client = _OpenAIClient(
                api_key=sf_key,
                base_url=config.get('SILICONFLOW_BASE_URL', 'https://api.siliconflow.cn/v1'),
            )
            self._embedding_model = config.get('SILICONFLOW_EMBEDDING_MODEL', 'BAAI/bge-m3')
        elif minimax_key:
            # MiniMax：嵌入接口格式特殊，使用 httpx 直接调用（见 _embed_text）
            self._use_minimax_embed = True
            self._minimax_api_key = minimax_key
            self._minimax_base_url = config.get('MINIMAX_BASE_URL', 'https://api.minimaxi.chat/v1')
            self._embedding_model = config.get('MINIMAX_EMBEDDING_MODEL', 'embo-01')
            self._embed_client = None  # MiniMax 嵌入不走 openai 包
        else:
            # 回退到本地 sentence-transformers（离线模式）
            self._use_minimax_embed = False
            self._embed_client = None  # 使用本地模型
            self._embedding_model = 'local/sentence-transformers'

        self._vector_dim = _KNOWN_DIMS.get(self._embedding_model, 1024)

        # ── 向量数据库初始化 ──────────────────────────────────────────
        self.qdrant_client = QdrantClient(
            url=config.get('QDRANT_URL', 'http://localhost:6333'),
            api_key=config.get('QDRANT_API_KEY') or None,
        )

        # 知识分类体系
        self.categories = {
            'foundation': {
                'name': '技术基础',
                'subcategories': ['programming', 'system-design', 'database', 'network-security']
            },
            'ai-engineering': {
                'name': 'AI工程化',
                'subcategories': ['ml-basics', 'deep-learning', 'llm-engineering', 'multi-agent']
            },
            'product-business': {
                'name': '产品业务',
                'subcategories': ['product-thinking', 'data-analysis', 'market-positioning']
            },
            'consulting-delivery': {
                'name': '咨询交付',
                'subcategories': ['client-management', 'project-delivery', 'change-management']
            }
        }

    def scan_knowledge_sources(self, category: str = None, difficulty: str = None) -> List[Dict]:
        """扫描知识源"""
        sources = []

        # 扫描不同类型的内容源
        sources.extend(self._scan_books(category, difficulty))
        sources.extend(self._scan_papers(category, difficulty))
        sources.extend(self._scan_obsidian_notes(category, difficulty))
        sources.extend(self._scan_code_examples(category, difficulty))

        return sources

    def _scan_books(self, category: str = None, difficulty: str = None) -> List[Dict]:
        """扫描书籍文件"""
        books_path = self.project_root / "assets" / "books"
        sources = []

        if not books_path.exists():
            return sources

        for book_file in books_path.glob("*.pdf"):
            # 提取元数据
            metadata = self._extract_book_metadata(book_file)

            # 过滤条件
            if category and metadata.get('category') != category:
                continue
            if difficulty and metadata.get('difficulty') != difficulty:
                continue

            sources.append({
                'type': 'book',
                'path': str(book_file),
                'name': book_file.stem,
                'metadata': metadata
            })

        return sources

    def _scan_papers(self, category: str = None, difficulty: str = None) -> List[Dict]:
        """扫描学术论文"""
        papers_path = self.project_root / "assets" / "papers"
        sources = []

        if not papers_path.exists():
            return sources

        for paper_file in papers_path.glob("*.pdf"):
            metadata = self._extract_paper_metadata(paper_file)

            if category and metadata.get('category') != category:
                continue
            if difficulty and metadata.get('difficulty') != difficulty:
                continue

            sources.append({
                'type': 'paper',
                'path': str(paper_file),
                'name': paper_file.stem,
                'metadata': metadata
            })

        return sources

    def _scan_obsidian_notes(self, category: str = None, difficulty: str = None) -> List[Dict]:
        """扫描 Obsidian 笔记"""
        core_path = self.project_root / "core"
        sources = []

        if not core_path.exists():
            return sources

        for note_file in core_path.rglob("*.md"):
            metadata = self._extract_obsidian_metadata(note_file)

            if category and metadata.get('category') != category:
                continue
            if difficulty and metadata.get('difficulty') != difficulty:
                continue

            sources.append({
                'type': 'note',
                'path': str(note_file),
                'name': note_file.stem,
                'metadata': metadata
            })

        return sources

    def _scan_code_examples(self, category: str = None, difficulty: str = None) -> List[Dict]:
        """扫描代码示例"""
        code_path = self.project_root / "assets" / "code-examples"
        sources = []

        if not code_path.exists():
            return sources

        for code_file in code_path.rglob("*.py"):
            metadata = self._extract_code_metadata(code_file)

            if category and metadata.get('category') != category:
                continue
            if difficulty and metadata.get('difficulty') != difficulty:
                continue

            sources.append({
                'type': 'code',
                'path': str(code_file),
                'name': code_file.stem,
                'metadata': metadata
            })

        return sources

    def process_source(self, source: Dict) -> List[KnowledgeChunk]:
        """处理单个知识源"""
        source_type = source['type']
        source_path = source['path']

        if source_type == 'book':
            return self._process_book(source_path, source['metadata'])
        elif source_type == 'paper':
            return self._process_paper(source_path, source['metadata'])
        elif source_type == 'note':
            return self._process_obsidian_note(source_path, source['metadata'])
        elif source_type == 'code':
            return self._process_code_example(source_path, source['metadata'])
        else:
            return []

    def _process_book(self, book_path: str, metadata: Dict) -> List[KnowledgeChunk]:
        """处理书籍文件"""
        print(f"处理书籍: {book_path}")

        # 使用 PyMuPDF 提取文本
        doc = fitz.open(book_path)
        text_parts = []
        for i, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- 第{i+1}页 ---\n{text}")
        doc.close()
        full_text = '\n\n'.join(text_parts)

        # 按段落切分
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(full_text)

        knowledge_chunks = []
        for i, chunk_text in enumerate(chunks):
            chunk_text = self._clean_text(chunk_text)
            if len(chunk_text) < 50:
                continue

            chunk_id = self._generate_chunk_id(book_path, i)

            knowledge_chunk = KnowledgeChunk(
                id=chunk_id,
                text=chunk_text,
                metadata={
                    **metadata,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'processing_date': datetime.now().isoformat()
                },
                source=book_path,
                category=metadata.get('category', 'foundation'),
                difficulty=metadata.get('difficulty', 'intermediate')
            )

            knowledge_chunks.append(knowledge_chunk)

        return knowledge_chunks

    def _process_paper(self, paper_path: str, metadata: Dict) -> List[KnowledgeChunk]:
        """处理学术论文"""
        print(f"处理论文: {paper_path}")

        # 使用 PyMuPDF 提取文本（前8页）
        doc = fitz.open(paper_path)
        text_parts = []
        max_pages = min(8, len(doc))
        for i in range(max_pages):
            text = doc[i].get_text()
            if text.strip():
                text_parts.append(f"--- 第{i+1}页 ---\n{text}")
        doc.close()
        full_text = '\n\n'.join(text_parts)

        # 按段落切分
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(full_text)

        knowledge_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_text = self._clean_text(str(chunk))

            if len(chunk_text) < 50:
                continue

            chunk_id = self._generate_chunk_id(paper_path, i)

            knowledge_chunk = KnowledgeChunk(
                id=chunk_id,
                text=chunk_text,
                metadata={
                    **metadata,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'processing_date': datetime.now().isoformat()
                },
                source=paper_path,
                category=metadata.get('category', 'ai-engineering'),
                difficulty=metadata.get('difficulty', 'expert')
            )

            knowledge_chunks.append(knowledge_chunk)

        return knowledge_chunks

    def _process_obsidian_note(self, note_path: str, metadata: Dict) -> List[KnowledgeChunk]:
        """处理 Obsidian 笔记"""
        print(f"处理笔记: {note_path}")

        with open(note_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 移除 YAML front matter
        content = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)

        # 按段落切分
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        chunks = text_splitter.split_text(content)

        knowledge_chunks = []
        for i, chunk_text in enumerate(chunks):
            if len(chunk_text) < 50:
                continue

            chunk_id = self._generate_chunk_id(note_path, i)

            knowledge_chunk = KnowledgeChunk(
                id=chunk_id,
                text=chunk_text,
                metadata={
                    **metadata,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'note_path': note_path,
                    'processing_date': datetime.now().isoformat()
                },
                source=note_path,
                category=metadata.get('category', 'foundation'),
                difficulty=metadata.get('difficulty', 'intermediate')
            )

            knowledge_chunks.append(knowledge_chunk)

        return knowledge_chunks

    def _process_code_example(self, code_path: str, metadata: Dict) -> List[KnowledgeChunk]:
        """处理代码示例"""
        print(f"处理代码: {code_path}")

        with open(code_path, 'r', encoding='utf-8') as f:
            code_content = f.read()

        # 提取注释和文档字符串
        comments = self._extract_code_comments(code_content)

        # 提取函数和类定义
        functions = self._extract_functions(code_content)

        knowledge_chunks = []

        # 代码注释作为知识块
        if comments:
            chunk_id = self._generate_chunk_id(code_path, 'comments')
            knowledge_chunk = KnowledgeChunk(
                id=chunk_id,
                text=comments,
                metadata={
                    **metadata,
                    'type': 'code_comments',
                    'processing_date': datetime.now().isoformat()
                },
                source=code_path,
                category=metadata.get('category', 'foundation'),
                difficulty=metadata.get('difficulty', 'intermediate')
            )
            knowledge_chunks.append(knowledge_chunk)

        # 每个函数作为单独的知识块
        for i, func in enumerate(functions):
            func_text = f"# 函数: {func['name']}\n{func['docstring']}\n{func['signature']}"

            chunk_id = self._generate_chunk_id(code_path, f'func_{i}')
            knowledge_chunk = KnowledgeChunk(
                id=chunk_id,
                text=func_text,
                metadata={
                    **metadata,
                    'type': 'function',
                    'function_name': func['name'],
                    'processing_date': datetime.now().isoformat()
                },
                source=code_path,
                category=metadata.get('category', 'foundation'),
                difficulty=metadata.get('difficulty', 'intermediate')
            )
            knowledge_chunks.append(knowledge_chunk)

        return knowledge_chunks

    def _embed_text(self, text: str, embed_type: str = "query") -> List[float]:
        """获取文本向量。

        MiniMax embo-01 与 OpenAI text-embedding-3-small 均输出 1536 维向量，
        但 MiniMax 嵌入接口格式不同，需要直接调用 HTTP：
          - 参数：texts（数组）+ type（"query" 检索 / "document" 入库）
          - 响应：vectors（二维数组）
        OpenAI 则走标准 openai 包。
        本地 sentence-transformers 离线模式。
        """
        if self._embed_client is None:
            # 本地 sentence-transformers 离线模式
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(text)
            return embedding.tolist()
        elif self._use_minimax_embed:
            # MiniMax 专用嵌入调用
            resp = httpx.post(
                f'{self._minimax_base_url}/embeddings',
                headers={
                    'Authorization': f'Bearer {self._minimax_api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': self._embedding_model,
                    'texts': [text],
                    'type': embed_type,
                },
                timeout=30,
            )
            data = resp.json()
            base = data.get('base_resp', {})
            if base.get('status_code', 0) != 0:
                raise RuntimeError(f"MiniMax 嵌入失败: {base.get('status_msg')}")
            return data['vectors'][0]
        else:
            # OpenAI 标准调用
            response = self._embed_client.embeddings.create(
                model=self._embedding_model,
                input=text,
            )
            return response.data[0].embedding

    def index_knowledge(self, chunks: List[KnowledgeChunk]):
        """将知识块索引到向量数据库"""
        # 创建集合（向量维度 1536 与 MiniMax embo-01 / OpenAI text-embedding-3-small 均兼容）
        collection_name = "fde_knowledge"

        existing = {c.name for c in self.qdrant_client.get_collections().collections}
        if collection_name not in existing:
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self._vector_dim, distance=Distance.COSINE),
            )
        else:
            # 如果集合维度与当前模型不匹配则重建
            info = self.qdrant_client.get_collection(collection_name)
            existing_dim = info.config.params.vectors.size
            if existing_dim != self._vector_dim:
                print(f"[重建集合] 维度变更 {existing_dim} → {self._vector_dim}")
                self.qdrant_client.delete_collection(collection_name)
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=self._vector_dim, distance=Distance.COSINE),
                )

        # 批量插入
        points = []
        for chunk in chunks:
            if chunk.embedding is None:
                # 知识入库用 "document" 类型，检索查询用 "query" 类型（见 search_knowledge）
                chunk.embedding = self._embed_text(chunk.text, embed_type="document")

            point = PointStruct(
                id=hash(chunk.id) % (2**32),  # 简单的 ID 生成
                vector=chunk.embedding,
                payload={
                    'text': chunk.text,
                    'metadata': chunk.metadata,
                    'source': chunk.source,
                    'category': chunk.category,
                    'difficulty': chunk.difficulty
                }
            )
            points.append(point)

        # 批量上传
        self.qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )

        print(f"成功索引 {len(chunks)} 个知识块")

    def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索相关知识"""
        query_embedding = self._embed_text(query)

        search_results = self.qdrant_client.query_points(
            collection_name="fde_knowledge",
            query=query_embedding,
            limit=top_k,
        ).points

        results = []
        for result in search_results:
            results.append({
                'text': result.payload['text'],
                'score': result.score,
                'metadata': result.payload['metadata'],
                'source': result.payload['source']
            })

        return results

    # 辅助方法
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}"\'-]', '', text)
        return text.strip()

    def _generate_chunk_id(self, source_path: str, chunk_index: Any) -> str:
        """生成知识块 ID"""
        source_hash = hashlib.md5(source_path.encode()).hexdigest()[:8]
        return f"{source_hash}_{chunk_index}"

    def _extract_page_range(self, chunk) -> str:
        """提取页码范围"""
        if hasattr(chunk, 'metadata') and 'page_number' in chunk.metadata:
            return f"Page {chunk.metadata['page_number']}"
        return ""

    def _extract_book_metadata(self, book_file: Path) -> Dict:
        """提取书籍元数据"""
        # 简单实现，实际可以从文件名或内容中提取
        filename = book_file.stem

        # 尝试从文件名解析元数据
        # 格式: "书籍名_作者_年份_分类_难度.pdf"
        parts = filename.split('_')

        metadata = {
            'title': parts[0] if len(parts) > 0 else filename,
            'author': parts[1] if len(parts) > 1 else 'Unknown',
            'year': parts[2] if len(parts) > 2 else 'Unknown',
            'category': parts[3] if len(parts) > 3 else 'foundation',
            'difficulty': parts[4] if len(parts) > 4 else 'intermediate'
        }

        return metadata

    def _extract_paper_metadata(self, paper_file: Path) -> Dict:
        """提取论文元数据"""
        filename = paper_file.stem
        parts = filename.split('_')

        metadata = {
            'title': parts[0] if len(parts) > 0 else filename,
            'authors': parts[1] if len(parts) > 1 else 'Unknown',
            'year': parts[2] if len(parts) > 2 else 'Unknown',
            'venue': parts[3] if len(parts) > 3 else 'Unknown',
            'category': 'ai-engineering',
            'difficulty': 'expert'
        }

        return metadata

    def _extract_obsidian_metadata(self, note_file: Path) -> Dict:
        """提取 Obsidian 笔记元数据"""
        metadata = {
            'title': note_file.stem,
            'path': str(note_file.relative_to(self.project_root)),
            'category': 'foundation',
            'difficulty': 'intermediate'
        }

        # 尝试从 YAML front matter 提取
        try:
            with open(note_file, 'r', encoding='utf-8') as f:
                content = f.read()

            yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if yaml_match:
                import yaml
                yaml_data = yaml.safe_load(yaml_match.group(1))
                if isinstance(yaml_data, dict):
                    metadata.update(yaml_data)
        except:
            pass

        return metadata

    def _extract_code_metadata(self, code_file: Path) -> Dict:
        """提取代码元数据"""
        return {
            'title': code_file.stem,
            'path': str(code_file.relative_to(self.project_root)),
            'category': 'foundation',
            'difficulty': 'intermediate',
            'language': 'python'
        }

    def _extract_code_comments(self, code: str) -> str:
        """提取代码注释"""
        # 简单实现，提取单行注释
        comments = re.findall(r'#.*$', code, re.MULTILINE)
        return '\n'.join(comments)

    def _extract_functions(self, code: str) -> List[Dict]:
        """提取函数定义"""
        functions = []

        # 简单实现，匹配函数定义
        func_pattern = r'def\s+(\w+)\s*\(([^)]*)\)\s*:\s*\n\s*"""([^"]*)"""'
        matches = re.findall(func_pattern, code, re.MULTILINE)

        for name, params, docstring in matches:
            functions.append({
                'name': name,
                'signature': f'def {name}({params}):',
                'docstring': docstring.strip()
            })

        return functions


def main():
    """主函数，用于命令行调用"""
    import argparse

    parser = argparse.ArgumentParser(description='FDE 知识摄取系统')
    parser.add_argument('--source', '-s', help='知识源路径')
    parser.add_argument('--category', '-c', help='知识分类')
    parser.add_argument('--difficulty', '-d', help='难度等级')
    parser.add_argument('--action', '-a', choices=['ingest', 'search'], default='ingest',
                       help='操作类型')

    args = parser.parse_args()

    # 加载配置
    from dotenv import load_dotenv
    load_dotenv()
    config = os.environ

    ingester = FDEKnowledgeIngester(config)

    if args.action == 'ingest':
        # 摄取知识
        if args.source:
            # 处理单个源
            source = {
                'type': 'file',
                'path': args.source,
                'metadata': {
                    'category': args.category or 'foundation',
                    'difficulty': args.difficulty or 'intermediate'
                }
            }
            chunks = ingester.process_source(source)
            ingester.index_knowledge(chunks)
        else:
            # 扫描并处理所有源
            sources = ingester.scan_knowledge_sources(args.category, args.difficulty)
            for source in sources:
                chunks = ingester.process_source(source)
                ingester.index_knowledge(chunks)

    elif args.action == 'search':
        # 搜索知识
        query = input("请输入搜索查询: ")
        results = ingester.search_knowledge(query)

        print(f"\n找到 {len(results)} 个相关结果:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. [分数: {result['score']:.3f}]")
            print(f"   {result['text'][:200]}...")
            print(f"   来源: {result['source']}")


if __name__ == '__main__':
    main()