---
type: book
category: ["AI论文", "Agent", "推理与行动"]
difficulty: intermediate
tags: ["ReAct", "CoT", "Agent", "工具调用", "推理", "论文"]
reading_status: completed
completion_date: 2026-05-18
prerequisites: ["LLM基础", "提示工程基础"]
related_books: ["《大语言模型-CS224N》", "《LangChain实战》"]
related_concepts: ["Chain of Thought", "Tool Use", "ReAct", "Scratchpad"]
---

# ReAct: Synergizing Reasoning and Acting in Language Models

## 📖 基本信息
- **作者**: Shunyu Yao, Jeffrey Zhao, Dian Yu, et al.（Princeton + Google）
- **发表**: ICLR 2023
- **核心主题**: 交替进行推理（Reasoning）和行动（Acting），让 LLM 能够与外部工具协作解决复杂任务
- **目标读者**: 构建 LLM Agent 的工程师；理解 AI Agent 范式的研究者
- **阅读难度**: intermediate

## 🎯 核心价值
> CoT 让模型会"想"，Tool Use 让模型会"做"——ReAct 将两者交替结合，产生了比单独使用任何一种都强得多的 Agent 范式，成为现代 LLM Agent 的基础框架。

## 📚 知识框架

### 1. 问题背景

#### 现有方法的局限
- **只用 CoT（思维链）**：推理时没有外部信息，容易产生幻觉；无法获取最新知识
- **只用 Act（行动/工具调用）**：没有中间推理，无法处理复杂多步任务；调试困难

#### ReAct 的洞察
将思维（Thought）和行动（Action）交替进行：
- 思维帮助 Agent 分析当前状态、制定下一步计划
- 行动执行具体操作（搜索、查询、计算）
- 观察（Observation）来自环境的反馈，更新 Agent 的认知

---

### 2. ReAct 框架

#### 基本格式（Trajectory）
```
问题（Human）：
  查找《代码整洁之道》的作者，并搜索他的其他著作

Thought 1: 
  我需要先搜索《代码整洁之道》来找到它的作者。

Action 1: 
  Search["代码整洁之道 作者"]

Observation 1: 
  《代码整洁之道》的作者是 Robert C. Martin，又称 Uncle Bob。

Thought 2: 
  知道了作者是 Robert C. Martin，现在搜索他的其他著作。

Action 2: 
  Search["Robert C. Martin 著作"]

Observation 2: 
  Robert C. Martin 的其他著作包括《代码整洁之道：程序员的职业素养》《架构整洁之道》《敏捷软件开发》等。

Thought 3: 
  已经找到了所有需要的信息，可以给出最终答案。

Action 3: 
  Finish["《代码整洁之道》的作者是 Robert C. Martin（Uncle Bob），他的其他著作包括《架构整洁之道》《代码整洁之道：程序员的职业素养》《敏捷软件开发》。"]
```

---

### 3. 实验结论

#### 对比 CoT 和 Act
| 方法 | HotpotQA | Fever | ALFWorld | WebShop |
|------|---------|-------|---------|---------|
| Act | 25.7 | 58.9 | 45% | 33% |
| CoT | 29.4 | 56.3 | — | — |
| **ReAct** | **35.1** | **60.9** | **71%** | **40%** |

- 结合两者显著优于任何单一方法
- 知识密集型任务（问答、事实验证）改善明显
- 交互式决策任务（游戏、购物）效果尤其突出

#### ReAct 的优势
1. **减少幻觉**：每个推理步骤都有外部观察锚定
2. **可解释性**：Thought 提供了可读的推理轨迹
3. **可纠错**：可以在中途识别并纠正错误
4. **人工干预点**：每个 Action 前可以人工检查 Thought

---

### 4. ReAct 的实现

#### Prompt 模板（LangChain 中的 `hwchase17/react`）
```
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
```

#### LangChain 实现
```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub

# 使用标准 ReAct Prompt
prompt = hub.pull("hwchase17/react")

# 定义工具
tools = [search_tool, calculator_tool, db_query_tool]

# 创建 Agent
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=15,
    handle_parsing_errors=True
)
```

---

### 5. ReAct 的变体与扩展

#### Reflexion（2023）
- 在 ReAct 基础上加入"自我反思"
- 任务失败后，用 LLM 生成言语反馈
- 将反馈存入记忆，下次尝试时参考
- 在代码生成任务上显著提升

#### ReWOO（Reasoning WithOut Observation）
- 预先生成完整计划（所有 Action），再批量执行
- 减少 LLM 调用次数，降低延迟
- 适合工具调用延迟高的场景

#### Tree of Thoughts（ToT）
- 每一步生成多个 Thought，形成树结构
- BFS/DFS 搜索最优路径
- 适合需要回溯的复杂规划问题

---

### 6. 局限性与工程注意点

#### 已知局限
1. **动作空间设计**：工具描述（docstring）的质量直接影响 Agent 决策
2. **解析脆弱性**：输出格式解析容易失败（LLM 不总是遵守格式）
3. **长链路退化**：超过 10+ 步时，LLM 容易忘记原始目标
4. **幻觉 Action**：LLM 可能调用不存在的工具或传入错误参数

