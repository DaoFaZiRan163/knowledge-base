---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["CLIP", "多模态", "图文对齐", "OpenAI", "对比学习"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["图文检索", "图像分类", "零样本学习", "视觉推理"]
related_concepts: ["ViT", "Transformer", "多模态", "零样本学习"]
prerequisites: ["Contrastive Learning", "Transformer"]
---

# CLIP — 对比语言-图像预训练

## 核心定义

**CLIP (Contrastive Language-Image Pre-training)**：2021年由 OpenAI 提出的多模态模型，通过对比学习在 4 亿图文对数据集上训练，实现"图像"与"文本"联合理解，可在零样本情况下完成图像分类等任务。

**核心理念**：图像和文本在同一个向量空间中对齐，学习"图像→文本"的通用表示。

## 🎯 一句话总结

> **CLIP = 4亿图文对 + 双塔对比学习 + 零样本图像分类**

```
训练数据: 4亿图文对 (来自互联网)
模型结构: Image Encoder + Text Encoder
训练目标: 最大化匹配对相似度，最小化不匹配对相似度
```

## 🏗️ 架构与训练

### CLIP 结构

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIP 训练                                 │
│                                                             │
│  Image Encoder (ViT)          Text Encoder (Transformer)    │
│       ↓                            ↓                        │
│  I1, I2, ..., In              T1, T2, ..., Tn                │
│       ↓                            ↓                        │
│  Image Embeddings             Text Embeddings               │
│       ↓                            ↓                        │
│       └────────── dot product ─────────┘                   │
│                    ↓                                        │
│            对比学习损失                                      │
└─────────────────────────────────────────────────────────────┘
```

### 对比学习目标

```python
import torch
import torch.nn.functional as F

def clip_loss(image_features, text_features):
    # 计算相似度矩阵
    logits = image_features @ text_features.T

    # 对角线是正样本
    labels = torch.arange(len(image_features))

    # 对称交叉熵损失
    image_loss = F.cross_entropy(logits, labels)
    text_loss = F.cross_entropy(logits.T, labels)
    return (image_loss + text_loss) / 2
```

### Zero-shot 分类示例

```python
from PIL import Image
import clip

model, preprocess = clip.load("ViT-B/32")

# 图像
image = preprocess(Image.open("dog.jpg")).unsqueeze(0)

# 文本描述（候选类别）
text_descriptions = [
    "a photo of a dog",
    "a photo of a cat",
    "a photo of a car"
]
text = clip.tokenize(text_descriptions)

# 提取特征
with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)

    # 计算相似度
    logits_per_image, _ = model(image, text)
    probs = logits_per_image.softmax(dim=-1).cpu().numpy()

# 输出: [0.92, 0.05, 0.03] - 92%概率是狗
```

## 💼 FDE 应用场景

### 场景: 电商商品搜索

**需求**: 用户用自然语言搜索商品图片

**方案**: CLIP 文本→图像检索，无需标注数据

**效果**: 搜索准确率 88%，超越传统关键词搜索

### 场景: 工业缺陷检测

**需求**: 检测产品外观缺陷，无需大量缺陷样本

**方案**: CLIP 零样本分类，"正常" vs "有缺陷"

**效果**: 缺陷检测召回率 85%，减少 90% 的标注成本

### 场景: 内容审核

**需求**: 检测图像是否包含违规内容

**方案**: CLIP 零样本 + 文本描述违规类型

**效果**: 审核效率提升，误杀率降低 30%

## 📊 CLIP 影响

| 指标 | 说明 |
|------|------|
| 训练数据 | 4亿图文对，来源为互联网 |
| 零样本 ImageNet | 76.2% top-1，与监督 ResNet50 相当 |
| 多模态 | 首次大规模验证图文联合表示 |
| 后续 | OpenCLIP, Llava, GPT-4V 等 |

## 🔗 相关知识

- [[ViT]] - CLIP 的 Image Encoder
- [[Transformer]] - CLIP 的 Text Encoder
- [[多模态大模型]] - CLIP 是多模态 LLM 的基础

---

**向量检索标签**: CLIP, 多模态, 图文对齐, 对比学习, OpenAI, 零样本学习, 视觉语言模型