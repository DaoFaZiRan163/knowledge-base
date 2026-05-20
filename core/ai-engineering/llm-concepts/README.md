# LLM Concepts - 大模型核心概念库

> 本目录收录大语言模型相关的核心概念，采用卡片式设计，支持向量检索和知识图谱链接。

## 📁 目录结构

```
llm-concepts/
├── README.md              # 本目录索引
├── DSPy-声明式LLM编程框架.md  # ✅ 已创建
└── ...                    # 待扩展概念
```

## ✅ 已收录概念

### LLM 工程化 (17个)
| 概念 | 标签 | 难度 | 状态 |
|------|------|------|------|
| [[DSPy-声明式LLM编程框架]] | DSPy, prompt优化, auto-prompt | intermediate | ✅ |
| [[CoT-思维链提示]] | CoT, 思维链, 推理 | intermediate | ✅ |
| [[Self-Consistency-自洽性提示]] | 自洽性, 推理验证, 投票机制 | intermediate | ✅ |
| [[Self-Refine-自我优化]] | 自我优化, 迭代优化, 反馈机制 | intermediate | ✅ |
| [[LangChain与LangGraph对比]] | LangChain, LangGraph, 工作流编排 | intermediate | ✅ |
| [[KV缓存与前缀缓存]] | KV-Cache, 推理优化, 上下文复用 | intermediate | ✅ |
| [[混合检索与召回率]] | 混合检索, RRF, BM25, 重排序 | intermediate | ✅ |
| [[模型微调与强化学习]] | 微调, RLHF, SFT, DPO | expert | ✅ |
| [[SFT与DPO]] | SFT, DPO, 监督微调 | intermediate | ✅ |
| [[数据清洗与评测集]] | 数据清洗, Benchmark, LLM评估 | intermediate | ✅ |
| [[并发熔断与容灾降级]] | 熔断, 限流, 高可用, 容灾 | intermediate | ✅ |
| [[ReAct与HyDE]] | ReAct, HyDE, 推理增强, 检索增强 | intermediate | ✅ |
| [[HITL与JobQueue]] | HITL, 人机协作, 异步任务 | intermediate | ✅ |
| [[MCP协议与配额预占]] | MCP, 配额, 资源管理, 成本控制 | intermediate | ✅ |
| [[输出Guardrail与成本监控]] | Guardrail, 内容安全, 成本监控 | intermediate | ✅ |
| [[Langfuse与可观测]] | Langfuse, 可观测, LLM监控 | intermediate | ✅ |
| [[RRF融合与技能匹配]] | RRF, 融合排序, 技能匹配 | intermediate | ✅ |

### AI 关键突破 (14个)
| 概念 | 标签 | 难度 | 状态 |
|------|------|------|------|
| [[LeNet]] | CNN, 卷积神经网络, 手写识别 | beginner | ✅ |
| [[AlexNet]] | ImageNet, 深度学习复兴, CNN | beginner | ✅ |
| [[ImageNet]] | 数据集, ILSVRC, 计算机视觉基准 | beginner | ✅ |
| [[ResNet]] | 残差网络, 残差连接, 深层网络 | intermediate | ✅ |
| [[R-CNN目标检测]] | 目标检测, Region Proposal, CNN | intermediate | ✅ |
| [[Transformer]] | 注意力机制, 自注意力, 序列建模 | intermediate | ✅ |
| [[Attention is All You Need]] | Transformer原论文, 注意力机制 | intermediate | ✅ |
| [[BERT]] | 预训练语言模型, 双向理解, 遮盖语言模型 | intermediate | ✅ |
| [[GPT-3]] | 1750亿参数, few-shot, 大语言模型 | intermediate | ✅ |
| [[CLIP]] | 多模态, 图文对齐, 对比学习 | intermediate | ✅ |
| [[ViT]] | Vision Transformer, 视觉Transformer | intermediate | ✅ |
| [[GAN]] | 生成对抗网络, 生成模型, 对抗训练 | intermediate | ✅ |
| [[NeRF]] | 神经辐射场, 3D重建, 体积渲染 | intermediate | ✅ |
| [[Gaussian Splatting]] | 高斯泼溅, 3D渲染, 实时重建 | intermediate | ✅ |

## 🎯 设计原则

### 向量检索兼容
- 每个概念包含清晰的 `tags` 字段用于向量 embedding
- `related_concepts` 双向链接，便于知识图谱构建
- `use_cases` 字段便于场景匹配检索

### 知识图谱兼容
- 使用 Obsidian 双链语法 `[[概念名]]` 建立概念关联
- 层次化：`前置知识` → `相关概念` → `进阶主题`
- `prerequisites` 明确学习路径依赖

### 问答系统兼容
- 核心定义使用**一句话总结**格式，便于直接引用
- 技术实现包含可运行的代码示例
- FAQ 章节针对高频问题提供直接答案

## 📊 概念分类

| 分类 | 描述 | 状态 |
|------|------|------|
| foundation | 基础概念（Token、Embedding等） | 🚧 待创建 |
| architecture | 模型架构（Transformer、Attention等） | 🚧 待创建 |
| training | 训练相关（预训练、微调、RLHF等） | 🚧 待创建 |
| inference | 推理优化（量化、KV缓存等） | 🚧 待创建 |
| application | 应用技术（RAG、Agent等） | 🚧 待创建 |

## 🔄 待添加概念

### Foundation (基础)
- [ ] [[Tokenizer]] - 分词器原理
- [ ] [[Embedding]] - 词嵌入
- [ ] [[Positional Encoding]] - 位置编码

### Architecture (架构)
- [ ] [[Transformer]] - 变换器架构
- [ ] [[Attention]] - 注意力机制
- [ ] [[MLP-FFN]] - 前馈神经网络

### Training (训练)
- [ ] [[Pre-training]] - 预训练
- [ ] [[Fine-tuning]] - 微调
- [ ] [[RLHF]] - 人类反馈强化学习

### Inference (推理)
- [ ] [[KV-Cache]] - 键值缓存
- [ ] [[Quantization]] - 模型量化
- [ ] [[Speculative Decoding]] - 投机解码

### Application (应用)
- [ ] [[RAG]] - 检索增强生成
- [ ] [[Agent]] - AI Agent
- [ ] [[CoT]] - 思维链

---

**状态**: 🚧 进行中
**最后更新**: 2026-05-19
**概念总数**: 1