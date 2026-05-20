---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["SFT", "监督微调", "LLM训练", "指令微调", "Fine-tuning"]
source: 原创
created_date: 2026-05-19
updated_date: 2026-05-19
implementation_status: production_ready
use_cases: ["任务微调", "领域适配", "指令跟随", "垂直行业模型"]
related_concepts: ["RLHF", "DPO", "LoRA", "模型微调与强化学习"]
prerequisites: ["LLM基础原理"]
---

# SFT — 监督微调 (Supervised Fine-Tuning)

## 核心定义

**SFT (Supervised Fine-Tuning)**：使用标注好的 (输入, 输出) 对数据，通过传统监督学习方式微调预训练模型，使其学会执行特定任务。

**核心理念**：用明确的输入输出对教模型"应该怎么做"，是最直接的微调方式。

## 🎯 一句话总结

> **SFT = 准备标注数据 → 监督学习 → 模型学会任务**

```
预训练:  学习语言规律 + 世界知识 (无标签文本)
SFT:     学习任务能力 (标注数据: 输入→期望输出)

示例:
输入: "将以下英文翻译成中文: Hello, world!"
期望: "你好，世界！"
```

## 🏗️ SFT 数据格式

### 常见数据格式

```json
// OpenAI 格式
{
  "messages": [
    {"role": "system", "content": "你是一个翻译助手"},
    {"role": "user", "content": "将以下英文翻译成中文: Hello, world!"},
    {"role": "assistant", "content": "你好，世界！"}
  ]
}

// 指令格式
{
  "instruction": "翻译以下句子",
  "input": "Hello, world!",
  "output": "你好，世界！"
}
```

### 数据量级建议

| 任务类型 | 最低数据量 | 推荐数据量 | 效果影响因素 |
|----------|------------|------------|--------------|
| 简单分类 | 100-500 | 1,000-5,000 | 数据质量 |
| 对话生成 | 500-1,000 | 5,000-20,000 | 多样性 |
| 领域专家 | 1,000-5,000 | 10,000-50,000 | 领域覆盖 |

## 🔧 技术实现

### 标准 SFT 流程

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
from trl import SFTTrainer

# 加载预训练模型
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b")

# 准备数据
dataset = load_dataset("json", data_files="train.jsonl")

# 配置训练参数
training_args = TrainingArguments(
    output_dir="./sft_output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-5,
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    logging_steps=10,
    save_steps=500,
    bf16=True,  # 使用 BF16 加速
)

# 创建 trainer
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    max_seq_length=4096,
)

# 开始训练
trainer.train()
```

### LoRA 微调 (高效版)

```python
from peft import LoraConfig, get_peft_model

# LoRA 配置
lora_config = LoraConfig(
    r=16,  # LoRA 秩
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],  # 目标层
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# 应用 LoRA
model = get_peft_model(model, lora_config)

# LoRA 只有 0.1% 参数需要更新
model.print_trainable_parameters()
# trainable params: 4,194,304 || all params: 6,738,415,616 || trainable%: 0.0623
```

### 数据预处理

```python
def format_instruction(example):
    """将数据格式化为指令格式"""
    return {
        "text": f"""### 指令:
{example['instruction']}

### 输入:
{example['input']}

### 响应:
{example['output']}

### 结束"""
    }

dataset = dataset.map(format_instruction)
```

## 💼 FDE 应用场景

### 场景 1: 客服对话系统

**需求**: 定制化客服风格和话术

**方案**: 收集历史客服对话，SFT 微调

**效果**: 客服回答质量接近人工，新员工培训周期缩短

### 场景 2: 代码助手

**需求**: 生成符合团队规范的代码

**方案**: SFT 微调团队代码库 + 代码规范文档

**效果**: 代码采纳率从 40% 提升至 75%

### 场景 3: 领域知识问答

**需求**: 法律/医疗等专业领域准确问答

**方案**: SFT 微调领域数据 + 知识图谱增强

**效果**: 领域问答准确率提升至 90%+

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 过拟合 | 数据量少或训练过长 | 早停、数据增强、LoRA |
| 灾难性遗忘 | 过度适应新任务丢失通用能力 | 混合原任务数据、降低学习率 |
| 格式崩塌 | 特殊格式数据干扰模型结构 | 数据质量筛选、格式标准化 |

## 🔗 相关知识

- [[模型微调与强化学习]] - 微调与 RL 的关系
- [[LoRA]] - 高效微调技术
- [[DPO]] - 替代 RLHF 的新方法

---

**向量检索标签**: SFT, 监督微调, 指令微调, 模型训练, Fine-tuning, LoRA