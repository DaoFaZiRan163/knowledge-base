---
type: concept
category: ["ai-engineering", "llm-concepts", "vector-database"]
difficulty: beginner
tags: ["Chroma", "向量数据库", "Embedding", "RAG", "本地存储"]
source: 原创
created_date: 2026-05-23
updated_date: 2026-05-23
implementation_status: production_ready
use_cases: ["RAG原型", "本地开发", "Embedding存储", "快速验证"]
related_concepts: ["向量数据库与Embedding", "RAG原理与实践", "Pinecone-Nexus"]
prerequisites: ["向量基础概念", "Embedding概念"]
---

# Chroma向量数据库

## 核心定义

**Chroma**：开源的轻量级向量数据库，专为AI应用设计，支持存储和检索向量 embedding。

**核心理念**：简单、快速、本地化，让开发者能快速搭建向量检索能力。

## 🎯 一句话总结

> **Chroma = 轻量级向量数据库，适合本地开发和原型验证**

## 为什么需要向量数据库

传统数据库按精确值匹配，向量数据库按语义相似度搜索：

```
传统查询：WHERE name = "张三"
向量查询：找到与"张三"语义最相似的内容

示例：
输入："机器学习" → 向量 [0.12, -0.45, 0.89, ...]
数据库存储所有文本的向量
检索时：找到最接近 [0.12, -0.45, 0.89, ...] 的向量
```

## 🏗️ Chroma 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Chroma 架构                            │
│                                                             │
│  文档 → Embedding模型 → 向量化 → Chroma存储                  │
│                                    ↓                        │
│  查询 → 向量化 → 相似度搜索 → 返回结果                       │
│                                                             │
│  本地持久化：./chroma_db                                     │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 核心特性

### 1. 轻量简单

```python
from chroma import Chroma

# 创建collection
db = Chroma.from_documents(documents, embeddings, persist_directory="./chroma_db")

# 相似度检索
results = db.similarity_search("机器学习")
```

### 2. 本地持久化

```python
persist_directory="./chroma_db"
# 数据存储在本地，随时可用
```

### 3. 支持元数据过滤

```python
results = db.similarity_search(
    query="机器学习",
    where={"source": "文档"}
)
```

### 4. 与LangChain集成

```python
from langchain_community.vectorstores import Chroma

vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
```

## 📊 Chroma vs 其他向量数据库

| 特性 | Chroma | Qdrant | Pinecone |
|------|--------|--------|----------|
| 部署方式 | 本地 | 云/自托管 | 云服务 |
| 规模 | 小中规模 | 大规模 | 大规模 |
| 复杂度 | 极简 | 中等 | 简单（托管） |
| 成本 | 免费开源 | 免费/云 | 付费 |
| 适用场景 | 原型/开发 | 生产环境 | 云端大规模 |
| 延迟 | 低 | 低 | 低 |

## 💼 选型建议

### 选 Chroma 当：

- 本地开发调试
- 初期原型验证
- 小规模数据集（<100万向量）
- 需要快速迭代
- 不想管理云服务

### 选 Qdrant/Pinecone 当：

- 生产环境
- 大规模数据（>100万向量）
- 需要高可用性
- 需要云端托管
- 需要更强的高级功能

## ⚠️ 局限性

| 限制 | 说明 |
|------|------|
| 规模 | 不适合超大规模数据集 |
| 分布式 | 单机为主，分布式支持有限 |
| 高级功能 | 比专业向量数据库功能少 |

## 🔗 相关知识

- [[向量数据库与Embedding]] - 向量数据库基础知识
- [[RAG原理与实践]] - RAG系统构建
- [[Pinecone-Nexus]] - 云端向量数据库

---

**向量检索标签**: Chroma, 向量数据库, Embedding存储, 本地开发, RAG, 向量检索