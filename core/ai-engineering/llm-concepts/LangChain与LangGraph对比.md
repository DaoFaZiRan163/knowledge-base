---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["LangChain", "LangGraph", "工作流编排", "LLM应用框架"]
source: 原创
created_date: 2026-05-19
updated_date: 2026-05-19
implementation_status: production_ready
use_cases: ["LLM应用开发", "Agent编排", "RAG实现", "工作流自动化"]
related_concepts: ["DSPy", "ReAct", "Agent", "RAG"]
prerequisites: ["LLM基础原理"]
---

# LangChain vs LangGraph — 对比分析

## 核心定义

| 框架 | 定义 | 定位 |
|------|------|------|
| **LangChain** | 构建 LLM 应用的 Python/JS 框架 | 应用开发框架 |
| **LangGraph** | 基于 LangChain 的图结构编排引擎 | 工作流编排工具 |

**核心理念**：
- LangChain 提供**组件库**（Chains、Agents、Memory）
- LangGraph 将应用建模为**有状态的有向图**，支持循环和条件分支

## 🎯 一句话总结

> **LangChain = 组件库，LangGraph = 带循环的状态机**

```
LangChain:  组件A → 组件B → 组件C (线性链式)
LangGraph:  ┌──────────────────────┐
            │                      │
            ▼                      │
         组件A ─→ 组件B ─→ 组件C ──┘
                    (可循环)
```

## 🏗️ 架构对比

### LangChain 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      LangChain                             │
│                                                             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │ Chains  │   │ Agents  │   │ Memory  │   │ Tools   │      │
│  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘      │
│       └────────────┼──────────────┼──────────────┘          │
│                    ▼                                      │
│              ┌─────────┐                                 │
│              │  LLM    │                                 │
│              └─────────┘                                 │
└─────────────────────────────────────────────────────────────┘
```

### LangGraph 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      LangGraph                             │
│                                                             │
│        ┌─────┐                                             │
│        │Start│                                             │
│        └──┬──┘                                             │
│           │                                                │
│           ▼                                                │
│     ┌───────────┐                                          │
│     │   Node A  │                                          │
│     └─────┬─────┘                                          │
│           │                                                │
│      ┌────┴────┐                                          │
│      ▼         ▼                                          │
│  ┌─────────┐ ┌─────────┐                                   │
│  │ Node B  │ │ Node C  │ ← 条件分支                        │
│  └────┬────┘ └────┬────┘                                   │
│       │         │                                          │
│       └────┬────┘                                          │
│            ▼                                               │
│      ┌───────────┐                                          │
│      │  Router   │                                          │
│      └─────┬─────┘                                          │
│            │                                                │
│       ┌────┴────┐                                           │
│       ▼         ▼                                          │
│   ┌─────────┐ ┌─────────┐                                  │
│   │ Node D  │ │  END    │                                  │
│   └─────────┘ └─────────┘                                  │
│                                                             │
│  支持: 循环、条件分支、状态持久化                            │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 技术实现

### LangChain 示例

```python
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# 简单链式调用
llm = ChatOpenAI(model="gpt-4")
prompt = PromptTemplate.from_template("请用一句话总结: {topic}")
chain = LLMChain(llm=llm, prompt=prompt)

result = chain.invoke({"topic": "人工智能"})
```

### LangGraph 示例

```python
from langgraph.graph import StateGraph, END

# 定义状态
class AgentState(TypedDict):
    messages: list
    current_step: str

# 创建图
graph = StateGraph(AgentState)

# 添加节点
graph.add_node("analyze", analyze_step)
graph.add_node("execute", execute_step)
graph.add_node("reflect", reflect_step)

# 设置边
graph.set_entry_point("analyze")
graph.add_edge("analyze", "execute")
graph.add_edge("execute", "reflect")

# 条件边：反思结果决定是否重试
graph.add_conditional_edges(
    "reflect",
    should_continue,
    {"continue": "execute", "end": END}
)

# 编译运行
app = graph.compile()
result = app.invoke({"messages": [...]})
```

### 对比总结

| 维度 | LangChain | LangGraph |
|------|-----------|-----------|
| **编程模型** | 链式 (Chain) | 图结构 (Graph) |
| **状态管理** | 外部 Memory | 内置状态传递 |
| **循环支持** | 需额外处理 | 原生支持 |
| **条件分支** | 简单判断 | 条件边/路由 |
| **适用场景** | 简单 Pipeline | 复杂 Agent 工作流 |
| **学习曲线** | 较平缓 | 较陡 |

## 💼 FDE 应用场景

### LangChain 适用场景
- 快速原型开发
- 简单 RAG 流水线
- 单链/多链调用
- 文档处理流水线

### LangGraph 适用场景
- Multi-Agent 编排（循环交互）
- 需要状态持久化的对话
- 复杂业务流程（订单处理、风控）
- 需要回退/重试机制的场景

## 🔗 相关知识

- [[DSPy]] - 另一种 LLM 编程范式
- [[ReAct]] - 推理与动作结合
- [[Agent]] - Agent 架构设计

---

**向量检索标签**: LangChain, LangGraph, 工作流编排, LLM框架对比, Agent编排