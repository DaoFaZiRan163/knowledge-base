---
type: book
category: ["RAG", "LLM应用", "AI工程化"]
difficulty: intermediate
tags: ["LangChain", "RAG", "Agent", "向量数据库", "Chain", "工具调用"]
reading_status: completed
completion_date: 2026-05-18
prerequisites: ["Python", "LLM基础概念", "向量数据库基础"]
related_books: ["《AI Engineering》-Chip Huyen", "《大语言模型-CS224N》"]
related_concepts: ["RAG", "Vector Store", "Tool Use", "Memory", "Agent"]
---

# LangChain 实战——LLM 应用开发框架

## 📖 基本信息
- **来源**: LangChain 官方文档 + 社区最佳实践（非单一书籍，为框架知识笔记）
- **创建者**: Harrison Chase（2022 年创建，现 LangChain Inc.）
- **核心主题**: 用 LangChain 构建 RAG 系统、Agent 和 LLM 工作流的实践指南
- **目标读者**: 需要快速构建 LLM 应用的 AI 工程师
- **阅读难度**: intermediate

## 🎯 核心价值
> LangChain 是 LLM 应用的"乐高积木"——提供标准化的组件接口，让你专注于业务逻辑而非底层胶水代码；但过度依赖它会让调试变成噩梦，需要知道何时用、何时不用。

## 📚 知识框架

### LangChain 核心组件

### 1. Model I/O（模型输入输出）

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 模型初始化
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Prompt 模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的 {role}"),
    ("user", "{question}")
])

# LCEL（LangChain Expression Language）链
chain = prompt | llm

result = chain.invoke({
    "role": "数据分析师",
    "question": "如何计算用户留存率？"
})
```

---

### 2. RAG（检索增强生成）完整流程

#### 文档加载与切分
```python
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 加载 PDF
loader = PyPDFLoader("document.pdf")
docs = loader.load()

# 递归字符切分（推荐用于大多数场景）
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,      # 重叠避免上下文断裂
    separators=["\n\n", "\n", "。", " ", ""]
)
chunks = splitter.split_documents(docs)
```

#### 向量化与存储
```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 向量化并存储
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
```

#### 检索链
```python
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

retriever = vectorstore.as_retriever(
    search_type="mmr",      # Maximum Marginal Relevance，增加多样性
    search_kwargs={"k": 5, "fetch_k": 20}
)

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

answer = rag_chain.invoke("什么是 DDIA 中的 CAP 定理？")
```

---

### 3. Memory（对话历史管理）

```python
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain

# 滑动窗口记忆（只保留最近 k 轮）
memory = ConversationBufferWindowMemory(k=5)

# 或 摘要记忆（LLM 压缩历史）
from langchain.memory import ConversationSummaryMemory
summary_memory = ConversationSummaryMemory(llm=llm)
```

---

### 4. Tools 与 Agent

#### 工具定义
```python
from langchain_core.tools import tool

@tool
def search_knowledge_base(query: str) -> str:
    """搜索知识库，返回相关文档内容"""
    results = vectorstore.similarity_search(query, k=3)
    return "\n".join([doc.page_content for doc in results])

@tool
def execute_sql(query: str) -> str:
    """执行 SQL 查询并返回结果（只允许 SELECT）"""
    if not query.strip().upper().startswith("SELECT"):
        return "只允许 SELECT 查询"
    # 执行查询...
```

#### ReAct Agent
```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub

prompt = hub.pull("hwchase17/react")  # 标准 ReAct Prompt

agent = create_react_agent(llm, tools=[search_knowledge_base, execute_sql], prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10)

result = agent_executor.invoke({"input": "查询本季度销售额并与去年同期对比"})
```

---

### 5. LCEL（LangChain 表达式语言）

```python
# LCEL 用 | 管道符组合组件
chain = prompt | llm | output_parser

# 并行执行
from langchain_core.runnables import RunnableParallel

parallel_chain = RunnableParallel(
    summary=summary_chain,
    keywords=keywords_chain
)

# 分支路由
from langchain_core.runnables import RunnableBranch

branch = RunnableBranch(
    (lambda x: "技术" in x["topic"], tech_chain),
    (lambda x: "业务" in x["topic"], business_chain),
    default_chain    # fallback
)
```

---

### 6. RAG 优化策略

#### 检索优化
| 策略 | 原理 | 场景 |
|------|------|------|
| **混合检索** | 向量 + BM25 关键词 | 通用场景，平衡语义和精确匹配 |
| **MMR** | 最大边际相关，减少重复 | 结果多样性要求高 |
| **Parent Document** | 检索小块，返回大块 | 保持上下文完整性 |
| **Self-Querying** | LLM 将问题转为结构化查询 | 有元数据过滤需求 |
| **HyDE** | 先生成假设答案再检索 | 问题与文档表达差异大 |

#### Reranker（重排序）
```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain_cohere import CohereRerank

