---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["ReAct", "HyDE", "推理", "检索增强", "Agent"]
source: 原创
created_date: 2026-05-19
updated_date: 2026-05-19
implementation_status: production_ready
use_cases: ["复杂推理", "RAG优化", "问答系统", "Tool-Use"]
related_concepts: ["CoT", "Agent", "RAG", "DSPy"]
prerequisites: ["CoT", "RAG架构原理"]
---

# ReAct 与 HyDE — 推理增强方法

## 核心定义

**ReAct (Reasoning + Acting)**：结合推理（思考下一步）和行动（执行操作）的 Agent 循环范式，让模型在推理过程中调用外部工具。

**HyDE (Hypothetical Document Embeddings)**：通过生成假设性答案来改进检索的方法，假设答案与真实答案语义相似，便于检索相关文档。

**核心理念**：
- ReAct = 让模型"边想边做"，推理与行动交替
- HyDE = 用"猜答案"来引导检索

## 🎯 一句话总结

> **ReAct = 思考 → 行动 → 观察 → 再思考；HyDE = 猜答案 → 检索 → 验证**

```
ReAct 循环:
Thought: 我需要查找相关信息
Action: search[query]
Observation: 获取到结果
Thought: 根据结果，我可以回答了
Action: finish[answer]

HyDE:
Query → 生成假设答案 → 向量检索 → 真实答案
```

## 🏗️ ReAct 原理

### ReAct 循环

```
┌─────────────────────────────────────────────────────────────┐
│                    ReAct Loop                               │
│                                                             │
│    ┌──────────┐                                            │
│    │   OBS    │ ← 外部环境反馈                              │
│    └────┬─────┘                                            │
│         │                                                  │
│         ▼                                                  │
│    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│    │ Thought  │ → │  Action  │ → │  Result  │             │
│    │ 推理下一步 │   │ 执行操作  │   │ 操作结果  │             │
│    └──────────┘    └──────────┘    └────┬─────┘             │
│                                          │                  │
│         ┌─────────────────────────────────┘                  │
│         │                                                  │
│         └────────────────────────────────────→ 循环直到完成 │
└─────────────────────────────────────────────────────────────┘
```

### ReAct 与 CoT 对比

| 维度 | CoT | ReAct |
|------|-----|-------|
| 核心能力 | 推理 | 推理 + 行动 |
| 工具使用 | 无 | 搜索、计算、API调用 |
| 适用场景 | 纯推理任务 | 需要外部交互的任务 |
| 输出格式 | 推理步骤 + 答案 | Thought + Action + Observation + 答案 |

## 🏗️ HyDE 原理

### HyDE 流程

```
┌─────────────────────────────────────────────────────────────┐
│                    HyDE Process                             │
│                                                             │
│   Query: "为什么天空是蓝色的？"                              │
│                                                             │
│        ↓                                                    │
│   ┌─────────────────┐                                        │
│   │ 生成假设答案    │                                        │
│   │ (可能不完全准确) │                                        │
│   │ "因为瑞利散射..." │                                       │
│   └────────┬────────┘                                        │
│            ↓                                                 │
│   ┌─────────────────┐                                        │
│   │ 用假设答案检索   │ ← 语义相似                             │
│   │ 向量数据库       │                                        │
│   └────────┬────────┘                                        │
│            ↓                                                 │
│   ┌─────────────────┐                                        │
│   │ 获取真实文档    │                                        │
│   │ 科学解释文章    │                                        │
│   └────────┬────────┘                                        │
│            ↓                                                 │
│        最终答案                                              │
└─────────────────────────────────────────────────────────────┘
```

### 为什么 HyDE 有效

- 假设答案包含完整的语义信息
- 假设答案与真实答案在向量空间中接近
- 可以捕获查询的深层意图

## 🔧 技术实现

### ReAct 实现

```python
import json

class ReActAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

    def run(self, query, max_iterations=5):
        steps = []
        observation = ""

        for _ in range(max_iterations):
            # 1. 生成 Thought
            thought_prompt = f"""
基于以下信息，推理下一步行动：

问题: {query}
历史步骤: {steps}
当前观察: {observation}

可用工具: {list(self.tools.keys())}

请输出 JSON 格式的推理:
{{
    "thought": "你的推理过程",
    "action": "工具名称[参数]",
    "finish": true/false
}}
"""
            response = self.llm.generate(thought_prompt)
            decision = json.loads(response)

            # 2. 执行或结束
            if decision.get("finish"):
                return {"answer": decision.get("answer"), "steps": steps}

            action = decision.get("action")
            result = self._execute_action(action)
            observation = result
            steps.append({
                "thought": decision.get("thought"),
                "action": action,
                "observation": result
            })

        return {"answer": observation, "steps": steps}

    def _execute_action(self, action):
        # 解析动作并执行
        tool_name, args = parse_action(action)
        return self.tools[tool_name](**args)
```

### HyDE 实现

```python
class HyDERetriever:
    def __init__(self, vector_db, llm):
        self.vector_db = vector_db
        self.llm = llm

    def retrieve(self, query, k=5):
        # 1. 生成假设答案
        hypothetical = self.llm.generate(f"""
请生成一个可能回答以下问题的假设答案：

问题: {query}

假设答案:""")

        # 2. 用假设答案检索
        query_embedding = embed(query)
        hyp_embedding = embed(hypothetical)

        # 3. 融合查询和假设答案的向量
        combined_embedding = (query_embedding + hyp_embedding) / 2

        # 4. 向量检索
        results = self.vector_db.search(combined_embedding, k=k)

        return results
```

### DSPy ReAct

```python
import dspy

# DSPy 内置 ReAct Module
react = dspy.ReAct(
    Signature.from_components(
        question="str",
        reasoning="str",
        action="str",
        observation="str",
        answer="str"
    ),
    tools=[search_tool, calculator_tool]
)

result = react(question="今天北京的天气如何？")
```

## 💼 FDE 应用场景

### 场景 1: 实时知识问答 (ReAct)

**需求**: 回答需要最新信息的问题（股价、天气、新闻）

**方案**: ReAct + 搜索工具 + 计算器

**效果**: 回答准确率比纯 CoT 提升 30%

### 场景 2: 复杂文档分析 (HyDE)

**需求**: 从大量文档中找到能回答特定问题的段落

**方案**: HyDE + 混合检索

**效果**: 召回率提升 25%，尤其对抽象问题效果好

### 场景 3: 多跳问答 (ReAct)

**需求**: 需要多步推理的复杂问题（"公司的第一任CEO是谁？"）

**方案**: ReAct + 知识图谱查询

**效果**: 多跳问题准确率从 60% 提升至 85%

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| ReAct 循环过多 | 推理步骤过长或死循环 | 设置最大迭代次数 |
| HyDE 生成错误假设 | 假设答案误导检索 | 限制假设答案长度 |
| 工具调用失败 | 工具不可用或参数错误 | 降级处理 |

## 🔗 相关知识

- [[CoT]] - 推理基础
- [[Agent]] - Agent 架构
- [[DSPy]] - ReAct Module
- [[混合检索与召回率]] - HyDE 与混合检索结合

---

**向量检索标签**: ReAct, HyDE, 推理增强, 检索增强, Agent, 假设文档