---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["TTS", "语音合成", "Text-to-Speech", "深度学习", "波形生成"]
source: 原创
created_date: 2026-05-20
updated_date: 2026-05-20
implementation_status: production_ready
use_cases: ["语音助手", "外呼机器人", "有声书", "导航播报"]
related_concepts: ["ASR", "NLU", "大模型外呼"]
prerequisites: ["深度学习基础", "GAN", "Transformer"]
---

# TTS — 语音合成

## 核心定义

**TTS (Text-to-Speech)**：将文本转换为自然语音的技术，也称为语音合成 (Speech Synthesis)。

**核心理念**：通过声学模型和声码器 (Vocoder) 的两级建模，或端到端模型，直接将文字转换为可播放的音频波形。

## 🎯 一句话总结

> **TTS = 文本分析 + 声学建模 + 波形生成，核心挑战是自然度、表现力、延迟**

## 📊 技术演进

| 时代 | 方法 | 代表模型 | 特点 |
|------|------|----------|------|
| 传统 | 拼接合成 | 单元拼接 | 音质好但需海量录音 |
| 传统 | 参数合成 | HMM-DNN | 灵活但音质机械 |
| 深度学习 | 神经参数合成 | Tacotron, FastSpeech | 端到端，音质提升 |
| 神经网络声码器 | 自回归 | WaveNet | 极高质量但慢 |
| 神经网络声码器 | 非自回归 | HiFi-GAN, VITS | 高质量+实时 |
| 大模型时代 | Diffusion | Storm, CosyVoice | 极致自然，情感可控 |

## 🏗️ 核心架构

### 两阶段 TTS 架构

```
文本输入 → 文本分析(分词, 韵律) → 梅尔频谱生成(Tacotron/FastSpeech)
                                              ↓
                               波形声码器(HiFi-GAN/VITS)
                                              ↓
                                         音频输出
```

### 一阶段端到端架构

```
文本输入 → [Transformer/ Diffusion] → 音频波形
```

### 主流模型对比

| 模型 | 机构 | 架构 | 特点 |
|------|------|------|------|
| Tacotron 2 | Google | Seq2Seq + WaveNet | 经典架构 |
| FastSpeech 2 | 微软 | 非自回归 + .duration预测 | 低延迟 |
| VITS | - | VAE + Flow + HiFi-GAN | 高质量单模型 |
| HiFi-GAN | 金山 | GAN声码器 | 实时合成 |
| CosyVoice | 阿里 | Transformer + HiFi-GAN | 中文优化，开源 |
| GPT-SoVITS | - | GPT + 声码器 | 少样本克隆 |

## 💼 FDE 应用场景

### 场景: AI外呼机器人

**需求**: 机器人说话自然、有情感、延迟低

**方案**:
- 选择 CosyVoice 或 GPT-SoVITS（中文优化）
- 预录制真人音色用于品牌一致性
- SSML 标记控制停顿、重音、语速

**效果**: MOS评分 > 4.0（5分制），接近真人

### 场景: 有声内容生成

**需求**: 将文章批量转为有声书

**方案**:
- VITS 支持多音色
- 章节结构自动添加停顿

**效果**: 1万字文章5分钟生成有声版本

## ⚠️ 核心挑战

| 挑战 | 描述 | 解决方案 |
|------|------|----------|
| 自然度 | 机械感、语调平板 | 韵律建模 + 情感控制 |
| 延迟 | 流式播放需低延迟 | FastSpeech + 预测性输出 |
| 音色克隆 | 需要少量样本复刻音色 | Few-shot adaptation |
| 多语言 | 中英混说/跨语言 | 多语言联合训练 |
| 实时性 | 对话交互需<300ms | 轻量模型 + 流式解码 |

## 🔗 相关知识

- [[ASR]] - 逆向技术，语音转文本
- [[NLU]] - 合成前的语义理解
- [[大模型外呼]] - ASR+TTS+NLU的整合应用

---

**向量检索标签**: TTS, 语音合成, CosyVoice, HiFi-GAN, VITS, 声码器, 文本转语音