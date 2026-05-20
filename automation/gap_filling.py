"""
FDE Knowledge Hub - 递归式补洞学习器 v2
目标驱动 → 向量检索 → AI 真实对话 → 掌握归档

使用方法：
    python automation/gap_filling.py
"""

import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime

# Windows UTF-8 fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── 依赖导入 ──────────────────────────────────────────────────────────────────
try:
    from openai import OpenAI as _OpenAIClient
except ImportError:
    print("请先安装依赖: pip install openai")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # 直接读环境变量也可以

# ── 路径常量 ──────────────────────────────────────────────────────────────────
PROJECT_ROOT      = Path(__file__).parent.parent
MASTERED_FILE     = PROJECT_ROOT / "docs" / "mastered_knowledge.json"
CORE_DIR          = PROJECT_ROOT / "core"
COLLECTION_NAME   = "fde_knowledge"

# ── 三个内置问题 ──────────────────────────────────────────────────────────────
PRESET_QUESTIONS = {
    "1": {
        "label": "专家共识思维模式",
        "prompt": "这个领域所有专家都认同的五个思维模式是什么？请结合知识库内容和你的判断给出深度分析。",
        "query_hint": "核心原理 思维模式 专家共识 基础概念",
    },
    "2": {
        "label": "争议热点",
        "prompt": "这个领域专家们争论最激烈的三个方面是什么？分别说明各方观点和你的判断。",
        "query_hint": "争议 挑战 局限性 最新进展 前沿",
    },
    "3": {
        "label": "真理解 vs 死记硬背测试题",
        "prompt": "请出10道题，要求一眼就能看出答题者是真正理解了还是死记硬背——避开定义背诵，聚焦推理、迁移和边界条件。",
        "query_hint": "原理 应用 场景 权衡 设计决策",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# 已掌握知识管理
# ══════════════════════════════════════════════════════════════════════════════

def load_mastered() -> list:
    """加载已掌握知识列表"""
    if MASTERED_FILE.exists():
        try:
            data = json.loads(MASTERED_FILE.read_text(encoding="utf-8"))
            return data.get("mastered", [])
        except Exception:
            return []
    return []


def save_mastered(topic: str, mastered_list: list) -> list:
    """将当前 topic 追加到已掌握列表并持久化"""
    # 去重
    existing_topics = [m["topic"] for m in mastered_list]
    if topic not in existing_topics:
        mastered_list.append({
            "topic": topic,
            "mastered_at": datetime.now().isoformat(),
        })

    MASTERED_FILE.parent.mkdir(parents=True, exist_ok=True)
    MASTERED_FILE.write_text(
        json.dumps({"mastered": mastered_list}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return mastered_list


# ══════════════════════════════════════════════════════════════════════════════
# 知识检索（Qdrant 优先，自动降级到本地 MD 文件）
# ══════════════════════════════════════════════════════════════════════════════

def _get_embedding(text: str) -> list | None:
    """用 SiliconFlow 或 MiniMax 获取向量；失败返回 None"""
    sf_key  = os.environ.get("SILICONFLOW_API_KEY", "")
    mm_key  = os.environ.get("MINIMAX_API_KEY", "")

    if sf_key:
        try:
            client = _OpenAIClient(
                api_key=sf_key,
                base_url=os.environ.get("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
            )
            model = os.environ.get("SILICONFLOW_EMBEDDING_MODEL", "BAAI/bge-m3")
            resp = client.embeddings.create(model=model, input=text)
            return resp.data[0].embedding
        except Exception as e:
            print(f"[向量] SiliconFlow 嵌入失败: {e}")

    if mm_key:
        try:
            import httpx
            resp = httpx.post(
                f"{os.environ.get('MINIMAX_BASE_URL', 'https://api.minimaxi.chat/v1')}/embeddings",
                headers={"Authorization": f"Bearer {mm_key}", "Content-Type": "application/json"},
                json={"model": "embo-01", "texts": [text], "type": "query"},
                timeout=30,
            )
            data = resp.json()
            if data.get("base_resp", {}).get("status_code", -1) == 0:
                return data["vectors"][0]
        except Exception as e:
            print(f"[向量] MiniMax 嵌入失败: {e}")

    return None


def _search_qdrant(query: str, top_k: int = 6) -> list[dict]:
    """向量检索，返回 [{text, source, score}]"""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(
            url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            timeout=5,
        )
        # 确认集合存在
        collections = {c.name for c in client.get_collections().collections}
        if COLLECTION_NAME not in collections:
            return []

        vec = _get_embedding(query)
        if vec is None:
            return []

        hits = client.query_points(
            collection_name=COLLECTION_NAME,
            query=vec,
            limit=top_k,
        ).points

        return [
            {
                "text":   h.payload.get("text", ""),
                "source": h.payload.get("source", ""),
                "score":  round(h.score, 3),
            }
            for h in hits
        ]
    except Exception:
        return []


def _search_local_md(topic: str, top_k: int = 6) -> list[dict]:
    """降级方案：关键词匹配本地 core/ 目录的 MD 文件"""
    keywords = [w for w in re.split(r"[\s，,、/]", topic) if len(w) > 1]
    results = []

    for md_file in CORE_DIR.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            # 去掉 YAML front matter
            content = re.sub(r"^---.*?---\s*", "", content, flags=re.DOTALL)
            # 简单评分：命中关键词数
            score = sum(1 for kw in keywords if kw in content)
            if score > 0:
                # 取前 800 字符作为摘要
                snippet = content[:800].strip()
                results.append({
                    "text":   snippet,
                    "source": str(md_file.relative_to(PROJECT_ROOT)),
                    "score":  score,
                })
        except Exception:
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def retrieve_context(topic: str, query_hint: str, mastered_topics: list[str]) -> tuple[str, bool]:
    """
    检索上下文，返回 (context_text, used_vector_db)
    已掌握的 topic 对应的片段会被过滤掉。
    """
    query = f"{topic} {query_hint}"

    # 先试 Qdrant
    chunks = _search_qdrant(query, top_k=8)
    used_vector = bool(chunks)

    # 降级到本地 MD
    if not chunks:
        chunks = _search_local_md(topic, top_k=8)

    # 过滤已掌握 topic 的相关片段（简单关键词匹配）
    def _is_mastered_chunk(chunk: dict) -> bool:
        for mt in mastered_topics:
            mt_words = [w for w in re.split(r"[\s，,、/]", mt) if len(w) > 1]
            # 片段里命中超过半数关键词则认为属于已掌握范畴
            if mt_words and sum(1 for w in mt_words if w in chunk["text"]) >= max(1, len(mt_words) // 2):
                return True
        return False

    filtered = [c for c in chunks if not _is_mastered_chunk(c)]

    if not filtered:
        # 过滤后为空则保留全部（不能让上下文完全空）
        filtered = chunks

    # 组装上下文文本
    parts = []
    for i, c in enumerate(filtered, 1):
        src = Path(c["source"]).name if c["source"] else "未知来源"
        parts.append(f"【片段 {i}】来源: {src}\n{c['text']}")

    context_text = "\n\n".join(parts) if parts else "（未找到相关知识片段）"
    return context_text, used_vector


# ══════════════════════════════════════════════════════════════════════════════
# AI 客户端
# ══════════════════════════════════════════════════════════════════════════════

def build_ai_client():
    """优先 MiniMax，回退 OpenAI"""
    mm_key = os.environ.get("MINIMAX_API_KEY", "")
    if mm_key:
        return (
            _OpenAIClient(
                api_key=mm_key,
                base_url=os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.chat/v1"),
            ),
            os.environ.get("MINIMAX_CHAT_MODEL", "MiniMax-Text-01"),
        )

    oa_key = os.environ.get("OPENAI_API_KEY", "")
    if oa_key:
        return _OpenAIClient(api_key=oa_key), "gpt-4o-mini"

    print("错误：未配置 MINIMAX_API_KEY 或 OPENAI_API_KEY，请检查 .env 文件。")
    sys.exit(1)


def chat(client, model: str, messages: list) -> str:
    """流式发送消息，逐字打印 AI 回复，自动跳过 <think> 思考链，返回完整文本"""
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=8192,
        stream=True,
    )

    collected = []
    buf       = ""      # 待处理缓冲区
    in_think  = False   # 当前是否在 <think> 块内
    shown_thinking = False  # 是否已显示"思考中"提示

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue
        collected.append(delta)
        buf += delta

        # ── 进入 <think> 块 ───────────────────────────────────────────────
        if not in_think and "<think>" in buf:
            before, _, buf = buf.partition("<think>")
            if before:
                print(before, end="", flush=True)
            in_think = True
            if not shown_thinking:
                print("（思考中...）", end="", flush=True)
                shown_thinking = True

        # ── 离开 <think> 块 ───────────────────────────────────────────────
        if in_think and "</think>" in buf:
            _, _, buf = buf.partition("</think>")
            in_think = False
            if shown_thinking:
                # 用空格覆盖"（思考中...）"提示
                print("\r" + " " * 20 + "\r", end="", flush=True)

        # ── 不在 think 块内则打印 ─────────────────────────────────────────
        if not in_think and buf:
            print(buf, end="", flush=True)
            buf = ""

    # 打印缓冲区剩余内容（正常情况下为空）
    if buf and not in_think:
        print(buf, end="", flush=True)

    print()  # 换行

    full_text = "".join(collected)
    full_text = re.sub(r"<think>.*?</think>", "", full_text, flags=re.DOTALL).strip()
    return full_text


# ══════════════════════════════════════════════════════════════════════════════
# 构建系统提示词
# ══════════════════════════════════════════════════════════════════════════════

def build_system_prompt(topic: str, context: str, mastered: list) -> str:
    mastered_section = ""
    if mastered:
        items = "\n".join(f"  - {m['topic']} (掌握于 {m['mastered_at'][:10]})" for m in mastered)
        mastered_section = f"""
## 用户已掌握的知识（无需重复讲解）
{items}
"""

    return f"""你是一位 FDE（Forward Deployed Engineer）领域的专家导师，正在帮助用户深度学习「{topic}」。

## 知识库相关内容（来自用户本地知识库，请结合这些内容作答）

{context}
{mastered_section}
## 行为准则
- 结合知识库内容和你自己的专业判断综合作答，不要只复述片段
- 对于已掌握的知识点，可以简略提及但无需详细展开
- 保持对话连贯，记住本次会话的上下文
- 回答要有深度，避免泛泛而谈
- 如果用户输入「我已经完全理解」，请对本次学习做一个简短总结，然后告知用户记录已保存
"""


# ══════════════════════════════════════════════════════════════════════════════
# 主题选择（从知识库扫描 + 已掌握展示）
# ══════════════════════════════════════════════════════════════════════════════

BATCH_SIZE = 6  # 每批展示的主题数量


def _scan_kb_topics() -> list[str]:
    """
    扫描 core/ 目录下所有 MD 文件，提取文件名作为主题候选。
    按文件修改时间倒序（最近编辑的排前面）。
    """
    if not CORE_DIR.exists():
        return []

    files = sorted(
        CORE_DIR.rglob("*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    # 用文件 stem 作为主题名，去掉模板类文件
    skip_prefixes = ("template_", "复习_", "学习路径")
    topics = []
    seen = set()
    for f in files:
        name = f.stem
        if any(name.startswith(p) for p in skip_prefixes):
            continue
        if name not in seen:
            seen.add(name)
            topics.append(name)
    return topics


def select_topic(mastered_list: list) -> str:
    """
    交互式主题选择：
    - 展示知识库主题（分批，支持换一批）
    - 展示已掌握主题（仍可选择复习）
    - 支持自定义输入
    返回用户最终选定的主题字符串。
    """
    all_topics  = _scan_kb_topics()
    mastered_topics = [m["topic"] for m in mastered_list]

    # 将已掌握主题从主列表里移到底部展示区（不重复）
    unmastered = [t for t in all_topics if t not in mastered_topics]

    batch_offset = 0  # 当前批次起始下标

    while True:
        print()
        print("─" * 60)
        print("📌 第一步：选择学习主题")
        print("─" * 60)

        # ── 知识库主题（当前批次）────────────────────────────────────────────
        batch = unmastered[batch_offset: batch_offset + BATCH_SIZE]

        if batch:
            print()
            print("📚 知识库主题：")
            for i, t in enumerate(batch, 1):
                print(f"  [{i}] {t}")
        else:
            print()
            print("  （知识库暂无可用主题，请自定义输入）")

        # ── 已掌握主题 ────────────────────────────────────────────────────────
        if mastered_topics:
            print()
            print("✅ 已掌握（仍可选择复习）：")
            letters = "abcdefghij"
            for idx, t in enumerate(mastered_topics):
                label = letters[idx] if idx < len(letters) else str(idx)
                date  = mastered_list[idx]["mastered_at"][:10]
                print(f"  [{label}] {t}  （掌握于 {date}）")

        # ── 操作提示 ──────────────────────────────────────────────────────────
        print()
        options = []
        if batch:
            options.append("1-6 选主题")
        if mastered_topics:
            options.append("a-j 选已掌握")
        total_unmastered = len(unmastered)
        if total_unmastered > BATCH_SIZE:
            options.append("r 换一批")
        options.append("0 自定义输入")
        print(f"  操作：{' | '.join(options)}")
        print()

        raw = input("> 请选择: ").strip()

        # 数字 → 选当前批次主题
        if raw.isdigit() and 1 <= int(raw) <= len(batch):
            return batch[int(raw) - 1]

        # 字母 a-j → 选已掌握主题
        letters_map = {chr(ord('a') + i): t for i, t in enumerate(mastered_topics)}
        if raw.lower() in letters_map:
            chosen = letters_map[raw.lower()]
            print(f"\n  ℹ️  将对已掌握主题「{chosen}」进行复习")
            return chosen

        # r → 换一批
        if raw.lower() == "r" and total_unmastered > BATCH_SIZE:
            batch_offset = (batch_offset + BATCH_SIZE) % max(total_unmastered, 1)
            # 确保不越界
            if batch_offset >= total_unmastered:
                batch_offset = 0
            continue

        # 0 → 自定义
        if raw == "0":
            custom = input("> 自定义主题: ").strip()
            if custom:
                return custom
            print("  主题不能为空，请重新选择。")
            continue

        # 直接回车或无效输入 → 提示重试
        print("  无效输入，请重新选择。")


# ══════════════════════════════════════════════════════════════════════════════
# 主程序
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  递归式补洞学习器 v2  —  真实 AI 对话版")
    print("=" * 60)
    print("提示：输入「我已经完全理解」保存掌握记录并退出")

    # ── 1. 加载已掌握 + 主题选择 ─────────────────────────────────────────────
    mastered_list   = load_mastered()
    topic           = select_topic(mastered_list)
    mastered_topics = [m["topic"] for m in mastered_list]
    print(f"\n✅ 已选主题：{topic}")

    # ── 2. 选择切入角度 ───────────────────────────────────────────────────────
    print()
    print("📌 第二步：选择你想从哪个角度切入")
    print()
    for key, q in PRESET_QUESTIONS.items():
        print(f"  [{key}] {q['label']}")
        print(f"       → {q['prompt'][:50]}…")
    print(f"  [0] 自定义角度")
    print()

    while True:
        choice = input("> 请输入编号 (1/2/3/0): ").strip()
        if choice in PRESET_QUESTIONS:
            selected = PRESET_QUESTIONS[choice]
            break
        if choice == "0":
            custom_prompt = input("> 输入你的问题或角度: ").strip()
            if not custom_prompt:
                print("   内容不能为空，请重新输入。")
                continue
            selected = {
                "label":      "自定义角度",
                "prompt":     custom_prompt,
                "query_hint": topic,   # 直接用主题名做检索词
            }
            break
        print("   请输入 0、1、2 或 3")

    print(f"\n✅ 已选择：{selected['label']}")

    # ── 3. 检索上下文 ────────────────────────────────────────────────────────
    print()
    print("🔍 正在检索知识库…")
    context, used_vector = retrieve_context(topic, selected["query_hint"], mastered_topics)

    if used_vector:
        print("   ✅ 已从向量数据库检索到相关知识片段")
    else:
        print("   ⚠️  向量库未就绪，已降级使用本地 Markdown 文件检索")

    if mastered_topics:
        print(f"   📚 已屏蔽已掌握主题：{', '.join(mastered_topics)}")

    # ── 4. 初始化 AI 客户端和会话 ─────────────────────────────────────────────
    client, model = build_ai_client()

    system_prompt = build_system_prompt(topic, context, mastered_list)
    first_user_msg = f"关于「{topic}」，{selected['prompt']}"

    messages = [
        {"role": "system",    "content": system_prompt},
        {"role": "user",      "content": first_user_msg},
    ]

    # ── 5. 第一次 AI 回复 ─────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"🤖 AI 正在回答：{selected['label']}")
    print("=" * 60)
    print()

    try:
        reply = chat(client, model, messages)
    except Exception as e:
        print(f"AI 调用失败: {e}")
        sys.exit(1)

    messages.append({"role": "assistant", "content": reply})

    # ── 6. 多轮对话循环 ───────────────────────────────────────────────────────
    while True:
        print()
        print("─" * 60)
        print("  直接输入追问继续对话，或选择：")
        print("  [m] 我已经完全理解    [n] 开始新会话    [q] 退出")
        print("─" * 60)
        print()

        user_input = input("你: ").strip()

        if not user_input:
            continue

        # ── 退出 ──────────────────────────────────────────────────────────
        if user_input.lower() == "q" or user_input == "退出":
            print()
            print("👋 已退出，下次继续加油！")
            break

        # ── 新会话 ────────────────────────────────────────────────────────
        if user_input.lower() == "n" or user_input == "新会话":
            print()
            print("🔄 开始新会话…")
            main()   # 递归调用，相当于重新走完整流程
            return   # 新会话结束后退出当前层

        # ── 完全理解 ──────────────────────────────────────────────────────
        if user_input.lower() == "m" or "我已经完全理解" in user_input:
            messages.append({"role": "user", "content": "我已经完全理解了，请做一个简短的总结。"})
            print()
            print("🤖 AI: ", end="", flush=True)
            try:
                chat(client, model, messages)
            except Exception:
                pass

            mastered_list = save_mastered(topic, mastered_list)
            print()
            print("=" * 60)
            print(f"✅ 已将「{topic}」记录到已掌握知识")
            print(f"   文件位置: docs/mastered_knowledge.json")
            print("=" * 60)
            print()
            print("  [n] 开始新会话    [q] 退出")
            print()
            nxt = input("> ").strip().lower()
            if nxt == "n":
                print()
                main()
                return
            break

        # ── 普通追问 ──────────────────────────────────────────────────────
        messages.append({"role": "user", "content": user_input})

        print()
        print("🤖 AI: ", end="", flush=True)
        try:
            reply = chat(client, model, messages)
        except Exception as e:
            print(f"\nAI 调用失败: {e}，请重试")
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
