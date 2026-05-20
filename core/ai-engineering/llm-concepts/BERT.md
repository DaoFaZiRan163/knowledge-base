---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["BERT", "预训练语言模型", "遮盖语言模型", "自然语言理解", "谷歌"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["文本分类", "命名实体识别", "问答系统", "语言理解任务"]
related_concepts: ["Transformer", "GPT-3", "遮盖语言模型", "预训练微调"]
prerequisites: ["Transformer"]
---

# BERT — 双向预训练语言模型

## 核心定义

**BERT (Bidirectional Encoder Representations from Transformers)**：2018年由 Google 提出的预训练语言模型，基于 Transformer Encoder 架构，通过"遮盖语言模型"（MLM）和"下一句预测"（NSP）进行预训练，在 11 项 NLP 任务刷新记录。

**核心理念**：双向编码器同时看到上下文（左右），而非 GPT 的单向视角，实现更深层的语言理解。

## 🎯 一句话总结

> **BERT = Transformer Encoder + 双向注意力 + MLM预训练 + 任务微调**

```
BERT 预训练:
[CLS] 我 爱 [MASK] 国 [SEP]  中 [MASK]  是 我 [MASK] 家  → 预测 [MASK]

微调阶段:
[CLS] 我爱中国 [SEP] 中国是 我的国家 [SEP]
              ↓ BERT
         情感分类: 正面/负面
```

## 🏗️ 架构与预训练

### MLM vs NSP

```python
# MLM (Masked Language Model)
# 随机遮盖 15% 的 token，预测被遮盖的词
input: "我喜欢[MASK]国"
target: "中国"

# NSP (Next Sentence Prediction)
# 判断句子B是否紧接句子A
input: "[CLS] 我爱中国 [SEP] 它很美 [SEP]"
target: IsNext  # True

input: "[CLS] 我爱中国 [SEP] 苹果是水果 [SEP]"
target: NotNext  # False
```

### BERT 变体

| 模型 | 层数 | 隐藏维度 | 参数量 | 性能 |
|------|------|----------|--------|------|
| BERT-Base | 12 | 768 | 110M | 标准 |
| BERT-Large | 24 | 1024 | 340M | 更高 |
| ALBERT | 12 | 768 | 12M | 轻量 |
| RoBERTa | 12 | 768 | 125M | 去掉 NSP 更优 |

## 🔧 技术实现

```python
from transformers import BertModel, BertTokenizer

tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
model = BertModel.from_pretrained('bert-base-chinese')

# 输入
text = "我喜欢深度学习"
inputs = tokenizer(text, return_tensors='pt')

# 前向传播
outputs = model(**inputs)

# last_hidden_state: 所有token的embedding
# pooler_output: [CLS] token的embedding
```

### 微调示例

```python
class BertClassifier(nn.Module):
    def __init__(self, bert_model, num_classes):
        super().__init__()
        self.bert = bert_model
        self.classifier = nn.Linear(768, num_classes)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.pooler_output  # [CLS] token
        return self.classifier(pooled)
```

## 💼 FDE 应用场景

### 场景: 客服意图识别

**需求**: 识别用户问题意图，转接对应部门

**方案**: BERT 微调 意图分类模型

**效果**: 意图识别准确率 95%+，响应时间 < 50ms

### 场景: 金融文档抽取

**需求**: 从合同中抽取关键条款（甲方、乙方、金额、日期）

**方案**: BERT 微调 命名实体识别（NER）

**效果**: 实体抽取 F1 92%，人工审核工作量减少 70%

## 📊 BERT vs GPT

| 维度 | BERT (Encoder) | GPT (Decoder) |
|------|---------------|---------------|
| 注意力 | 双向（看到全文）| 单向（只看上文）|
| 预训练 | MLM + NSP | Next Token Prediction |
| 擅长 | 理解任务（分类、NER）| 生成任务（写作、对话）|
| 典型应用 | 文本分类、问答 | 文本生成、代码生成 |

## 🔗 相关知识

- [[Transformer]] - BERT 的基础架构
- [[GPT-3]] - GPT 系列（单向）
- [[预训练语言模型]] - 预训练-微调范式

---

**向量检索标签**: BERT, 双向语言模型, 预训练, 遮盖语言模型, 谷歌, NLP, 文本理解