---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["ResNet", "残差网络", "残差连接", "深度网络", "梯度消失"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["图像分类", "目标检测", "语义分割", "深度网络训练"]
related_concepts: ["AlexNet", "ImageNet", "VGG", "退化问题"]
prerequisites: ["CNN基础"]
---

# ResNet — 残差网络与深度网络的突破

## 核心定义

**ResNet (Residual Network)**：2015年由何恺明等人提出，通过"残差连接"（skip connection）解决深层网络训练困难的问题，是深度学习史上最重要的架构之一。

**核心理念**：让网络学习"残差"而非"完整映射"，使梯度能够直接流向浅层，从而训练超深网络（152层）。

## 🎯 一句话总结

> **ResNet = 残差连接让梯度直达底层，深层网络不再退化，152层成为可能**

```
传统网络:    x → Conv → Conv → ... → Conv → 输出
ResNet:      x → Conv → Conv → ... → Conv → 输出
                ↘__________________↗
                   (残差连接 +)
```

## 🏗️ 残差模块

### Basic Block

```python
class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()

        # 主路径
        self.conv1 = nn.Conv2d(in_channels, out_channels,
                               kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels,
                               kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)

        # 残差连接
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels,
                         kernel_size=1, stride=stride),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        out += self.shortcut(residual)  # 残差相加
        out = self.relu(out)

        return out
```

### 为什么残差有效

| 问题 | 传统深层网络 | ResNet |
|------|-------------|--------|
| 梯度消失 | 链式法则导致梯度指数衰减 | 残差连接提供梯度直达通道 |
| 退化问题 | 深层网络准确率反而下降 | 恒等映射保证至少不减 |
| 训练难度 | 需要谨慎的权重初始化 | 更易收敛 |

## 🏗️ ResNet 变体

| 模型 | 层数 | Top-1 准确率 | 参数量 |
|------|------|--------------|--------|
| ResNet-18 | 18 | 69.8% | 11.7M |
| ResNet-34 | 34 | 73.3% | 21.8M |
| ResNet-50 | 50 | 76.1% | 25.6M |
| ResNet-101 | 101 | 77.4% | 44.5M |
| ResNet-152 | 152 | 78.3% | 60.2M |

### Bottleneck 设计

```
ResNet-50+ 使用 Bottleneck:
输入 → 1x1 Conv(压缩) → 3x3 Conv(处理) → 1x1 Conv(恢复) → 输出

例子: 256 → 64 → 64 → 64 → 256
      输入    压缩   处理   恢复
```

## 🔧 应用场景

### 场景: 医学图像分析

**需求**: 从 CT 扫描中检测肿瘤

**方案**: ResNet-50 迁移学习 + 病灶区域标注

**效果**: 病灶检测准确率 94%，超过放射科医生平均水平

### 场景: 人脸识别

**需求**: 高精度人脸验证系统

**方案**: ResNet 作为 backbone + ArcFace 损失函数

**效果**: LFW 准确率 99.8%

## 📊 历史意义

| 里程碑 | 说明 |
|--------|------|
| 2015 | ResNet 获 ILSVRC 冠军，3.6% top-5 错误率 |
| 何恺明 | 第一作者，后成为"ResNet之父" |
| 突破 | 证明"更深"可以"更好" |
| 影响 | 几乎所有现代视觉模型的基础 |

## 🔗 相关知识

- [[AlexNet]] - ResNet 之前的深度学习起点
- [[VGG]] - 另一个重要的深层网络
- [[Transformer]] - NLP 领域的"ResNet"时刻
- [[ViT]] - Transformer 应用于视觉

---

**向量检索标签**: ResNet, 残差网络, 残差连接, 深度网络, 何恺明, ImageNet, 梯度消失