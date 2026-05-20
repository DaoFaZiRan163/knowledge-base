---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["Langfuse", "可观测", "LLM监控", "trace", "成本分析"]
source: 原创
created_date: 2026-05-19
updated_date: 2026-05-19
implementation_status: production_ready
use_cases: ["LLM应用监控", "问题诊断", "成本分析", "质量评估"]
related_concepts: ["并发熔断与容灾降级", "输出Guardrail与成本监控"]
prerequisites: ["LLM基础原理"]
---

# Langfuse 与可观测性

## 核心定义

**Langfuse**：开源的 LLM 应用可观测平台，提供 Traces、评估、质量监控等功能。

**可观测性 (Observability)**：通过系统输出的数据理解内部状态的能力，包含三个核心：Traces（调用链）、Metrics（指标）、Logs（日志）。

**核心理念**：LLM 应用的不确定性需要"可见性"，让开发者能追踪、诊断和优化 AI 应用。

## 🎯 一句话总结

> **Langfuse = LLM 应用的"黑匣子"，记录每一次调用的输入输出和中间状态**

```
传统监控:  指标曲线 → 判断健康状态
LLM可观测: Trace链路 → 理解每一步推理 → 精准定位问题
```

## 🏗️ 可观测性三大支柱

### Traces (调用链)

```
┌─────────────────────────────────────────────────────────────┐
│                    Langfuse Trace                           │
│                                                             │
│  User Query → Embedding → Vector Search → LLM Generation   │
│      │           │           │              │               │
│      └───────────┴───────────┴──────────────┘               │
│                     完整调用链                               │
│                                                             │
│  每个节点记录:                                              │
│  - 输入/输出                                                │
│  - 耗时                                                     │
│  - Token 消耗                                               │
│  - 错误信息                                                 │
└─────────────────────────────────────────────────────────────┘
```

### Metrics (指标)

| 指标类型 | 说明 | 告警阈值 |
|----------|------|----------|
| 请求量 | QPS、每秒请求数 | > 1000 QPS |
| 延迟 | P50/P95/P99 | > 30s P99 |
| 错误率 | 失败请求比例 | > 1% |
| Token 消耗 | 输入/输出 Token 数 | 每日预算 80% |
| 成本 | 每小时/每天成本 | 月度预算 90% |

### Logs (日志)

```
[2024-05-19 10:30:15] INFO trace_id=abc123
  user_id=user_456
  model=gpt-4
  input_tokens=1200
  output_tokens=350
  latency_ms=2800
  status=success

[2024-05-19 10:30:18] ERROR trace_id=def456
  error=rate_limit_exceeded
  retry_after=5
```

## 🔧 技术实现

### Langfuse Python SDK

```python
from langfuse import Langfuse

langfuse = Langfuse()

def generate_with_trace(prompt, user_id):
    # 开始 trace
    trace = langfuse.trace(
        name="llm_generation",
        user_id=user_id,
        metadata={"source": "api"}
    )

    # 记录各个阶段
    embedding_span = trace.span(name="embedding")
    query_embedding = embed_model.encode(prompt)
    embedding_span.end(output={"embedding": query_embedding})

    search_span = trace.span(name="vector_search")
    results = vector_db.search(query_embedding, k=5)
    search_span.end(output={"results_count": len(results)})

    generation_span = trace.span(name="llm_generation")
    response = llm.generate(context=results, query=prompt)
    generation_span.end(
        output={"response": response},
        metrics={"input_tokens": 1500, "output_tokens": 300}
    )

    trace.end()
    return response
```

### Langfuse 评估

```python
from langfuse.evaluation import evaluate

# 定义评估函数
def accuracy_score(trace):
    expected = trace.metadata.get("expected_answer")
    actual = trace.output.get("answer")
    return levenshtein_distance(expected, actual) < 5

# 批量评估
results = evaluate(
    dataset=test_dataset,
    implementation=my_llm_app,
    scoring_function=accuracy_score,
    num_samples=100
)

# 查看结果
print(f"准确率: {results.score}%")
print(f"失败案例: {results.failed_traces}")
```

### 自定义监控面板

```python
from langfuse import Langfuse

langfuse = Langfuse()

# 查询 trace
traces = langfuse.traces(
    start_time="2024-05-01",
    end_time="2024-05-19",
    user_id="user_123"
)

# 聚合统计
for trace in traces:
    print(f"""
    Trace ID: {trace.id}
    模型: {trace.model}
    输入Token: {trace.input_tokens}
    输出Token: {trace.output_tokens}
    延迟: {trace.latency_ms}ms
    成本: ${trace.cost}
    """)
```

## 💼 FDE 应用场景

### 场景 1: 生产问题诊断

**需求**: 用户报告 AI 回答质量下降，需要定位原因

**方案**:
1. 查看 Langfuse trace，找到最近的失败案例
2. 分析是检索问题还是生成问题
3. 定位具体环节（Embedding 超时？LLM 幻觉？）

**效果**: 问题定位时间从 2 小时缩短到 10 分钟

### 场景 2: 成本异常排查

**需求**: 发现某天 API 成本异常高

**方案**:
1. 按用户/时间聚合查看消费分布
2. 发现某用户 Token 消耗是平时的 10 倍
3. 检查该用户的请求日志，发现异常长的 Prompt

**效果**: 快速定位并处理资源滥用

### 场景 3: Prompt 版本对比

**需求**: 对比新旧版 Prompt 的效果差异

**方案**:
1. 为不同 Prompt 版本打标签
2. Langfuse 对比分析：延迟、Token 消耗、用户满意度
3. 数据驱动选择最优 Prompt

**效果**: Prompt 优化周期缩短，数据驱动决策

## 📊 关键功能

| 功能 | 说明 | 使用场景 |
|------|------|----------|
| Trace 详情 | 每次调用的完整输入输出 | 问题诊断 |
| 成本分解 | 按用户/模型/时间分解成本 | 成本分析 |
| 评估看板 | 质量评分趋势 | 效果监控 |
| Prompt 版本 | 对比不同 Prompt 效果 | 优化迭代 |
| 实时告警 | 异常情况即时通知 | 故障响应 |

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Trace 数据量大 | 生产环境调用量高 | 采样策略、只记录异常 |
| SDK 性能影响 | 同步记录增加延迟 | 异步写入、批处理 |
| 数据隐私 | Trace 包含敏感信息 | 脱敏处理、选择性记录 |

## 🔗 相关知识

- [[输出Guardrail与成本监控]] - 成本监控
- [[并发熔断与容灾降级]] - 故障处理
- [[数据清洗与评测集]] - 质量评估

---

**向量检索标签**: Langfuse, 可观测, LLM监控, 链路追踪, 成本分析, 质量评估