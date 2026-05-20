---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["KV-Cache", "前缀缓存", "推理优化", "Attention", "Context复用"]
source: 原创
created_date: 2026-05-19
updated_date: 2026-05-19
implementation_status: production_ready
use_cases: ["长上下文推理", "流式输出", "多轮对话优化", "成本控制"]
related_concepts: ["Attention", "Transformer", "Quantization", "预训练"]
prerequisites: ["Transformer", "LLM基础原理"]
---

# KV-Cache 与前缀缓存

## 核心定义

**KV-Cache** (Key-Value Cache)：在自回归生成过程中，缓存已计算的 Key 和 Value 向量，避免重复计算。

**前缀缓存** (Prefix Caching)：将可复用的系统 Prompt、前缀文本的 KV 张量缓存起来，多请求共享。

**核心理念**：Transformer 的 Attention 计算是 O(n²)，通过缓存已计算结果，复用前缀计算，只增量计算新 token。

## 🎯 一句话总结

> **KV-Cache = 空间换时间，缓存已计算的注意力键值对**

```
无缓存:  Token1 → Token2 → Token3 → Token4
         [K1,V1]   [K2,V2]   [K3,V3]   [K4,V4]
         每步重新计算所有历史

有缓存:  Token1 → Token2 → Token3 → Token4
         [K1,V1]   [K2,V2]   [K3,V3]   [K4,V4]
                            ↑缓存↑   只计算新token
```

## 🏗️ 原理详解

### 标准自回归生成

```python
# 无缓存的生成方式
for token in new_tokens:
    # 每步都要重新计算所有历史token的attention
    context = torch.cat([past_kv, new_kv], dim=-2)
    output = attention(query, context)
    past_kv = context  # 保存但每次都要重算
```

### KV-Cache 原理

```python
# 有缓存的生成方式
past_kv = None
for token in new_tokens:
    # 只计算新token的K/V
    q = compute_query(token)
    k, v = compute_kv(token)

    # 与缓存拼接
    k_full = torch.cat([past_kv.k, k], dim=-2)
    v_full = torch.cat([past_kv.v, v], dim=-2)

    output = attention(q, k_full, v_full)
    past_kv = (k_full, v_full)  # 更新缓存
```

### 前缀缓存场景

```
请求1: [System Prompt] + [User Question A]
       └──────────────前缀─────────────┘

请求2: [System Prompt] + [User Question B]
       └──────────────前缀─────────────┘

请求3: [System Prompt] + [User Question C]
       └──────────────前缀─────────────┘

→ 前缀[System Prompt]的KV只计算一次，多请求共享
```

## 💼 FDE 应用场景

### 场景 1: 长文档分析

**痛点**: 处理100页PDF时，每次生成都要重新计算整个上下文

**解决方案**: 文档 embedding 计算后缓存，后续问答只增量计算用户问题部分

**效果**: 长文档场景延迟降低 60-80%

### 场景 2: 多轮对话

**痛点**: 每轮对话都重算历史上下文

**解决方案**: 系统 Prompt 和对话历史 KV 缓存，新消息只计算增量

**效果**: 多轮对话延迟降低 50-70%

### 场景 3: 高并发场景成本控制

**痛点**: 大量相似请求重复计算相同前缀

**解决方案**: 前缀缓存 + 请求合并

**效果**: GPU 计算量减少 40-60%

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 内存占用大 | KV 张量随序列长度线性增长 | 量化压缩 / 分段缓存 |
| 缓存失效 | 系统更新后前缀变化 | 缓存失效策略 |
| 多实例不一致 | 分布式环境下缓存未同步 | 集中式缓存服务 |

## 🔗 相关知识

- [[Attention]] - Attention 机制原理
- [[Quantization]] - KV-Cache 量化压缩
- [[Transformer]] - Transformer 架构

---

**向量检索标签**: KV-Cache, 前缀缓存, 推理优化, 注意力优化, 上下文复用