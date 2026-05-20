# FDE Knowledge Hub — Forward Deployed Engineer 知识管理系统

> 一个面向 FDE（Forward Deployed Engineer）角色的工程化知识管理系统，整合 Obsidian + NotebookLM + AI 能力，支持智能学习、知识检索、面试准备与能力评估。

**核心定位**：将碎片化技术知识转化为系统化的 FDE 能力体系，为寻找 FDE 工程师岗位提供扎实的技术与业务知识储备。

---

## 🎯 这个项目做什么？

| 功能 | 说明 |
|------|------|
| **AI 对话学习** | 基于本地知识库的递归式补洞学习器，AI陪你深度理解概念 |
| **知识摄入** | 网页/文本/文件 → 结构化笔记（支持 ASR/TTS/NLU/外呼等主题） |
| **学习路径** | 根据目标岗位要求生成个性化学习路径 |
| **面试准备** | AI 基于知识库动态生成 FDE 相关面试题 |
| **间隔复习** | Spaced Repetition 算法驱动，遗忘曲线优化记忆 |
| **知识评估** | 真实理解 vs 死记硬背测试题，检验掌握程度 |

---

## 🗂️ 知识体系结构

```
FDE Knowledge Hub/
├── core/                          # 核心知识库
│   ├── foundation/                # 技术基础层
│   │   ├── system-design/         # 系统设计（电商、CQRS、高并发）
│   │   ├── knowledge-management/  # 知识管理方法论
│   │   └── ...                    # Clean-Code、设计模式、数据库、网络安全
│   │
│   ├── ai-engineering/            # AI 工程化层 ⭐
│   │   ├── llm-concepts/          # LLM核心概念（Transformer、BERT、RAG、Agent...）
│   │   ├── llm-theory/            # LLM理论基础（CS224N、机器学习、深度学习）
│   │   ├── agent-systems/         # Agent系统与Multi-Agent编排
│   │   ├── rag-systems/           # RAG架构与实战
│   │   ├── prompt-engineering/    # Prompt工程化
│   │   └── evaluation/            # AI产品评估体系
│   │
│   ├── product-business/          # 产品业务层
│   │   ├── pm-fundamentals/       # 产品经理基础
│   │   ├── product-design/         # 产品设计方法
│   │   └── growth-business/       # 增长与商业策略
│   │
│   └── consulting-delivery/       # 咨询交付层
│       └── ...                    # PMBOK、变革管理、麦肯锡方法、金字塔原理
│
├── templates/                     # 笔记模板
│   ├── concepts/                  # 概念笔记模板
│   ├── books/                    # 书籍笔记模板
│   ├── review_notes/             # 复习笔记
│   └── learning_paths/           # 学习路径模板
│
├── automation/                    # 自动化工具
│   ├── gap_filling.py            # 递归式补洞学习器
│   ├── learning_path_generator.py # 学习路径生成
│   ├── interview_prep.py        # 面试准备
│   ├── spaced_repetition.py      # 间隔复习
│   ├── knowledge_ingestion.py    # 知识摄入
│   ├── web_ingest.py            # 网页/文本摄入
│   ├── cli.py                   # 统一命令行工具
│   └── paper_processor.py       # 论文处理
│
└── integration/                   # 外部集成
    └── obsidian_notebooklm_sync.py  # Obsidian ↔ NotebookLM 同步
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/FDE-Knowledge-Hub.git
cd FDE-Knowledge-Hub

# 安装依赖
pip install -r requirements.txt

# 复制配置模板
cp .env.example .env
# 编辑 .env 填入你的 API 密钥（见下方说明）
```

### 2. 配置 API 密钥

编辑 `.env` 文件（**此文件不会被提交到 GitHub**）：