#### 工程实践
```python
# 1. 工具 docstring 要明确、具体
@tool
def query_sales_db(sql: str) -> str:
    """
    执行 SQL 查询销售数据库。
    只支持 SELECT 语句。
    表结构：orders(id, user_id, amount, created_at), products(id, name, price)
    返回：JSON 格式的查询结果，最多 100 行
    """
    ...

# 2. 处理解析错误
agent_executor = AgentExecutor(
    handle_parsing_errors="请严格按照格式输出：Action: ...\nAction Input: ..."
)

# 3. 限制迭代次数，防止无限循环
agent_executor = AgentExecutor(max_iterations=10, max_execution_time=60)
```

---

## 🔑 关键概念

### Thought-Action-Observation 循环
**定义**: LLM 交替输出推理过程（Thought）、执行工具（Action）、接收结果（Observation）

**重要性**: 这个循环是现代 LLM Agent 的核心范式，几乎所有 Agent 框架都基于此

**应用场景**:
1. 信息检索任务：搜索 + 筛选 + 综合
2. 代码执行任务：写代码 + 运行 + 调试
3. 数据分析任务：查询 + 计算 + 可视化

---

### Scratchpad（草稿纸）
**定义**: 上下文窗口中保留的 Thought 历史，作为 Agent 的"工作记忆"

**重要性**: Scratchpad 太长会超出上下文窗口；需要管理 Scratchpad 的长度

**应用场景**:
1. 短任务：完整保留 Scratchpad
2. 长任务：压缩/摘要历史 Thought
3. 多 Agent：每个 Agent 有独立 Scratchpad

---

## 💡 实战应用场景

### 场景 1: 构建 FDE 的技术调研 Agent
**背景**: 需要自动调研客户使用的技术栈，生成评估报告

**解决方案**: ReAct Agent + 多工具

**实施步骤**:
1. 定义工具：Web 搜索、GitHub 仓库分析、文档读取
2. 系统 Prompt：明确调研目标和输出格式
3. 用 ReAct 框架让 Agent 自主规划调研步骤
4. 最终输出结构化报告（技术栈 + 成熟度 + 风险）

**预期效果**: 几分钟完成人工需要几小时的调研

---

### 场景 2: 客户现场数据分析 Agent
**背景**: 在客户现场，需要快速回答数据相关问题

**解决方案**: ReAct + SQL 工具 + 计算工具

**实施步骤**:
1. 接入客户数据库的只读连接
2. 定义 `query_db(sql)` 工具
3. ReAct Agent 将自然语言问题转换为 SQL
4. 执行查询 → 解读结果 → 生成可视化

**预期效果**: 非技术的业务人员也能获得数据洞察

---

## 🔗 相关技术栈
- **框架**: LangChain（`create_react_agent`）, LangGraph
- **论文**: arxiv 2210.03629
- **相关工作**: Reflexion, ToT, ReWOO, AutoGPT, BabyAGI

---

## 📝 个人笔记

### 重要洞察
- ReAct 的核心贡献是"把 CoT 和工具调用统一到一个框架里"，简单但影响深远
- Thought 的质量取决于 Prompt 中的 Few-shot 示例，这是调优 Agent 的关键点
- FDE 场景：向客户展示 Agent 的推理过程（Thought）能极大增加信任感

### 待深入研究
- [ ] 阅读 Reflexion 论文，了解自我反思机制
- [ ] 研究 Tree of Thoughts 在规划问题中的应用
- [ ] 了解 Function Calling vs ReAct 的工程选型

### 实践项目
- [ ] 实现一个 ReAct Agent，工具包括网络搜索 + 计算器 + 文本文件读写
- [ ] 对比 ReAct 和 Function Calling 在同一任务上的完成质量和 token 消耗

---

## 🎓 学习检验

### 自测问题
1. 为什么在 ReAct 中 Thought 步骤很重要，不直接输出 Action？
2. ReAct 相比纯 Act 在哪类任务上改善最明显？
3. Scratchpad 变得很长时会产生什么问题？如何缓解？
4. Tree of Thoughts 和 ReAct 的适用场景有何不同？
5. 工具的 docstring 质量为什么对 ReAct Agent 的性能影响这么大？

### 实践任务
- [ ] 手写一个 ReAct Few-shot Prompt，让 LLM 用工具回答 3 步以上的问题
- [ ] 使用 LangSmith 追踪一次 ReAct 调用，分析每个 Thought 的质量

---

## 📊 知识关联

### 前置知识
- [[大语言模型-CS224N]]
- [[LangChain实战]]

### 后续学习
- [[LangGraph工作流编排]]
- [[Hermes-Agent工作系统]]
- [[Multi-Agent编排平台产品设计]]

### 并行学习
- [[Multi-Agent-Systems-Weiss]]
- [[Prompt工程化团队规范]]

---

## 🏷️ 标签系统
#论文 #技术 #Agent #intermediate

---
**阅读开始**: 2026-05-18
**阅读完成**: 2026-05-18
**下次复习**: 2026-06-18
**总计用时**: 知识提炼版（直接生成）
**推荐指数**: ⭐⭐⭐⭐⭐
