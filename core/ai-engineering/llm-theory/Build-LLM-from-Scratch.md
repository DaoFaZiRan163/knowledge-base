---
type: book
category: ["大语言模型", "动手实践", "AI工程"]
difficulty: intermediate
tags: ["LLM", "从零构建", "PyTorch", "GPT", "预训练", "微调", "实践"]
reading_status: completed
completion_date: 2026-05-18
prerequisites: ["Python", "PyTorch基础", "深度学习基础概念"]
related_books: ["《深度学习》-Goodfellow", "《大语言模型-CS224N》", "《AI Engineering》"]
related_concepts: ["Transformer", "GPT架构", "自回归训练", "LoRA微调"]
---

# 《Build a Large Language Model from Scratch》- Sebastian Raschka

## 📖 基本信息
- **作者**: Sebastian Raschka（前威斯康星大学计算机科学助理教授，知名 ML 教育者）
- **出版年份**: 2024
- **核心主题**: 从零开始用 PyTorch 构建一个类 GPT 的语言模型，覆盖架构实现、预训练、微调全流程
- **目标读者**: 有 Python/PyTorch 基础，希望通过动手理解 LLM 内部机制的工程师
- **阅读难度**: intermediate

## 🎯 核心价值
> 真正理解 LLM 的最好方式是自己从零写一遍——不是包装 API，而是实现 Attention、训练循环、采样策略，让每个组件都在你脑子里有具体对应。

## 📚 知识框架

### 主要章节/模块

### 1. 文本数据处理
- **分词（Tokenization）**
  - 字符级：最简单，词表小，序列长
  - 词级：词表大，OOV 问题
  - **BPE（字节对编码）**：GPT 系列使用；平衡词表大小和序列长度
  - tiktoken：OpenAI 的 BPE 实现，cl100k_base（GPT-4 使用）
- **嵌入层（Embedding）**
  - Token 嵌入：词表大小 × 隐藏维度
  - 位置嵌入：序列长度 × 隐藏维度
  - 最终嵌入 = Token 嵌入 + 位置嵌入

### 2. Attention 机制实现

#### 简单自注意力（无权重）
```python
def simple_attention(x):
    # x: (seq_len, d_model)
    attn_scores = x @ x.T          # (seq_len, seq_len)
    attn_weights = softmax(attn_scores, dim=-1)
    return attn_weights @ x         # (seq_len, d_model)
```

#### 带权重的自注意力
```python
class SelfAttention(nn.Module):
    def __init__(self, d_in, d_out):
        self.W_q = nn.Linear(d_in, d_out, bias=False)
        self.W_k = nn.Linear(d_in, d_out, bias=False)
        self.W_v = nn.Linear(d_in, d_out, bias=False)

    def forward(self, x):
        Q, K, V = self.W_q(x), self.W_k(x), self.W_v(x)
        scores = Q @ K.T / (K.shape[-1] ** 0.5)
        weights = softmax(scores, dim=-1)
        return weights @ V
```

#### 因果（掩码）注意力
```python
# 上三角掩码，防止看到未来 token
mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool()
scores = scores.masked_fill(mask, float('-inf'))
```

#### 多头注意力
- 将 d_model 分成 h 个头，每头维度 d_model/h
- 并行计算，最后 Concat 再线性变换

### 3. GPT 模型架构实现

```python
class GPTModel(nn.Module):
    def __init__(self, cfg):
        self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.emb_dim)
        self.pos_emb = nn.Embedding(cfg.context_length, cfg.emb_dim)
        self.drop_emb = nn.Dropout(cfg.drop_rate)
        self.trf_blocks = nn.Sequential(*[
            TransformerBlock(cfg) for _ in range(cfg.n_layers)
        ])
        self.final_norm = LayerNorm(cfg.emb_dim)
        self.out_head = nn.Linear(cfg.emb_dim, cfg.vocab_size, bias=False)

    def forward(self, in_idx):
        tok_embeds = self.tok_emb(in_idx)
        pos_embeds = self.pos_emb(torch.arange(in_idx.shape[1]))
        x = self.drop_emb(tok_embeds + pos_embeds)
        x = self.trf_blocks(x)
        x = self.final_norm(x)
        return self.out_head(x)   # logits: (batch, seq_len, vocab_size)
```

#### Transformer Block
```
输入 x
├── LayerNorm
├── 多头因果注意力
├── 残差连接（+ x）
├── LayerNorm
├── 前馈网络（FFN）：Linear → GELU → Linear
└── 残差连接（+ x）
```

#### GPT-2 小型配置参数
```python
GPT_CONFIG_124M = {
    "vocab_size": 50257,
    "context_length": 1024,
    "emb_dim": 768,
    "n_heads": 12,
    "n_layers": 12,
    "drop_rate": 0.1,
    "qkv_bias": False
}
```

### 4. 预训练

#### 数据准备
```python
class GPTDatasetV1(Dataset):
    def __init__(self, txt, tokenizer, max_length, stride):
        self.input_ids = []
        self.target_ids = []
        token_ids = tokenizer.encode(txt)
        for i in range(0, len(token_ids) - max_length, stride):
            input_chunk = token_ids[i:i + max_length]
            target_chunk = token_ids[i + 1:i + max_length + 1]  # 下移一位
            self.input_ids.append(torch.tensor(input_chunk))
            self.target_ids.append(torch.tensor(target_chunk))
```

#### 训练循环
```python
def train_model_simple(model, train_loader, val_loader, optimizer, num_epochs):
    for epoch in range(num_epochs):
        model.train()
        for input_batch, target_batch in train_loader:
            optimizer.zero_grad()
            logits = model(input_batch)
            # 交叉熵损失
            loss = F.cross_entropy(
                logits.flatten(0, 1),   # (batch*seq, vocab)
                target_batch.flatten()   # (batch*seq,)
            )
            loss.backward()
            optimizer.step()
```

