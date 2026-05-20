---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["Gaussian Splatting", "高斯泼溅", "3D重建", "实时渲染", "显式表示"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["3D渲染", "实时重建", "VR/AR", "自动驾驶仿真"]
related_concepts: ["NeRF", "3D重建", "体积渲染", "神经渲染"]
prerequisites: ["3D基础", "渲染基础"]
---

# Gaussian Splatting — 实时 3D 可微渲染

## 核心定义

**Gaussian Splatting (3D Gaussian Splatting)**：2023年提出的 3D 场景表示方法，用数百万个 3D 高斯函数表示场景，通过"泼溅"（splatting）实现实时可微渲染，速度比 NeRF 快 100 倍。

**核心理念**：用**显式的** 3D 高斯椭球代替 NeRF 的隐式场，每个高斯包含位置、协方差、颜色，通过泼溅到 2D 图像平面实现快速渲染。

## 🎯 一句话总结

> **Gaussian Splatting = 3D 高斯集合 + 泼溅渲染 = 实时 3D 重建（比 NeRF 快 100x）**

```
输入: 多视角图像
    ↓
3D 高斯初始化 (通过 SfM 点云)
    ↓
高斯优化 (位置、协方差、不透明度、颜色)
    ↓
泼溅渲染 → 任意视角图像

速度: 1080p 实时 (~30 FPS)
```

## 🏗️ 核心原理

### 3D 高斯表示

```python
import torch
import torch.nn as nn

class Gaussian3D:
    """单个 3D 高斯"""
    def __init__(self, mean, covariance, color, opacity):
        self.mean = mean  # [3] 中心位置 (x,y,z)
        self.covariance = covariance  # [3,3] 协方差矩阵
        self.color = color  # [3] RGB
        self.opacity = opacity  # scalar 不透明度

    def cov_to_scale_rotation(self):
        """
        协方差矩阵分解为 scale 和 rotation
        用于可学习优化
        """
        # SVD 分解: Cov = R S S^T R^T
        # 返回 scale (3,) 和 rotation (四元数)
        pass

class GaussianModel:
    """3D 高斯场景模型"""
    def __init__(self):
        self.gaussians = []  # 数百万个高斯

    def initialize_from_sfm(self, points, colors):
        """从 SfM 点云初始化"""
        for pt, color in zip(points, colors):
            # 创建高斯，初始协方差与点密度相关
            gaussian = Gaussian3D(
                mean=pt,
                covariance=self.estimate_covariance(pt),
                color=color,
                opacity=1.0
            )
            self.gaussians.append(gaussian)
```

### 泼溅渲染 (Splatting)

```python
def gaussian_splatting_2D(gaussian, view_matrix, proj_matrix, width, height):
    """
    将 3D 高斯泼溅到 2D 图像平面
    """
    # 变换高斯中心到屏幕坐标
    center_cam = view_matrix @ gaussian.mean
    center_clip = proj_matrix @ center_cam

    # 2D 屏幕坐标
    center_2D = center_clip[:2] / center_clip[3]

    # 变换协方差矩阵
    # Cov' = J W Cov W^T J^T
    # J: 投影雅可比, W: 视图变换

    # 计算 2D 协方差 (椭圆参数)
    cov_2D = compute_2D_covariance(gaussian.covariance, view_matrix, proj_matrix)

    # 高斯权重衰减
    alpha = gaussian.opacity * gaussian_2D_weight(center_2D, cov_2D, pixel_pos)

    return color * alpha, alpha


def render_image(gaussians, view_matrix, proj_matrix, width, height):
    """
    渲染完整图像
    """
    color_accum = torch.zeros((height, width, 3))
    alpha_accum = torch.zeros((height, width, 1))

    for gaussian in gaussians:
        # 对每个高斯计算 2D 投影
        color, alpha = gaussian_splatting_2D(
            gaussian, view_matrix, proj_matrix, width, height
        )

        # 按深度排序后累加 (从近到远或从远到近)
        color_accum += color * (1 - alpha_accum)
        alpha_accum += alpha * (1 - alpha_accum)

    return color_accum
```

## 💼 FDE 应用场景

### 场景: 自动驾驶实时感知重建

**需求**: 实时重建道路场景用于仿真

**方案**: Gaussian Splatting 快速 3D 重建

**效果**: 实时 30 FPS，支撑高带宽仿真数据生成

### 场景: 电商 3D 商品展示

**需求**: 手机扫描商品生成 3D 模型

**方案**: Gaussian Splatting 移动端扫描重建

**效果**: 扫描到 3D 模型 < 1 分钟，消费级设备可用

### 场景: 虚拟现实 (VR)

**需求**: 实时渲染真实场景的 3D 表示

**方案**: Gaussian Splatting + VR 头显

**效果**: 低延迟沉浸式体验

## 📊 Gaussian Splatting vs NeRF

| 维度 | Gaussian Splatting | NeRF |
|------|---------------------|------|
| 表示方式 | 显式（高斯集合）| 隐式（MLP）|
| 渲染速度 | 实时 (~30 FPS) | 慢 (数秒/帧) |
| 优化速度 | 30 分钟 | 数小时 |
| 内存占用 | 高 (数百万高斯) | 中 (MLP 参数) |
| 质量 | 相当或更好 | 良好 |
| 泛化能力 | 单场景 | 单场景 |

## 🔧 优化流程

```python
def train_gaussian_splatting(images, cameras, num_iters=30000):
    """
    训练 3D Gaussian Splatting
    """
    # 1. 从 SfM 初始化高斯
    gaussians = initialize_from_sfm(cameras)

    optimizer = torch.optim.Adam(gaussians.parameters(), lr=0.001)

    for i in range(num_iters):
        # 随机选择相机视角
        cam = random.choice(cameras)

        # 渲染
        render = render_cuda(gaussians, cam)

        # 计算损失
        loss = mse_loss(render, images[cam])

        # 反向传播 + densification (密集化)
        loss.backward()
        optimizer.step()

        # 定期 densify: 分裂过多高斯，移除有问题的高斯
        if i % 100 == 0:
            densify_and_prune(gaussians)
```

## 🔗 相关知识

- [[NeRF]] - Gaussian Splatting 的前辈
- [[3D重建]] - 场景重建综述
- [[实时渲染]] - 渲染技术

---

**向量检索标签**: Gaussian Splatting, 高斯泼溅, 3D重建, 实时渲染, 可微渲染, 神经渲染