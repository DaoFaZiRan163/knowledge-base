---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: beginner
tags: ["LeNet", "CNN", "卷积神经网络", "深度学习", "早期神经网络"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["图像分类", "手写识别", "CNN基础", "深度学习入门"]
related_concepts: ["AlexNet", "ResNet", "ImageNet", "CNN"]
prerequisites: []
---

# LeNet — 手写数字识别的经典CNN

## 核心定义

**LeNet** (LeNet-5)：1998年由 Yann LeCun 等人提出的卷积神经网络，是第一个成功商用的深度学习模型，主要用于手写数字识别（MNIST数据集）。

**核心理念**：通过卷积层提取特征 + 池化层降维 + 全连接层分类的端到端学习。

## 🎯 一句话总结

> **LeNet = 7层CNN结构，奠定了现代卷积神经网络的基础架构**

```
输入(32x32) → Conv(6) → Pool → Conv(16) → Pool → FC(120) → FC(84) → 输出(10)
```

## 🏗️ 架构详解

### LeNet-5 结构

| 层 | 输出尺寸 | 参数量 | 功能 |
|------|----------|--------|------|
| Input | 32×32×1 | - | 灰度图像 |
| Conv1 | 28×28×6 | 156 | 5×5卷积，6通道 |
| Pool1 | 14×14×6 | - | 2×2最大池化 |
| Conv2 | 10×10×16 | 2,416 | 5×5卷积，16通道 |
| Pool2 | 5×5×16 | - | 2×2最大池化 |
| FC1 | 120 | 48,120 | 全连接 |
| FC2 | 84 | 10,164 | 全连接 |
| Output | 10 | 840 | 分类输出 |

### 核心创新

1. **局部感受野**: 每个卷积核只连接局部区域，模拟视觉皮层
2. **权值共享**: 同一通道共享卷积核权重，减少参数量
3. **空间下采样**: 池化层提取主要特征同时降维
4. **端到端训练**: 反向传播优化整个网络

## 🔧 技术实现

```python
# LeNet-5 PyTorch 实现
import torch.nn as nn

class LeNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 6, 5)      # 32x32 → 28x28
        self.pool1 = nn.MaxPool2d(2)        # 28x28 → 14x14
        self.conv2 = nn.Conv2d(6, 16, 5)    # 14x14 → 10x10
        self.pool2 = nn.MaxPool2d(2)        # 10x10 → 5x5
        self.fc1 = nn.Linear(16*5*5, 120)   # 400 → 120
        self.fc2 = nn.Linear(120, 84)      # 120 → 84
        self.fc3 = nn.Linear(84, 10)       # 84 → 10

    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = self.pool1(x)
        x = torch.relu(self.conv2(x))
        x = self.pool2(x)
        x = x.view(-1, 16*5*5)
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x
```

## 💼 FDE 应用场景

### 场景: 文档数字化

**需求**: 识别手写表单、发票上的数字

**方案**: 基于 LeNet 改进的 CNN 用于光学字符识别（OCR）

**效果**: 银行支票识别准确率 99%+，成为早期深度学习商业化典范

## 📊 历史意义

| 里程碑 | 说明 |
|--------|------|
| 1998 | LeNet-5 提出 |
| 1989 | 早期版本（LeNet-1）诞生 |
| 奠定了 | CNN 的三大核心：卷积、池化、全连接 |
| 影响 | AlexNet、VGG、ResNet 的直接祖先 |

## 🔗 相关知识

- [[AlexNet]] - 深度学习复兴的标志性模型
- [[ResNet]] - 残差连接解决梯度消失
- [[ImageNet]] - 推动 CNN 发展的数据集

---

**向量检索标签**: LeNet, CNN, 卷积神经网络, 手写识别, MNIST, 深度学习先驱