### 5. 文本生成（解码策略）

```python
def generate(model, idx, max_new_tokens, temperature=1.0, top_k=None):
    for _ in range(max_new_tokens):
        logits = model(idx[:, -context_size:])
        logits = logits[:, -1, :]            # 只取最后一个 token 的 logits

        if top_k is not None:
            # Top-K 采样：只保留概率最高的 K 个 token
            top_k_logits, _ = torch.topk(logits, top_k)
            logits[logits < top_k_logits[:, -1:]] = float('-inf')

        probs = F.softmax(logits / temperature, dim=-1)
        idx_next = torch.multinomial(probs, num_samples=1)
        idx = torch.cat((idx, idx_next), dim=1)
    return idx
```

**采样策略说明**：
- temperature → 0：接近贪婪，确定性强
- temperature → ∞：接近均匀采样，随机性强
- Top-K：防止采样到低概率 token
- Top-P（核采样）：按累积概率截断

### 6. 加载预训练权重（GPT-2）

```python
# 从 HuggingFace 加载 GPT-2 权重
import gpt_download
params = gpt_download.download_and_load_gpt2(model_size="124M")

# 权重映射到自定义模型
assign(gpt.tok_emb.weight, params["wte"])
assign(gpt.pos_emb.weight, params["wpe"])
# ... 逐层赋值
```

### 7. 指令微调（SFT）

#### 数据格式化
```python
def format_input(entry):
    instruction_text = (
        f"Below is an instruction that describes a task. "
        f"Write a response that appropriately completes the request."
        f"\n\n### Instruction:\n{entry['instruction']}"
    )
    input_text = f"\n\n### Input:\n{entry['input']}" if entry["input"] else ""
    return instruction_text + input_text
```

#### 微调要点
- 只对 Response 部分计算损失（Instruction 部分 mask 掉）
- 学习率远小于预训练（1e-5 vs 1e-4）
- 少量高质量数据（几千条）即可显著改变行为

---

## 🔑 关键概念

### Pre-LN vs Post-LN
**定义**: 
- Post-LN（原始 Transformer）：Sublayer → Add → LayerNorm
- Pre-LN（现代实践，包括 GPT-2）：LayerNorm → Sublayer → Add

**重要性**: Pre-LN 训练更稳定，梯度流更好，允许省去 Warmup

---

### 权重共享（Weight Tying）
**定义**: 输入的 Token 嵌入矩阵与输出线性层共享权重（转置关系）

**重要性**: 减少参数量；在输入和输出语义空间保持一致

---

## 💡 实战应用场景

### 场景 1: 理解为什么 LLM 生成重复
**背景**: 模型生成时陷入重复循环

**解决方案**: 调整采样策略

**实施步骤**:
1. 检查 temperature：太低会贪婪选择最高概率，容易循环
2. 加入重复惩罚（repetition_penalty > 1.0）
3. 使用 Top-P 采样而非 Top-K

---

### 场景 2: 评估是否需要微调还是 Prompt Engineering
**背景**: 客户想改变模型的输出风格

**解决方案**: 先 Prompt，不行再微调

**实施步骤**:
1. 先用 System Prompt + Few-shot 尝试引导输出风格
2. 若一致性不够，收集 100-500 条样本做 SFT
3. 微调时只改变输出层附近的参数（LoRA r=8 足够）

---

## 🔗 相关技术栈
- **框架**: PyTorch（本书全程使用）
- **模型下载**: HuggingFace Hub, tiktoken
- **部署**: llama.cpp（GGUF 量化格式）, Ollama

---

## 📝 个人笔记

### 重要洞察
- 手写过一遍 Attention 之后，调用 `nn.MultiheadAttention` 时心里有底了
- 预训练的本质是在做一件事：预测下一个 token
- 微调改变的不是"知识"，而是"行为模式"——知识存在预训练权重里

### 待深入研究
- [ ] 研究 Flash Attention 如何通过 IO 优化加速注意力计算
- [ ] 从本书的代码扩展，实现 LoRA 微调
- [ ] 了解 Grouped Query Attention（GQA）如何减少 KV Cache

### 实践项目
- [ ] 跟着本书完整实现一个 GPT-2 等效模型
- [ ] 在小语料上（如诗歌数据集）预训练，观察 Loss 曲线

---

## 🎓 学习检验

### 自测问题
1. 因果掩码（Causal Mask）是如何实现的？为什么 GPT 需要它而 BERT 不需要？
2. temperature=0 和 temperature=1 的生成有何本质区别？
3. 为什么微调时要 mask 掉 Instruction 部分的 loss？
4. Weight Tying 的直觉是什么？
5. LayerNorm 和 BatchNorm 的区别是什么？GPT 为什么选 LayerNorm？

### 实践任务
- [ ] 实现不带掩码的自注意力，再加上因果掩码，对比两者的 attention map
- [ ] 修改采样代码，实现 Nucleus Sampling（Top-P）

---

## 📊 知识关联

### 前置知识
- [[深度学习-Goodfellow]]
- [[大语言模型-CS224N]]

### 后续学习
- [[AI Engineering-Chip-Huyen]]
- [[LLM记忆分层架构]]

### 并行学习
- [[Prompt工程化团队规范]]

---

## 🏷️ 标签系统
#书籍 #技术 #LLM #intermediate

---
**阅读开始**: 2026-05-18
**阅读完成**: 2026-05-18
**下次复习**: 2026-06-18
**总计用时**: 知识提炼版（直接生成）
**推荐指数**: ⭐⭐⭐⭐⭐