```bash
# SiliconFlow（Embedding 推荐，国内可用）
SILICONFLOW_API_KEY=your_siliconflow_api_key_here

# MiniMax（对话模型，国内可直连）
MINIMAX_API_KEY=your_minimax_api_key_here

# 或使用 OpenAI / Anthropic
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

> **注意**：
> - `.env` 和 `.env.local` 已在 `.gitignore` 中排除，不会被提交
> - 如需更换设备，从 `.env.example` 重新复制模板即可

### 3. Obsidian 配置（可选）

```bash
# 1. 下载 Obsidian: https://obsidian.md/download
# 2. 打开 Obsidian → "打开文件夹作为仓库" → 选择本项目目录
# 3. 安装推荐插件：Self-hosted Search（本地搜索）、Templater（模板）
```

---

## 📚 知识体系全景

### FDE 能力金字塔

```
         咨询交付层
        ┌─────────────┐
        │ 项目管理    │
        │ 变革管理    │
        │ 客户沟通    │
        └─────────────┘
         产品业务层
        ┌─────────────┐
        │ 产品思维    │
        │ 增长策略    │
        │ 数据分析    │
        └─────────────┘
         AI工程化层 ⭐
        ┌─────────────┐
        │ LLM/RAG/Agent│
        │ 评估体系    │
        │ AI产品成本  │
        └─────────────┘
         技术基础层
        ┌─────────────┐
        │ 系统设计    │
        │ 数据库      │
        │ 网络安全    │
        └─────────────┘
```

### 核心主题

| 主题 | 覆盖内容 | 文件数 |
|------|----------|--------|
| **LLM核心概念** | Transformer、BERT、GPT、RAG、Agent、幻觉解决、Benchmark | 28+ |
| **外呼与语音AI** | ASR、TTS、NLU、AI外呼、大模型外呼 | 5 |
| **系统设计** | 高并发、电商架构、CQRS、DDIA | 5+ |
| **咨询交付** | PMBOK、变革管理、金字塔原理 | 8 |
| **产品业务** | PM基础、产品设计、增长策略 | 15+ |

---

## 🔧 CLI 工具使用

```bash
# 查看所有命令
python -m automation.cli --help

# AI 对话学习（推荐入门方式）
python automation/gap_filling.py

# 生成学习路径
python -m automation.cli path --topic "RAG系统" --hours 20

# 面试准备
python -m automation.cli interview --role FDE --count 10

# 智能复习
python -m automation.cli review --review-type adaptive

# 网页内容摄入
python -m automation.cli web --paste
python -m automation.cli web --url "https://example.com/article"

# 知识库统计
python -m automation.cli status
```

---

## 📊 笔记格式标准

所有 `core/` 下的笔记统一采用标准格式：

```yaml
---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["RAG", "检索增强", "向量数据库"]
source: 原创
created_date: 2026-05-20
implementation_status: production_ready
use_cases: ["知识问答", "客服机器人", "外呼系统"]
related_concepts: ["ASR", "TTS", "NLU"]
prerequisites: ["LLM基础原理"]
---

# 标题 — 概念名称

## 核心定义
**概念**：一句话定义

## 🎯 一句话总结
> 一句话核心理解

## 📊 技术对比表格

## 🏗️ 架构图/代码示例

## 💼 FDE 应用场景

## ⚠️ 常见问题与挑战

## 🔗 相关知识
- [[关联概念1]]
- [[关联概念2]]
```

---

## 🤝 贡献指南

欢迎补充知识笔记和改进学习工具！

```bash
# 1. Fork 项目
# 2. 创建特性分支
git checkout -b feature/new-concept

# 3. 添加笔记（参考上方格式）
# 4. 提交
git commit -m 'Add: new concept note for XXX'

# 5. 推送并创建 PR
git push origin feature/new-concept
```

---

## ⚙️ 配置说明

| 文件 | 用途 | 是否提交 |
|------|------|----------|
| `.env` | API密钥配置 | ❌ 不提交（已在.gitignore） |
| `.env.example` | 配置模板 | ✅ 提交 |
| `.gitignore` | 排除规则 | ✅ 提交 |
| `requirements.txt` | Python依赖 | ✅ 提交 |
| `vendor/` | Qdrant等外部依赖 | ❌ 不提交（pip install覆盖） |

---

## 📖 相关资源

| 资源 | 链接 |
|------|------|
| Obsidian | https://obsidian.md/ |
| NotebookLM | https://notebooklm.google.com/ |
| SiliconFlow | https://cloud.siliconflow.cn/ |
| MiniMax API | https://www.minimaxi.com/ |

---

**项目目标**：帮助技术从业者系统化掌握 FDE 核心能力，成功获得 FDE 工程师岗位。

**最后更新**：2026-05-20