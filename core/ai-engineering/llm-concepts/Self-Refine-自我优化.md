---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["Self-Refine", "自我优化", "迭代优化", "LLM优化", "反馈机制"]
source: 原创
created_date: 2026-05-19
updated_date: 2026-05-19
implementation_status: production_ready
use_cases: ["文本优化", "代码改进", "创意生成", "问答改进"]
related_concepts: ["CoT", "Self-Consistency", "DSPy", "Agent"]
prerequisites: ["LLM基础原理", "CoT"]
---

# Self-Refine — 自我优化提示

## 核心定义

**Self-Refine** 是一种让 LLM 通过**迭代式反馈与改进**来优化输出的技术。模型先生成初始版本，然后**自我评估问题**，再**针对问题改进**，循环直到满意。

**核心理念**：不是一次性生成最优答案，而是通过"生成→评估→改进"的迭代循环逐步逼近最佳结果。

## 🎯 一句话总结

> **Self-Refine = 生成初始答案 → 自我批评 → 针对性改进 → 重复直到满意**

```
传统方式:  问题 → 一次性生成 → 答案 (可能不满意)
Self-Refine:
           问题 → 生成v1 → 评估: 问题A, 问题B
                         ↓
                    改进v2 → 评估: 问题B已修复, 问题C存在
                         ↓
                    改进v3 → 评估: 满足要求 ✓
           最终输出: v3
```

## 🏗️ 架构原理

### 核心机制

```
┌────────────────────────────────────────────────────────────┐
│                    Self-Refine 循环                         │
│                                                             │
│   ┌───────────┐                                           │
│   │  初始生成  │ ← 原始输入                                 │
│   └─────┬─────┘                                           │
│         │                                                  │
│         ▼                                                  │
│   ┌───────────┐                                           │
│   │  自我评估  │ ← 评估标准/反馈                            │
│   │ 问题: ... │                                           │
│   └─────┬─────┘                                           │
│         │                                                  │
│         ▼                                                  │
│   ┌───────────┐                                           │
│   │  针对性改进 │ ← 根据评估反馈调整                         │
│   └─────┬─────┘                                           │
│         │                                                  │
│         ▼                                                  │
│   ┌───────────┐                                           │
│   │  停止条件? │ ← 达到质量阈值 或 达到最大迭代次数           │
│   └─────┬─────┘                                           │
│         │否  │是                                           │
│         ▼    ▼                                             │
│      继续   输出最终结果                                     │
│     循环    └──────────────────────────────────────────────┘
└────────────────────────────────────────────────────────────┘
```

### 三阶段结构

| 阶段 | 输入 | 输出 | 说明 |
|------|------|------|------|
| Generate | 原始输入 / 上一轮反馈 | 初始版本 / 新版本 | 生成内容 |
| Critique | 当前版本 | 问题列表 + 改进建议 | 评估内容 |
| Refine | 当前版本 + 批评意见 | 改进版本 | 优化内容 |

### 评估维度

```python
# 典型的评估维度
critique_dimensions = {
    "accuracy": "答案是否正确？",
    "completeness": "是否涵盖所有要点？",
    "clarity": "表达是否清晰易懂？",
    "coherence": "逻辑是否连贯？",
    "relevance": "是否切题，无无关内容？",
    "conciseness": "是否简洁，不冗余？"
}
```

## 🔧 技术实现

### 基本实现

```python
def self_refine(question, max_iterations=3):
    """
    Self-Refine 基本实现
    """
    current_output = llm.generate(f"回答以下问题: {question}")

    for iteration in range(max_iterations):
        # 阶段1: 自我批评
        critique = llm.generate(f"""
请评估以下回答的质量，并指出需要改进的地方：

回答: {current_output}

评估维度:
1. 准确性 - 回答是否正确？
2. 完整性 - 是否涵盖所有要点？
3. 清晰度 - 表达是否清晰？

如果回答已经很好，请直接说"无需改进"。
否则，请列出具体问题：
""")

        # 检查是否需要改进
        if "无需改进" in critique:
            break

        # 阶段2: 针对性改进
        current_output = llm.generate(f"""
基于以下反馈改进你的回答：

原始回答: {current_output}

反馈: {critique}

请根据反馈生成改进版本：
""")

    return current_output
```

### 详细版本（带评估维度）

