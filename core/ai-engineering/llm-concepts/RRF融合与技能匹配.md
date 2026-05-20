---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["RRF", "融合排序", "技能匹配", "多路召回", "搜索排序"]
source: 原创
created_date: 2026-05-19
updated_date: 2026-05-19
implementation_status: production_ready
use_cases: ["搜索排序", "RAG融合", "多源检索", "技能路由"]
related_concepts: ["混合检索与召回率", "ReAct", "DSPy"]
prerequisites: ["混合检索与召回率"]
---

# RRF融合与技能匹配

## 核心定义

**RRF (Reciprocal Rank Fusion)**：倒数排名融合，将多个检索结果按排名融合的算法，简单高效，是混合检索的核心技术。

**技能匹配 (Skill Matching)**：在 Agent 系统中，根据任务需求匹配最合适的技能/工具的机制。

**核心理念**：RRF 通过排名而非分数融合结果，避免不同评分体系不可比的问题；技能匹配让 Agent 知道"该用什么工具"。

## 🎯 一句话总结

> **RRF = 多路检索结果的排名融合；技能匹配 = 任务到工具的智能路由**

```
RRF:
搜索A返回 [Doc1, Doc3, Doc5]
搜索B返回 [Doc2, Doc3, Doc1]
         ↓
    RRF融合
         ↓
    最终: [Doc1, Doc3, Doc2, Doc5]

技能匹配:
用户需求 → 分析 → [路由] → 选择最适合的工具
```

## 🏗️ RRF 原理

### RRF 公式

```
RRF_score(d) = Σ 1 / (k + rank_d)

其中:
- d: 文档
- rank_d: 该文档在第i个检索结果中的排名
- k: 融合参数（通常 60）
- Σ: 对所有检索源求和
```

### 示例

```python
# 假设有两个检索结果
results_a = ["doc1", "doc2", "doc3", "doc4"]  # 排名 0,1,2,3
results_b = ["doc3", "doc1", "doc4", "doc2"]  # 排名 0,1,2,3

k = 60

# 计算 RRF 分数
scores = {
    "doc1": 1/(k+0) + 1/(k+1),  # 在A排第0，在B排第1
    "doc2": 1/(k+1) + 1/(k+3),  # 在A排第1，在B排第3
    "doc3": 1/(k+2) + 1/(k+0),  # 在A排第2，在B排第0
    "doc4": 1/(k+3) + 1/(k+2),  # 在A排第3，在B排第2
}

# 最终排序
sorted_docs = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
# 结果: doc3, doc1, doc2, doc4

# 注意: doc3 虽然在A中排第2，但在B中排第0，综合得分最高
```

## 🏗️ 技能匹配原理

### Agent 技能路由

```
用户意图 → 意图分类 → 技能检索 → 技能选择 → 执行

示例:
输入: "帮我写一封道歉邮件给客户"
         ↓
    意图分类: 邮件撰写
         ↓
    技能检索: 找到 [邮件撰写, 商务写作, 模板选择]
         ↓
    技能选择: 根据上下文选择最合适的技能
         ↓
    执行: 调用邮件撰写技能
```

### 技能匹配策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| 精确匹配 | 关键词/标签完全匹配 | 明确意图 |
| 语义匹配 | 向量相似度匹配 | 模糊意图 |
| 多技能组合 | 多个技能串联 | 复杂任务 |
| 回退策略 | 精确匹配失败后语义匹配 | 鲁棒性 |

## 🔧 技术实现

### RRF 融合实现

```python
from collections import defaultdict

def rrf_fusion(result_sets: list, k=60):
    """
    RRF 融合多个检索结果
    result_sets: [[doc1, doc2, ...], [doc3, doc1, ...], ...]
    """
    scores = defaultdict(float)

    for result_set in result_sets:
        for rank, doc in enumerate(result_set):
            # RRF 公式
            scores[doc] += 1 / (k + rank)

    # 按分数排序
    return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
```

### 技能匹配实现

