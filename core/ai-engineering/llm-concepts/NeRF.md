---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["NeRF", "神经辐射场", "3D重建", "体积渲染", "场景重建"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["3D场景重建", "新视角合成", "VR/AR", "自动驾驶"]
related_concepts: ["GAN", "Gaussian Splatting", "3D重建", "体积渲染"]
prerequisites: ["深度学习基础", "体积渲染"]
---

# NeRF — 神经辐射场 3D 场景重建

## 核心定义

**NeRF (Neural Radiance Fields)**：2020年由 Berkeley 提出，通过神经网络隐式表示 3D 场景，用体积渲染从任意视角合成图像，实现高精度 3D 重建和新视角合成。

**核心理念**：用 MLP 学习一个函数，输入 3D 坐标 (x,y,z) 和视角方向 (θ,φ)，输出该点的颜色和密度，从而隐式表示整个 3D 场景。

## 🎯 一句话总结

> **NeRF = MLP(3D坐标, 视角) → 颜色+密度 → 体积渲染合成新视角**

```
输入: 3D位置 (x,y,z) + 视角方向 (θ,φ)
    ↓
MLP 网络
    ↓
输出: 颜色 (RGB) + 密度 (σ)
    ↓
体积渲染 → 合成图像
```

## 🏗️ 核心原理

### 神经辐射场表示

```python
import torch
import torch.nn as nn

class NeRF(nn.Module):
    def __init__(self):
        super().__init__()

        # 位置编码
        self.encode_pos = lambda x: torch.cat([
            torch.sin(π * x * 2**i) for i in range(10)
        ] + [
            torch.cos(π * x * 2**i) for i in range(10)
        ], dim=-1)

        # 密度网络 (预测每点的密度/不透明度)
        self.density_net = nn.Sequential(
            nn.Linear(60, 256),  # 3D坐标 × 20维编码
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 1),  # 输出密度 σ
        )

        # 颜色网络 (预测每点的颜色)
        self.color_net = nn.Sequential(
            nn.Linear(256 + 60, 128),  # 密度特征 + 视角编码
            nn.ReLU(),
            nn.Linear(128, 3),  # RGB 颜色
        )

    def forward(self, x, d):
        """
        x: [B, 3] 3D坐标
        d: [B, 3] 视角方向
        """
        # 位置编码
        x_enc = self.encode_pos(x)
        d_enc = self.encode_pos(d)

        # 预测密度
        h = self.density_net(x_enc)
        sigma = torch.relu(h)

        # 预测颜色
        c = self.color_net(torch.cat([h, d_enc], dim=-1))

        return {'rgb': torch.sigmoid(c), 'sigma': sigma}
```

### 体积渲染

```python
def volume_render(rays, model, num_samples=64):
    """
    rays: [B, 6] 射线原点 + 方向
    返回: [B, 3] 合成颜色
    """
    # 沿着射线采样点
    t = torch.linspace(0, 1, num_samples)
    positions = rays[:, None, :3] + t[None, :, None] * rays[:, None, 3:]

    colors = []
    alphas = []

    for i in range(num_samples):
        pts = positions[:, i]
        dirs = rays[:, 3:]  # 所有射线同方向

        output = model(pts, dirs)
        colors.append(output['rgb'])
        alphas.append(1 - torch.exp(-output['sigma']))

    # 累加渲染
    T = torch.cumprod(torch.stack([1] + alphas[:-1]), dim=0)
    C = torch.sum(T[:, None] * torch.stack(colors) * torch.stack(alphas), dim=0)

    return C
```

## 💼 FDE 应用场景

### 场景: 文物 3D 数字化

**需求**: 高精度数字化珍贵文物，支持远程展示

**方案**: 多角度照片 → NeRF 重建 → 3D 模型

**效果**: 精度达毫米级，支持任意角度查看

### 场景: 自动驾驶仿真

**需求**: 生成多样化驾驶场景用于训练

**方案**: NeRF 重建真实道路场景 → 改变视角/天气/时间

**效果**: 仿真数据补充实车数据，降低数据采集成本

### 场景: 电影特效

**需求**: 从照片生成逼真 3D 场景，替换绿幕

**方案**: NeRF 场景重建 + 虚拟物体融合

**效果**: 降低特效制作成本 40%

## 📊 NeRF 演进

| 模型 | 年份 | 改进 |
|------|------|------|
| NeRF | 2020 | 基础架构 |
| NeRF-W | 2021 | 神经辐射场 + 照明变化 |
| Mip-NeRF | 2021 | 抗锯齿，多尺度 |
| Instant NGP | 2022 | 哈希编码，实时 |
| NeRFStudio | 2022 | 统一框架 |

## ⚠️ 局限性

| 问题 | 描述 | 解决方向 |
|------|------|----------|
| 计算慢 | 单场景需数小时重建 | Instant NGP 加速 |
| 泛化差 | 每个场景单独训练 |RegNeRF 等 |
| 纹理模糊 | 细节不足 | 高分辨率变体 |

## 🔗 相关知识

- [[Gaussian Splatting]] - NeRF 的改进
- [[3D重建]] - 传统方法对比
- [[体积渲染]] - 核心渲染技术

---

**向量检索标签**: NeRF, 神经辐射场, 3D重建, 体积渲染, 新视角合成, 隐式表示