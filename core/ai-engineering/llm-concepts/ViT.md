---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["ViT", "Vision Transformer", "视觉transformer", "图像分类", "Patch Embedding"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["图像分类", "图像编码", "多模态视觉", "视觉理解"]
related_concepts: ["Transformer", "CLIP", "BERT", "ImageNet"]
prerequisites: ["Transformer"]
---

# ViT — Vision Transformer 视觉分类

## 核心定义

**ViT (Vision Transformer)**：2020年由 Google 提出，将标准 Transformer 架构应用于图像分类任务，把图像分割为固定大小的 patch 后作为 token 输入。

**核心理念**：将图像视为"视觉单词序列"，用 NLP 领域的 Transformer 架构处理视觉任务。

## 🎯 一句话总结

> **ViT = 图像切块 + 线性映射 + 位置编码 + 标准 Transformer Encoder**

```
图像 (224×224)
  → 切分成 16×16 patches (14×14=196 patches)
  → 每 patch 展平为 768 维向量 (16×16×3)
  → 添加 [CLS] token 和位置编码
  → 输入标准 Transformer Encoder
  → [CLS] token 输出分类
```

## 🏗️ ViT 架构

### Patch Embedding

```python
import torch
import torch.nn as nn

class PatchEmbed(nn.Module):
    def __init__(self, img_size=224, patch_size=16, in_channels=3, embed_dim=768):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.num_patches = (img_size // patch_size) ** 2

        # 线性投影每个 patch
        self.proj = nn.Conv2d(in_channels, embed_dim,
                              kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        # x: [B, 3, 224, 224]
        x = self.proj(x)  # [B, 768, 14, 14]
        x = x.flatten(2)   # [B, 768, 196]
        x = x.transpose(1, 2)  # [B, 196, 768]
        return x
```

### ViT 模型

```python
class ViT(nn.Module):
    def __init__(self, img_size=224, patch_size=16, num_classes=1000,
                 embed_dim=768, depth=12, num_heads=12):
        super().__init__()

        self.patch_embed = PatchEmbed(img_size, patch_size)

        # [CLS] token 可学习
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))

        # 位置编码
        self.pos_embed = nn.Parameter(torch.zeros(1, 197, embed_dim))

        # Transformer Encoder
        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads)
            for _ in range(depth)
        ])

        # 分类头
        self.head = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        B = x.shape[0]

        # Patch 嵌入
        x = self.patch_embed(x)

        # 添加 [CLS] token
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)

        # 添加位置编码
        x = x + self.pos_embed

        # 通过 Transformer blocks
        for block in self.blocks:
            x = block(x)

        # [CLS] token 用于分类
        cls_token_final = x[:, 0]
        return self.head(cls_token_final)
```

## 💼 FDE 应用场景

### 场景: 医学图像诊断

**需求**: X光/CT 图像分类（肺炎检测、肿瘤识别）

**方案**: ViT 预训练 + 医疗数据微调

**效果**: 准确率与 ResNet 相当，ViT 大模型微调效果更优

### 场景: 遥感图像分析

**需求**: 卫星图像地物分类（建筑、植被、水体）

**方案**: ViT 处理大尺寸遥感图像

**效果**: 分割精度优于 CNN，擅长全局依赖建模

## 📊 ViT vs CNN 对比

| 维度 | ViT | CNN (ResNet) |
|------|-----|--------------|
| 归纳偏置 | 少（需要更多数据）| 多（平移不变性等）|
| 数据效率 | 低（需大数据）| 高（小数据也好）|
| 长距离依赖 | 强（全局 Attention）| 弱（靠深层卷积）|
| 计算效率 | 中等（Attention O(n²)）| 高（卷积 O(n)）|
| 预训练成本 | 高 | 中等 |

## ViT 家族

| 模型 | 参数 | ImageNet Top-1 |
|------|------|----------------|
| ViT-B/16 | 86M | 79.7% |
| ViT-L/16 | 307M | 87.1% |
| ViT-H/14 | 632M | 88.6% |
| DeiT | 86M | 81.8% (数据增强) |

## 🔗 相关知识

- [[Transformer]] - ViT 的基础架构
- [[CLIP]] - ViT 用于图文对学习
- [[ResNet]] - CNN 对比

---

**向量检索标签**: ViT, Vision Transformer, 视觉Transformer, 图像分类, Patch Embedding, 谷歌