```python
from sklearn.metrics.pairwise import cosine_similarity

class SkillMatcher:
    def __init__(self, skills: list, embeddings):
        """
        skills: [{"name": "邮件撰写", "tags": [...], "description": "..."}]
        embeddings: 预计算的技能向量
        """
        self.skills = skills
        self.embeddings = embeddings

    def match(self, query: str, top_k=3):
        # 1. 向量化用户需求
        query_emb = embed_model.encode(query)

        # 2. 计算与所有技能的相似度
        similarities = cosine_similarity([query_emb], self.embeddings)[0]

        # 3. 返回 top-k
        top_indices = similarities.argsort()[-top_k:][::-1]
        return [(self.skills[i], similarities[i]) for i in top_indices]

    def match_with_fallback(self, query: str, required_tags: list = None):
        # 主要匹配
        matches = self.match(query, top_k=5)

        # 如果指定了必需标签，过滤
        if required_tags:
            filtered = [
                (skill, score) for skill, score in matches
                if any(tag in skill["tags"] for tag in required_tags)
            ]
            if filtered:
                return filtered

        # 回退到基于关键词的匹配
        return self.keyword_match(query, required_tags)

    def keyword_match(self, query: str, required_tags: list = None):
        scores = []
        for skill in self.skills:
            score = 0
            for tag in skill["tags"]:
                if tag in query.lower():
                    score += 1
            if required_tags and not any(rt in skill["tags"] for rt in required_tags):
                score = 0
            scores.append((skill, score))

        return sorted(scores, key=lambda x: x[1], reverse=True)[:3]
```

### RRF + 技能匹配结合

```python
class HybridSkillRetriever:
    """
    结合 RRF 的技能检索器
    """
    def __init__(self, vector_db, skill_matcher):
        self.vector_db = vector_db
        self.skill_matcher = skill_matcher

    def retrieve(self, query: str, k=10):
        # 1. 语义检索
        semantic_results = self.vector_db.search(query, k=k)

        # 2. 关键词检索
        keyword_results = self.keyword_search(query, k=k)

        # 3. 技能匹配
        skill_matches = self.skill_matcher.match(query, k=k)

        # 4. RRF 融合
        all_results = rrf_fusion([
            [r["id"] for r in semantic_results],
            [r["id"] for r in keyword_results],
            [s[0]["id"] for s in skill_matches]
        ], k=60)

        # 5. 获取完整文档
        return [self.get_doc(doc_id) for doc_id in all_results[:k]]
```

## 💼 FDE 应用场景

### 场景 1: 多源文档问答

**需求**: 企业知识库包含 Wiki、文档、邮件，需要统一检索

**方案**:
1. Wiki 向量检索 → 结果A
2. 文档 BM25 检索 → 结果B
3. 邮件关键词检索 → 结果C
4. RRF 融合 → 最终结果

**效果**: 跨源召回率提升 35%

### 场景 2: Agent 技能路由

**需求**: 智能助手根据用户需求自动调用合适工具

**方案**:
1. 用户输入 → 意图识别
2. 技能匹配 → 候选技能排序
3. RRF 融合 → 最终执行计划

**效果**: 技能调用准确率从 70% 提升至 92%

### 场景 3: 搜索结果重排序

**需求**: 初始搜索结果不够精准，需要重排

**方案**:
1. 粗排：向量检索 top 100
2. 精排：交叉编码器重新打分
3. RRF 融合：结合粗排和精排结果

**效果**: NDCG@10 提升 15%

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| RRF k 值选择 | k 过小导致排名权重过高 | 根据数据规模调优，通常 60 |
| 技能匹配冷启动 | 新技能缺少训练数据 | 用规则 + 语义混合 |
| 多技能冲突 | 多个技能都匹配成功 | 优先级 + 互斥规则 |

## 🔗 相关知识

- [[混合检索与召回率]] - RRF 基础
- [[ReAct]] - 技能调用
- [[Agent]] - Agent 技能系统

---

**向量检索标签**: RRF, 融合排序, 技能匹配, 多路召回, 搜索排序, 技能路由