```python
def self_refine_detailed(question, max_iterations=5):
    output = llm.generate(question)

    critique_template = """
你是一个批评家。请评估以下回答在以下维度的问题：

维度:
1. accuracy（准确性）: 事实是否正确？
2. relevance（相关性）: 是否切题？
3. clarity（清晰度）: 是否易于理解？
4. completeness（完整性）: 是否完整？

回答: {output}

请逐维度指出问题，格式如下：
- [维度名]: [问题描述]（如果没问题写"OK"）
"""

    refine_template = """
你是一个作家。请根据以下反馈改进你的回答：

原始回答: {output}

批评: {critique}

请生成改进版本：
"""

    for _ in range(max_iterations):
        # 评估
        critique = llm.generate(critique_template.format(output=output))

        # 检查是否达标
        if all("OK" in line for line in critique.split("\n")):
            break

        # 改进
        output = llm.generate(refine_template.format(
            output=output,
            critique=critique
        ))

    return output
```

### 与 DSPy 结合

```python
import dspy

class SelfRefineModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.Predict(
            Signature.from_components(
                context="str", question="str", answer="str"
            )
        )
        self.critique = dspy.Predict(
            Signature.from_components(
                answer="str", critique="str"
            )
        )
        self.refine = dspy.Predict(
            Signature.from_components(
                answer="str", critique="str", improved="str"
            )
        )

    def forward(self, question, max_iters=3):
        # 初始生成
        out = self.generate(question=question)
        answer = out.answer

        for _ in range(max_iters):
            # 批评
            crit = self.critique(answer=answer)
            if "无需改进" in crit.critique:
                break

            # 改进
            refined = self.refine(answer=answer, critique=crit.critique)
            answer = refined.improved

        return answer
```

### 生产环境示例

```python
class SelfRefineRAG:
    """
    结合 RAG 的 Self-Refine 实现
    """

    def __init__(self, retriever):
        self.retriever = retriever

    def query_with_refine(self, question, max_iters=3):
        context = self.retriever.search(question)

        # 初始答案
        prompt = f"基于以下上下文回答：\n\n{context}\n\n问题: {question}"
        answer = llm.generate(prompt)

        for i in range(max_iters):
            # 评估
            critique = self._critique(answer, question, context)
            if critique["needs_improvement"]:
                # 改进
                answer = self._refine(answer, critique["feedback"], context)
            else:
                break

        return {
            "answer": answer,
            "iterations": i + 1,
            "critiques": [critique]
        }

    def _critique(self, answer, question, context):
        # 评估逻辑
        prompt = f"""
评估以下回答：

回答: {answer}
问题: {question}

检查：
1. 事实准确性 - 是否与上下文一致？
2. 问题匹配 - 是否回答了问题？
3. 完整性 - 是否完整？

如果有问题请具体说明，否则说"无需改进"。
"""
        return {"needs_improvement": True, "feedback": llm.generate(prompt)}
```

## 💼 FDE 应用场景

### 场景 1: 营销文案优化

**客户需求**: AI 生成营销文案，需要迭代优化直到满意

**FDE 分析**:
- **痛点**: 一次性生成的文案质量不稳定
- **机会**: Self-Refine 迭代优化直到符合品牌调性
- **风险**: 迭代次数过多导致延迟和成本

**实施策略**:
1. 定义评估标准：品牌调性、转化率、清晰度
2. 设置最大迭代次数（通常 3-5 次）
3. 关键迭代点可加入人工反馈

**预期效果**: 文案质量一致性提升，客户修改次数减少 60%

### 场景 2: 技术方案评审

**客户需求**: AI 辅助评审技术方案，提出改进建议

**FDE 分析**:
- **痛点**: 一次性评审可能遗漏问题
- **机会**: Self-Refine 多轮迭代，深入分析
- **风险**: 技术细节在迭代中可能被稀释

**实施策略**:
1. 第一轮：全面评审，记录所有问题
2. 第二轮：针对高优先级问题深入分析
3. 第三轮：整合所有建议，形成完整评审报告

**预期效果**: 评审深度提升，问题发现率增加 40%

### 场景 3: 客户服务话术优化

**客户需求**: 将用户投诉转化为专业的客服回复

**FDE 分析**:
- **痛点**: 简单回复不够专业或缺乏同理心
- **机会**: Self-Refine 迭代优化语气和内容
- **风险**: 迭代后回复可能过长

**实施策略**:
1. 定义语气标准：专业、同理心、简洁
2. 迭代改进：准确 → 有同理心 → 简洁
3. 最终检查：是否适合公开回复

**预期效果**: 客户满意度提升，投诉升级率降低

### 场景 4: 代码 Review

**客户需求**: AI 自动 Review 代码并提出改进建议

**FDE 分析**:
- **痛点**: 一次性 Review 可能遗漏问题或建议不够具体
- **机会**: Self-Refine 迭代深入，发现更深层问题
- **风险**: 迭代后建议可能过于冗长

**实施策略**:
1. 第一轮：基础 Review（语法、风格）
2. 第二轮：深度 Review（逻辑、安全）
3. 第三轮：优化建议优先级排序

**预期效果**: Code Review 效率提升，发现更多深层问题

## ⚠️ 常见陷阱与解决方案

