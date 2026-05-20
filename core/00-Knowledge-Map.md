---
type: knowledge-map
category: ["system"]
tags: ["导航", "知识体系", "FDE"]
---

# FDE 知识图谱总览

> Forward Deployed Engineer 专业知识管理系统 - 知识图谱导航中心

## 🗺️ 知识体系架构

```
┌─────────────────────────────────────────────────────────────┐
│                    FDE 能力金字塔                             │
├─────────────────────────────────────────────────────────────┤
│  咨询交付层          客户现场 · 项目交付 · 变革管理         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  产品业务层        产品思维 · 产品设计 · 增长策略     │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  AI工程化层       LLM理论 · Agent · RAG · 评估体系    │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  技术基础层       编程基础 · 系统设计 · 数据库        │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📚 知识领域导航

### 🏗️ 技术基础层 (core/foundation)

| 子目录 | 内容 |
|--------|------|
| `system-design/` | 系统设计知识 |
| `knowledge-management/` | 知识管理方法 |

**核心文件**:
- Clean-Code-代码整洁之道.md
- 设计模式-GoF.md
- 设计数据密集型应用-DDIA.md
- TCP-IP详解.md
- Web安全深度剖析.md
- 高性能MySQL.md

---

### 🤖 AI工程化层 (core/ai-engineering)

| 子目录 | 内容 |
|--------|------|
| `llm-theory/` | LLM理论基础（机器学习、深度学习、统计学习方法） |
| `agent-systems/` | Agent系统与Multi-Agent编排 |
| `prompt-engineering/` | Prompt工程化 |
| `rag-systems/` | RAG架构与实战 |
| `evaluation/` | AI产品评估体系 |

**核心文件**:
- AI Agent概念.md
- LLM基础原理.md
- GPT系列演进.md
- RAG原理与实践.md
- 向量数据库与Embedding.md
- AI产品评估体系.md
- AI安全与对齐.md
- TADI-工具增强的钻井智能系统.md (论文笔记)

---

### 💼 产品业务层 (core/product-business)

| 子目录 | 内容 |
|--------|------|
| `pm-fundamentals/` | 产品经理基础概论 |
| `product-design/` | 产品设计与需求分析 |
| `growth-business/` | 增长与商业策略 |
| `ai-product-methods/` | AI产品方法论（Prompt设计、对话交互等） |

**核心文件**:
- 产品经理概论.md
- 需求分析方法（KANO）.md
- PRD写作入门.md
- 数据驱动决策.md
- 用户画像与场景.md
- 竞品分析框架.md

---

### 🤝 咨询交付层 (core/consulting-delivery)

| 文件 | 内容 |
|------|------|
| 企业AI实施手册.md | 斯坦福实证报告与落地经验 |
| PMBOK项目管理知识体系.md | 项目管理标准方法 |
| 变革之心-Kotter.md | 组织变革管理 |
| 客户成功.md | 客户关系管理 |
| 演说之禅.md | 演示汇报技巧 |
| 财务智慧.md | 财务分析基础 |
| 金字塔原理.md | 逻辑思维与表达 |
| 麦肯锡方法.md | 咨询公司方法论 |

---

## ⚡ 快速操作

### 知识摄入
```bash
# 论文处理（PDF -> 中文模板）
python automation/paper_processor.py

# 网页/文本摄入
python -m automation.web_ingest --paste
python -m automation.web_ingest --url "https://..."
python -m automation.web_ingest --file content.md
```

### 学习与复习
```bash
# 学习路径
python automation/learning_path_generator.py

# 面试准备
python automation/interview_prep.py

# 智能复习
python automation/spaced_repetition.py
```

---

## 📊 当前知识库统计

| 领域 | 文件数 | 说明 |
|------|--------|------|
| 技术基础 | 11 | 编程、系统设计、数据库、安全 |
| AI工程化 | 28 | LLM、Agent、RAG、评估、产品案例 |
| 产品业务 | 31 | PM基础、产品设计、增长、商业 |
| 咨询交付 | 8 | 项目管理、变革管理、沟通技巧 |
| **总计** | **78** | |

---

**知识图谱版本**: 2.0.0
**最后更新**: 2026-05-18
**维护频率**: 每周更新一次