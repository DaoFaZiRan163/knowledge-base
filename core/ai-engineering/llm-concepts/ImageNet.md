---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: beginner
tags: ["ImageNet", "数据集", "ILSVRC", "ImageNet竞赛", "计算机视觉"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["计算机视觉基准", "深度学习训练", "模型评估"]
related_concepts: ["AlexNet", "ResNet", "VGG", "数据集"]
prerequisites: []
---

# ImageNet — 计算机视觉的"北极星"

## 核心定义

**ImageNet**：由李飞飞团队于2009年发布的大规模图像数据集，包含约1400万张标注图像，涵盖2万多个类别。

**ILSVRC**：ImageNet Large Scale Visual Recognition Challenge，2010-2017年每年举办的图像分类竞赛，是深度学习发展的催化剂。

**核心理念**：构建大规模多样化的数据集，让机器学习模型能够"看到"真实世界的多样性。

## 🎯 一句话总结

> **ImageNet = 1400万张标注图像 + 年度竞赛，深度学习革命的燃料**

```
ImageNet 规模:
├── 14,197,122 张图像
├── 21,841 个synset (语义类别)
├── 约 1000 类 ILSVRC 子集
└── 每张图像人工标注类别
```

## 🏗️ 数据集结构

### ImageNet 层级

```
ImageNet
├── 引导词 (anchor word)
│   └── 下位词 (hyponym)
│       └── 示例图像 (images)
│
示例:
motor vehicle (机动车辆)
├── car (汽车)
│   ├── [红汽车图像]
│   ├── [蓝汽车图像]
│   └── ...
├── truck (卡车)
├── bus (公交车)
└── ...
```

### ILSVRC 竞赛任务

| 年份 | 冠军模型 | Top-5 错误率 | 标志性突破 |
|------|----------|--------------|------------|
| 2010 | NEC | 28% | 传统方法主导 |
| 2011 | ISI | 26% | 传统方法巅峰 |
| **2012** | **AlexNet** | **15.3%** | **深度学习开启** |
| 2013 | ZF Net | 11.2% | CNN 深化 |
| 2014 | VGG/GoogLeNet | 7.3% | 网络更深 |
| 2015 | ResNet | 3.6% | 残差连接 |
| 2016-17 | 深度模型集成 | < 3% | 接近人类水平 |

## 💼 FDE 应用场景

### 场景: 预训练模型选择

**需求**: 选择计算机视觉任务的预训练模型

**方案**: 在 ImageNet 上预训练的模型具有通用特征提取能力

**效果**: 迁移学习到医疗、制造、农业等垂直领域，减少数据需求

### 常用预训练模型对比

| 模型 | ImageNet Top-1 | 参数量 | 推理速度 |
|------|----------------|--------|----------|
| ResNet-50 | 76.1% | 25M | 快 |
| VGG-16 | 71.5% | 138M | 慢 |
| EfficientNet-B0 | 77.1% | 5.3M | 快 |
| ViT-B/16 | 79.7% | 86M | 中 |

## 📊 历史意义

| 里程碑 | 说明 |
|--------|------|
| 2009 | ImageNet 论文发表 |
| 2010-2017 | ILSVRC 年度竞赛 |
| 2012 | AlexNet 突破引发深度学习热潮 |
| 2017 | 竞赛终结，人类水平已超越 |

**核心启示**:
- 大数据是深度学习的根基
- 标准化 Benchmark 推动领域进步
- 竞赛机制加速技术迭代

## 🔗 相关知识

- [[AlexNet]] - 2012年ImageNet夺冠，开启深度学习时代
- [[ResNet]] - 2015年ILSVRC冠军
- [[ViT]] - Transformer在图像分类的应用

---

**向量检索标签**: ImageNet, 数据集, ILSVRC, 计算机视觉, 深度学习基准, 李飞飞