compressor = CohereRerank(top_n=3)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever
)
```

---

### 7. LangSmith（可观测性）

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"

# 所有链的调用自动追踪到 LangSmith
# 可以看到：每步输入输出、Token 消耗、延迟、错误
```

---

## 🔑 关键概念

### Runnable 接口
**定义**: LangChain 所有组件实现的统一接口：`invoke / stream / batch / ainvoke`

**重要性**: LCEL 管道的基础；统一接口允许任意组件组合

**应用场景**:
1. 流式输出：`chain.stream(input)` 逐 token 返回
2. 批量处理：`chain.batch([input1, input2])` 并发执行
3. 异步：`await chain.ainvoke(input)` 用于 FastAPI

---

### LangChain 的局限性
**定义**: 框架抽象层带来的调试困难和版本不稳定

**重要性**: 决定何时用 LangChain，何时直接调用 SDK

**应用场景**:
1. 原型和演示 → LangChain 快速搭建
2. 生产系统 → 考虑直接用 Anthropic/OpenAI SDK + 自定义管道
3. 复杂 Agent → LangGraph（更可控的图执行引擎）

---

## 💡 实战应用场景

### 场景 1: 企业知识库 QA 系统（72 小时版本）
**背景**: FDE 需要快速为客户搭建内部文档问答系统

**解决方案**: LangChain RAG 标准流程

**实施步骤**:
1. 文档加载：支持 PDF/Word/网页
2. 分块：RecursiveCharacterTextSplitter，chunk_size=800
3. 向量化：text-embedding-3-small（性价比高）
4. 存储：Chroma（本地）或 Qdrant（生产）
5. 检索：混合检索 + Reranker
6. 生成：GPT-4o + 来源引用 Prompt

**预期效果**: 2 天内可以交付可演示版本

---

### 场景 2: 多工具 Agent 系统
**背景**: 客户需要 AI 助手能查数据库、调 API、生成报表

**解决方案**: LangGraph + 工具调用

**实施步骤**:
1. 用 `@tool` 装饰器定义工具（注意写好 docstring，LLM 靠它决定调用）
2. 用 LangGraph 构建有状态的 Agent 图
3. 添加人工确认节点（高风险操作前暂停）
4. 用 LangSmith 监控每次调用的工具链

**预期效果**: 可审计、可调试、可扩展的 Agent 系统

---

## 🔗 相关技术栈
- **向量数据库**: Chroma（本地）, Qdrant（生产）, Pinecone（云）
- **嵌入模型**: text-embedding-3-small/large（OpenAI）, bge-m3（本地）
- **Agent 框架**: LangGraph（推荐）, AutoGen, CrewAI
- **可观测**: LangSmith, Arize AI, Helicone

---

## 📝 个人笔记

### 重要洞察
- LangChain 的最大价值在原型阶段；生产阶段往往需要自己控制每一步
- chunk_size 和 chunk_overlap 是 RAG 质量最敏感的参数，需要针对具体文档实验
- FDE 场景：LangChain 的 Demo 速度极快，非常适合客户现场 POC

### 待深入研究
- [ ] 深入 LangGraph 的状态机设计，用于复杂多步 Agent
- [ ] 研究 RAG Fusion（多查询 + RRF 重排）
- [ ] 了解 LangChain 与 LlamaIndex 的适用场景差异

### 实践项目
- [ ] 用 LangChain 为本项目的知识库构建一个 QA 接口
- [ ] 实现一个带 Memory 的多轮对话 RAG 系统

---

## 🎓 学习检验

### 自测问题
1. RecursiveCharacterTextSplitter 的 chunk_overlap 有什么作用？
2. MMR 检索策略相比纯相似度检索有什么优势？
3. LCEL 管道中 `|` 操作符的底层是什么接口？
4. LangSmith 追踪的数据对 RAG 优化有什么帮助？
5. 什么情况下应该选 LangGraph 而不是 LangChain Agent？

### 实践任务
- [ ] 用 LangChain 实现一个支持 PDF 问答的 RAG 系统
- [ ] 添加 Reranker，对比有无 Reranker 的检索质量

---

## 📊 知识关联

### 前置知识
- [[RAG架构原理]]
- [[大语言模型-CS224N]]

### 后续学习
- [[LangGraph工作流编排]]
- [[72小时RAG-Demo实战清单]]

### 并行学习
- [[AI Engineering-Chip-Huyen]]
- [[Hermes-Agent工作系统]]

---

## 🏷️ 标签系统
#书籍 #技术 #RAG #LangChain #intermediate

---
**阅读开始**: 2026-05-18
**阅读完成**: 2026-05-18
**下次复习**: 2026-06-18
**总计用时**: 知识提炼版（直接生成）
**推荐指数**: ⭐⭐⭐⭐☆
