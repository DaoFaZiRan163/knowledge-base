---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["Transformer", "注意力机制", "自注意力", "序列建模", "GPT"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["自然语言处理", "序列建模", "机器翻译", "文本生成"]
related_concepts: ["Attention", "BERT", "GPT-3", "Self-Attention"]
prerequisites: ["CNN基础"]
---

# Transformer — 序列建模的革命性架构

## 核心定义

**Transformer**：2017年由 Vaswani 等人在论文"Attention is All You Need"中提出，完全基于注意力机制（无 RNN/卷积）的序列到序列建模架构。

**核心理念**：通过自注意力（Self-Attention）并行建模序列依赖，突破 RNN 的顺序计算限制，实现并行训练和全局建模。

## 🎯 一句话总结

> **Transformer = 多头自注意力 + 位置编码 + 前馈网络，并行化建模任意距离依赖**

```
输入序列 → Embedding + 位置编码 → N× Encoder块 → N× Decoder块 → 输出
                    ↓                        ↓
              Multi-Head              Masked Multi-Head
              Self-Attention          Self-Attention
                    ↓                        ↓
              Feed Forward            Encoder-Decoder Attention
                                          ↓
                                      Feed Forward
```

## 🏗️ 核心组件

### Self-Attention 机制

```python
import torch
import torch.nn.functional as F
import math

def self_attention(Q, K, V, mask=None):
    """
    Q, K, V: query, key, value matrices
    返回: 注意力加权后的输出
    """
    d_k = Q.size(-1)

    # 计算注意力分数
    scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(d_k)

    # 应用 mask (可选)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)

    # Softmax 归一化
    attention_weights = F.softmax(scores, dim=-1)

    # 加权求和
    output = torch.matmul(attention_weights, V)

    return output, attention_weights

# Multi-Head Attention
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        self.num_heads = num_heads
        self.d_model = d_model
        self.depth = d_model // num_heads

        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def split_heads(self, x):
        batch_size = x.size(0)
        x = x.reshape(batch_size, -1, self.num_heads, self.depth)
        return x.permute(0, 2, 1, 3)

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)

        Q = self.split_heads(self.W_q(query))
        K = self.split_heads(self.W_k(key))
        V = self.split_heads(self.W_v(value))

        attn_output, _ = self_attention(Q, K, V, mask)

        # 拼接多头
        attn_output = attn_output.permute(0, 2, 1, 3).contiguous()
        attn_output = attn_output.reshape(batch_size, -1, self.d_model)

        return self.W_o(attn_output)
```

### 位置编码

```python
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super().__init__()

        # 预计算位置编码
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * -(math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]
```

## 💼 FDE 应用场景

### 场景: 实时机器翻译

**需求**: 毫秒级延迟的多语言翻译服务

**方案**: Transformer Encoder-Decoder 架构 + 模型压缩

**效果**: Google Translate 延迟降低 50%，质量超越人类平均水平

### 场景: 客服对话生成

**需求**: 自动生成符合语境的自然对话

**方案**: GPT（Transformer Decoder）架构 + RLHF 微调

**效果**: 对话流畅度提升，大幅减少人工客服工作量

## 📊 Transformer 家族

| 模型 | 架构 | 特点 |
|------|------|------|
| Original | Encoder-Decoder | 机器翻译专用 |
| BERT | Encoder Only | 双向理解，NLP 预训练 |
| GPT | Decoder Only | 单向生成，LLM 基础 |
| T5 | Encoder-Decoder | 统一文本到文本任务 |

## ⚠️ 复杂度问题

| 问题 | 描述 | 解决方案 |
|------|------|----------|
| O(n²) 注意力 | 序列长度平方的内存和计算 | Flash Attention, Sparse Attention |
| 长序列处理 | 64K+ token 的挑战 | Longformer, BigBird, Ring Attention |

## 🔗 相关知识

- [[Attention is All You Need]] - 原论文
- [[BERT]] - Encoder 代表
- [[GPT-3]] - Decoder 代表，大语言模型基础

---

**向量检索标签**: Transformer, 注意力机制, 自注意力, 序列建模, NLP, 深度学习架构