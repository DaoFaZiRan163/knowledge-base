---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["GAN", "生成对抗网络", "生成模型", "对抗训练", "Goodfellow"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["图像生成", "图像修复", "风格迁移", "数据增强"]
related_concepts: ["Diffusion", "NeRF", "图像生成", "博弈论"]
prerequisites: ["深度学习基础"]
---

# GAN — 生成对抗网络

## 核心定义

**GAN (Generative Adversarial Network)**：2014年由 Ian Goodfellow 等人提出的生成模型框架，通过"生成器"与"判别器"的对抗训练实现高质量数据生成。

**核心理念**：生成器 G 造假，判别器 D 鉴伪，两者对抗提升，直到 D 无法区分真假。

## 🎯 一句话总结

> **GAN = 生成器 G（造假）+ 判别器 D（鉴伪）+ 对抗训练 = 以假乱真**

```
噪声 z → Generator → 生成图像 G(z)
                 ↓
真实图像 x → Discriminator → 判别结果 (真/假)
                 ↑
生成图像 G(z) ↙

对抗损失: min_G max_D E[log D(x) + log(1-D(G(z)))]
```

## 🏗️ GAN 架构

### 对抗训练流程

```python
import torch
import torch.nn as nn

class Generator(nn.Module):
    """生成器: 噪声 → 图像"""
    def __init__(self, latent_dim, img_shape):
        super().__init__()
        self.img_shape = img_shape

        self.model = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.LeakyReLU(0.2),
            nn.Linear(128, 256),
            nn.BatchNorm1d(256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, 512),
            nn.BatchNorm1d(512),
            nn.LeakyReLU(0.2),
            nn.Linear(512, int(torch.prod(torch.tensor(img_shape)))),
            nn.Tanh()
        )

    def forward(self, z):
        img = self.model(z)
        return img.view(z.size(0), *self.img_shape)


class Discriminator(nn.Module):
    """判别器: 图像 → 真/假"""
    def __init__(self, img_shape):
        super().__init__()

        self.model = nn.Sequential(
            nn.Linear(int(torch.prod(torch.tensor(img_shape))), 512),
            nn.LeakyReLU(0.2),
            nn.Linear(512, 256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def forward(self, img):
        img_flat = img.view(img.size(0), -1)
        return self.model(img_flat)


# 训练循环
def train_gan(generator, discriminator, dataloader, epochs):
    criterion = nn.BCELoss()
    optimizer_g = torch.optim.Adam(generator.parameters(), lr=0.0002)
    optimizer_d = torch.optim.Adam(discriminator.parameters(), lr=0.0002)

    for epoch in range(epochs):
        for real_imgs, _ in dataloader:
            batch_size = real_imgs.size(0)

            # 真实图像标签 = 1
            real_labels = torch.ones(batch_size, 1)
            # 生成图像标签 = 0
            fake_labels = torch.zeros(batch_size, 1)

            # 训练判别器
            noise = torch.randn(batch_size, latent_dim)
            fake_imgs = generator(noise)

            d_real = discriminator(real_imgs)
            d_fake = discriminator(fake_imgs.detach())

            loss_d = criterion(d_real, real_labels) + criterion(d_fake, fake_labels)
            optimizer_d.zero_grad()
            loss_d.backward()
            optimizer_d.step()

            # 训练生成器
            noise = torch.randn(batch_size, latent_dim)
            fake_imgs = generator(noise)
            d_fake = discriminator(fake_imgs)

            # 生成器希望骗过判别器（标签=1）
            loss_g = criterion(d_fake, real_labels)
            optimizer_g.zero_grad()
            loss_g.backward()
            optimizer_g.step()
```

## 💼 FDE 应用场景

### 场景: 产品图像生成

**需求**: 电商平台需要大量商品展示图

**方案**: GAN 生成不同角度/背景的商品图

**效果**: 降低拍摄成本 60%，支持个性化场景

### 场景: 人像处理

**需求**: 美颜、换脸、年龄变化

**方案**: StyleGAN、StarGAN 等变体

**效果**: FaceApp、Deepfake 等应用

### 场景: 数据增强

**需求**: 医疗影像数据不足

**方案**: GAN 生成稀缺病历图像

**效果**: 小样本分类准确率提升 20%

## 📊 GAN 家族

| 模型 | 年份 | 特点 |
|------|------|------|
| DCGAN | 2015 | 深度卷积 GAN，稳定训练 |
| WGAN | 2017 | Wasserstein 距离，解决模式崩溃 |
| StyleGAN | 2018 | 风格控制，高质量人脸 |
| BigGAN | 2019 | 大规模，高保真 |
| StyleGAN3 | 2021 | 解决 aliasing 问题 |
| Diffusion | 2020+ | GAN 的替代者，更稳定 |

## ⚠️ 训练问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 模式崩溃 | 生成器只产生少数模式 | WGAN, MINIST |
| 训练不稳定 | 对抗目标难以平衡 | 谱归一化，多个 D |
| 评估困难 | 无完美指标 | FID, IS 等指标 |

## 🔗 相关知识

- [[Diffusion]] - GAN 的竞争对手
- [[NeRF]] - 3D 场景生成
- [[图像生成]] - 生成模型综述

---

**向量检索标签**: GAN, 生成对抗网络, 生成模型, 对抗训练, Ian Goodfellow, 图像生成