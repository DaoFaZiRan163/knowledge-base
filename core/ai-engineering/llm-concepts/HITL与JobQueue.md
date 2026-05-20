---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["HITL", "JobQueue", "人机协作", "异步任务", "工作流"]
source: 原创
created_date: 2026-05-19
updated_date: 2026-05-19
implementation_status: production_ready
use_cases: ["人工审批", "异步处理", "长时任务", "质量控制"]
related_concepts: ["Agent", "LangChain", "工作流编排"]
prerequisites: ["LLM基础原理", "Agent"]
---

# HITL 与 JobQueue — 人机协作模式

## 核心定义

**HITL (Human-in-the-Loop)**：人在关键环节参与决策的人工智能协作模式，确保 AI 输出符合人类意图和价值观。

**JobQueue (任务队列)**：将异步任务排队处理的管理系统，支持任务的调度、优先级、重试和监控。

**核心理念**：复杂 AI 系统需要人类在关键节点把关，任务队列确保大规模异步处理的有序进行。

## 🎯 一句话总结

> **HITL = 人类在关键节点做决策；JobQueue = 异步任务排队处理**

```
HITL 模式:
AI生成 → 人类审核 → 通过/修改 → 下一步

JobQueue 模式:
任务 → 入队 → 队列 → Worker处理 → 完成
```

## 🏗️ HITL 模式

### 触发时机

| 时机 | 说明 | 示例 |
|------|------|------|
| 前置审批 | 执行前人类确认 | AI 发送邮件前主管审批 |
| 后置审核 | 执行后人类确认 | AI 生成合同后法务审核 |
| 异常处理 | AI 不确定时求助 | AI 识别敏感内容需人工判断 |
| 持续监控 | 人类监控 AI 行为 | AI 输出实时监控 |

### 人机协作级别

```
Level 0: 纯 AI，自动执行
Level 1: AI 建议，人类最终决策
Level 2: AI 执行，人类随时可干预
Level 3: AI 辅助，人类主导
Level 4: 纯人工，AI 仅提供信息
```

## 🏗️ JobQueue 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    JobQueue 架构                            │
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    │
│  │ API     │ → │  队列   │ → │ Worker  │ → │  结果   │    │
│  │ 接收任务 │    │(Redis) │    │ 处理任务 │    │ 存储    │    │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    │
│                     ↑                                         │
│              ┌──────┴──────┐                                 │
│              │  定时任务    │                                 │
│              │ (Cron Job)  │                                 │
│              └─────────────┘                                 │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 技术实现

### HITL 实现

```python
from enum import Enum

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"

class HumanInTheLoop:
    def __init__(self, notification_service):
        self.notification_service = notification_service

    async def request_approval(self, task, context):
        """请求人工审批"""
        # 创建审批任务
        approval_task = {
            "id": generate_id(),
            "task": task,
            "context": context,
            "status": ApprovalStatus.PENDING,
            "created_at": datetime.now()
        }

        # 发送通知
        await self.notification_service.notify(
            approvers=task.approvers,
            task=approval_task
        )

        # 等待审批（阻塞或回调）
        return await self.wait_for_approval(approval_task["id"])

    async def wait_for_approval(self, task_id, timeout=3600):
        """等待审批结果"""
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_approval_status(task_id)
            if status != ApprovalStatus.PENDING:
                return status
            await asyncio.sleep(5)

        raise TimeoutError("审批超时")
```

### JobQueue 实现

```python
import asyncio
from dataclasses import dataclass
from typing import Callable
import redis

@dataclass
class Job:
    id: str
    task_type: str
    payload: dict
    priority: int = 0
    max_retries: int = 3
    retry_count: int = 0

class JobQueue:
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.queue_name = "llm_jobs"

    async def enqueue(self, job: Job):
        """添加任务到队列"""
        score = -job.priority  # 优先级高的分数低
        self.redis.zadd(self.queue_name, {job.id: score})

    async def dequeue(self) -> Job:
        """获取任务（阻塞）"""
        while True:
            result = self.redis.zpopmin(self.queue_name, 1)
            if result:
                job_id = result[0][0]
                return self.get_job(job_id)
            await asyncio.sleep(1)

    async def process(self, handler: Callable):
        """Worker 处理任务"""
        while True:
            job = await self.dequeue()
            try:
                result = await handler(job)
                self.mark_complete(job.id, result)
            except Exception as e:
                if job.retry_count < job.max_retries:
                    job.retry_count += 1
                    await self.enqueue(job)
                else:
                    self.mark_failed(job.id, str(e))
```

### HITL + JobQueue 结合

```python
class HITLJobQueue:
    """需要人工审批的任务队列"""

    async def submit_task(self, task):
        if task.requires_approval:
            # 进入人工审批队列
            await self.hitl.request_approval(task)
        else:
            # 进入自动处理队列
            await self.job_queue.enqueue(task)

    async def process_approval_result(self, approval_result):
        if approval_result.status == ApprovalStatus.APPROVED:
            await self.job_queue.enqueue(approval_result.task)
        elif approval_result.status == ApprovalStatus.MODIFIED:
            # 使用修改后的内容
            modified_task = approval_result.modified_task
            await self.job_queue.enqueue(modified_task)
        # REJECTED 则不处理
```

## 💼 FDE 应用场景

### 场景 1: AI 邮件发送审批

**需求**: AI 生成的邮件在发送前需要主管审批

**方案**: 前置 HITL，审批通过后 JobQueue 执行发送

**效果**: 避免 AI 误发邮件，减少公司损失

### 场景 2: 合同生成审核

**需求**: AI 生成的合同需法务审核后才能给客户

**方案**: 后置 HITL + 多级审批流程

**效果**: 法律风险降低，审核流程数字化

### 场景 3: 大规模内容处理

**需求**: 每天处理 10 万篇文章，AI 总结后人工抽检

**方案**: JobQueue 批量处理 + 5% 抽检 HITL

**效果**: 处理效率提升 20 倍，质量可控

### 场景 4: 敏感内容审核

**需求**: AI 识别到敏感内容时暂停，等待人工判断

**方案**: 异常触发 HITL，处理后决定继续或终止

**效果**: 合规风险降低，误判率 < 1%

## 📊 关键指标

| 指标 | 说明 | 目标 |
|------|------|------|
| 审批周期 | 从提交到审批完成的平均时间 | < 2小时 |
| 自动化率 | 无需人工干预的任务比例 | > 90% |
| 队列积压 | 等待处理的任务数 | < 1000 |
| Worker 利用率 | Worker 忙碌时间占比 | 70-90% |

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 审批积压 | 审批人未及时处理 | 催办通知、限时机制 |
| 队列阻塞 | Worker 故障或任务死循环 | 超时中断、优先级调度 |
| 审批遗漏 | 通知未送达 | 多渠道通知、状态跟踪 |

## 🔗 相关知识

- [[Agent]] - Agent 决策
- [[并发熔断与容灾降级]] - 故障处理
- [[输出Guardrail与成本监控]] - 输出质量控制

---

**向量检索标签**: HITL, 人机协作, JobQueue, 异步任务, 人工审批, 工作流