### 陷阱 1: 迭代改进但方向错误
**症状**: 多次迭代后输出反而变差

**原因分析**: 批评阶段对问题判断错误，改进方向偏离

**解决方案**:
1. 在批评后加入"改进方向确认"步骤
2. 设置最小质量阈值，未达到则回退
3. 保留每次迭代版本，最终选择最优

### 陷阱 2: 迭代无限进行
**症状**: 模型不断"改进"但永远达不到满意

**原因分析**: 停止条件设置不合理或模型无法准确判断质量

**解决方案**:
1. 设置最大迭代次数（硬性限制）
2. 显式定义"满意"的标准
3. 在评估 Prompt 中加入"如果已达标准请明确说明"

### 陷阱 3: 批评过于宽泛
**症状**: 模型给出"不够好"但不说具体问题

**原因分析**: 评估维度不够具体

**解决方案**:
1. 细化评估维度为具体问题
2. 要求批评必须包含具体修改建议
3. 提供评估维度的示例帮助模型理解

### 陷阱 4: 成本与延迟失控
**症状**: Self-Refine 迭代 10+ 次，成本爆炸

**原因分析**: 未设置迭代上限或自适应逻辑

**解决方案**:
1. 硬性限制最大迭代次数（建议 3-5 次）
2. 早期评估：简单问题 1-2 次，复杂问题 3-5 次
3. 并行评估与改进（非串行）

## 📊 性能优化

### 性能指标
- **质量提升**: 具体取决于任务，通常第二轮改进效果最明显
- **延迟增加**: 迭代次数 × 单次生成延迟
- **成本**: 迭代次数 × 单次调用成本

### 优化策略
1. **自适应迭代**: 根据问题复杂度动态调整迭代次数
2. **早停策略**: 达到质量阈值立即停止
3. **并行批评**: 一次调用生成多个维度的批评
4. **缓存优化结果**: 相似问题直接复用优化后的答案

## 🔗 相关知识

### 前置知识
- [[LLM基础原理]] - LLM 基本工作机制
- [[CoT]] - 思维链，理解生成-评估的基本模式

### 相关概念
- [[Self-Consistency]] - 自洽性，与 Self-Refine 互补
- [[DSPy]] - DSPy 的 Module 封装方式
- [[Agent]] - Self-Refine 是 Agent 的基础能力之一

### 进阶主题
- [[Constitutional AI]] - AI 自我对齐的更系统方法
- [[PEARL]] - 自我改进的学习方法
- [[Reflexion]] - 语言增强的自我反思

## 📚 推荐资源

### 论文
- **Self-Refine: Iterative Refinement with Self-Feedback**: Madaan et al., 2023
- **Constitutional AI: Harmlessness from AI Feedback**: Anthropic, 2022
- **Reflexion: Language Agents with Verbal Reinforcement Learning**: Shinn et al., 2023

### 实践
- [DSPy Self-Refine](https://dspy.ai/learn/advanced/)
- [LangChain Self-Refine](https://python.langchain.com/docs/use_cases/more)

## 🔍 FAQ

### Q1: Self-Refine 和 Self-Consistency 可以一起用吗？

可以。推荐使用顺序：

1. **Self-Consistency → 得出多个候选答案**
2. **Self-Refine → 优化最终答案**

```
问题 → Self-Consistency(5次) → 投票得出A/B
     → Self-Refine(A) → A+
     → Self-Refine(B) → B+
     → 最终选择质量更好的
```

### Q2: 迭代次数如何选择？

| 任务类型 | 推荐迭代次数 | 原因 |
|----------|--------------|------|
| 简单问答 | 1-2 | 问题本身不复杂 |
| 文本写作 | 3-4 | 需要多轮优化风格/内容 |
| 代码生成 | 2-3 | 语法检查后可快速收敛 |
| 复杂推理 | 4-5 | 需要深入分析 |

### Q3: Self-Refine 适用于所有任务吗？

不。Self-Refine 最适合：
- ✅ 创意写作、文案优化
- ✅ 需要多轮打磨的文本生成
- ✅ 代码改进、技术文档
- ❌ 简单事实问答（迭代反而增加延迟）
- ❌ 实时性要求高的场景
- ❌ 已有标准答案的任务

### Q4: 如何避免模型"自我满足"？

模型可能过早认为"无需改进"。解决方案：
1. 在 Prompt 中强调"严格评估"
2. 要求批评必须指出至少一个具体问题
3. 使用外部验证（如调用工具检查答案正确性）

---

**创建日期**: 2026-05-19
**最后更新**: 2026-05-19
**掌握程度**: 理论理解
**使用频率**: 中
**向量检索标签**: Self-Refine, 自我优化, 迭代改进, 反馈机制, LLM优化, 评估驱动