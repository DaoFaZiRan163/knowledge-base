---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["R-CNN", "目标检测", "Region Proposal", "CNN", "计算机视觉"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["目标检测", "目标识别", "场景理解", "自动驾驶感知"]
related_concepts: ["ResNet", "Fast R-CNN", "Faster R-CNN", "YOLO"]
prerequisites: ["CNN基础"]
---

# R-CNN — 区域提议与深度学习的结合

## 核心定义

**R-CNN (Regions with CNN features)**：2014年由 Ross Girshick 等人提出，将 CNN 用于目标检测的开山之作，首次将深度学习成功应用于目标检测任务。

**核心理念**：先用区域提议方法（Selective Search）生成候选区域，再用 CNN 对每个区域提取特征并分类，实现"先找再认"的两阶段检测。

## 🎯 一句话总结

> **R-CNN = 选择性搜索找候选框 + CNN 提特征 + SVM 分类，检测精度大幅提升**

```
图像 → Selective Search (~2000区域) → 统一缩放 → CNN提特征 → SVM分类 + 边界回归
```

## 🏗️ R-CNN 流程

### 四步检测流程

```
┌─────────────────────────────────────────────────────────────┐
│                    R-CNN 检测流程                            │
│                                                             │
│  1. 区域提议 (Region Proposal)                               │
│     输入图像 → Selective Search → ~2000 个候选区域           │
│                                                             │
│  2. 特征提取 (Feature Extraction)                           │
│     每个区域 → 统一缩放到 227×227 → CNN (AlexNet) → 4096维   │
│                                                             │
│  3. 分类 (Classification)                                  │
│     特征向量 → SVM分类器 → 每个类别的置信度                  │
│                                                             │
│  4. 边界回归 (Bounding Box Regression)                       │
│     微调候选框位置 → 更精确的检测结果                        │
└─────────────────────────────────────────────────────────────┘
```

### 核心问题与解决

| 问题 | R-CNN 解决方案 |
|------|---------------|
| 候选框数量多 | CNN 共享特征，独立处理每个区域 |
| 候选框尺寸不一 | 统一缩放到 227×227（warp 或 crop）|
| 训练数据稀缺 | ImageNet 预训练 + Pascal VOC 微调 |

## 🔧 技术实现

```python
# R-CNN 核心步骤
import torchvision
from selective_search import selective_search

# 1. Selective Search 生成候选区域
boxes, _ = selective_search(image, mode='fast')

# 2. 特征提取
transform = transforms.Compose([
    transforms.Resize((227, 227)),
    transforms.ToTensor(),
])

cnn = torchvision.models.alexnet(pretrained=True)
features = []

for box in boxes[:2000]:  # 最多2000个区域
    roi = image[box['y']:box['y']+box['h'], box['x']:box['x']+box['w']]
    roi_tensor = transform(roi)
    feature = cnn(roi_tensor.unsqueeze(0))  # CNN前向
    features.append(feature)

# 3. SVM 分类 (每个类别一个分类器)
for cls in classes:
    svm_classifier[cls].predict(features)

# 4. 边界回归精调
bbox_regressor[cls].predict(features[cls > threshold])
```

## 💼 FDE 应用场景

### 场景: 自动驾驶障碍物检测

**需求**: 实时检测车辆、行人、交通标志

**方案**: R-CNN 家族（Fast/Faster R-CNN）用于感知层

**效果**: 目标检测 mAP 从 30% 提升至 70%+，支撑自动驾驶安全

### 场景: 工业缺陷检测

**需求**: 在生产线检测产品表面缺陷

**方案**: R-CNN 检测缺陷区域 + 分类判断类型

**效果**: 缺陷检出率 98%，减少人工质检成本

## 📊 R-CNN 家族演进

| 模型 | 年份 | mAP (VOC) | 创新点 |
|------|------|-----------|--------|
| R-CNN | 2014 | 53.7% | 两阶段开山之作，慢（~50s/img）|
| Fast R-CNN | 2015 | 70.0% | ROI Pooling 共享特征，快 |
| Faster R-CNN | 2015 | 78.8% | RPN 替代 SS，GPU可跑 |
| Mask R-CNN | 2017 | - | 实例分割，ROI Align |

## ⚠️ R-CNN 的问题

| 问题 | 描述 | 后续改进 |
|------|------|----------|
| 慢 | ~50秒/图，无法实时 | Fast/Faster R-CNN |
| 多阶段训练 | SS→CNN→SVM→BB，繁琐 | 端到端 |
| 候选框固定 | SS 无法学习 | RPN 可学习 |

## 🔗 相关知识

- [[ResNet]] - 特征提取网络
- [[YOLO]] - 单阶段检测器，实时性更好
- [[目标检测]] - 综述

---

**向量检索标签**: R-CNN, 目标检测, Region Proposal, Selective Search, CNN, Ross Girshick