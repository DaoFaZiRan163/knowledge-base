---
type: concept
category: ["ai-engineering", "llm-concepts"]
difficulty: intermediate
tags: ["MCP协议", "配额预占", "API配额", "资源管理", "成本控制"]
source: 原创
created_date: 2026-05-19
updated_date: 2026-05-19
implementation_status: production_ready
use_cases: ["API调用控制", "成本管理", "资源分配", "多租户"]
related_concepts: ["Agent", "并发熔断与容灾降级"]
prerequisites: ["LLM基础原理"]
---

# MCP协议与配额预占

## 核心定义

**MCP (Model Context Protocol)**：Anthropic 提出的模型上下文协议，用于标准化 AI 应用与外部工具、数据源的连接。

**配额预占 (Quota Reservation)**：在消费前预先锁定资源配额，确保关键任务有足够资源执行。

**核心理念**：MCP 解决"如何连接"，配额预占解决"如何保证资源"。

## 🎯 一句话总结

> **MCP = AI 与外部世界的标准接口；配额预占 = 资源预留与防超售**

```
MCP:
AI应用 ← → MCP Server ← → 工具/数据源

配额预占:
请求 → 检查配额 → 预占 → 执行 → 确认/回滚
```

## 🏗️ MCP 协议架构

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP 协议架构                              │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │  AI 应用    │ ←→ │ MCP Client  │ ←→ │ MCP Server  │   │
│  │ (Claude等)  │    │ (SDK)       │    │ (工具/数据)  │   │
│  └─────────────┘    └─────────────┘    └─────────────┘   │
│         │                  │                  │          │
│         └──────────────────┼──────────────────┘          │
│                            │                               │
│                    ┌───────┴───────┐                      │
│                    │  标准协议    │                      │
│                    │ JSON-RPC 2.0  │                      │
│                    └───────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### MCP 能力

| 能力 | 说明 |
|------|------|
| 工具调用 (Tools) | AI 可以调用外部功能 |
| 资源访问 (Resources) | AI 可以读取外部数据 |
| 提示模板 (Prompts) | 可复用的提示模板 |
| 采样 (Sampling) | AI 请求人类输入 |

## 🏗️ 配额预占机制

```
┌─────────────────────────────────────────────────────────────┐
│                    配额预占流程                              │
│                                                             │
│  请求到达                                                    │
│     │                                                       │
│     ▼                                                       │
│  ┌──────────┐                                              │
│  │ 检查配额  │ ← 当前已用 + 本次需求 > 配额？               │
│  └────┬─────┘                                              │
│       │  是   │否                                          │
│       ▼       ▼                                            │
│  ┌────────┐  ┌────────┐                                   │
│  │ 拒绝   │  │ 预占配额│                                   │
│  │ 或排队 │  │ 继续执行│                                   │
│  └────────┘  └────┬────┘                                   │
│                   │                                        │
│                   ▼                                        │
│            ┌────────────┐                                  │
│            │ 执行任务   │                                  │
│            └─────┬──────┘                                  │
│                  │                                        │
│         ┌────────┴────────┐                               │
│         ▼                 ▼                                │
│    ┌────────┐       ┌────────┐                           │
│    │ 确认   │       │ 回滚   │ ← 执行失败/超时            │
│    │ 释放配额│       │ 释放配额│                           │
│    └────────┘       └────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 技术实现

### MCP Server 实现

```python
from mcp.server import MCPServer
from mcp.types import Tool, Resource

server = MCPServer("my-server")

@server.tool("search_database")
def search_database(query: str) -> str:
    """搜索数据库"""
    results = db.execute(query)
    return format_results(results)

@server.resource("customer_data/{customer_id}")
def get_customer(customer_id: str) -> dict:
    """获取客户数据"""
    return db.customers.find_one(id=customer_id)

# 运行服务器
server.run()
```

### MCP Client 调用

```python
from mcp import Client

async def main():
    client = Client("http://localhost:8080")

    # 调用工具
    result = await client.call_tool(
        "search_database",
        {"query": "SELECT * FROM orders"}
    )

    # 访问资源
    customer = await client.get_resource(
        "customer_data/12345"
    )

    print(result, customer)
```

### 配额预占实现

```python
import asyncio
from datetime import datetime, timedelta

class QuotaManager:
    def __init__(self):
        self.quotas = {}  # tenant_id -> quota_info
        self.reservations = {}  # reservation_id -> reservation_info

    async def reserve(self, tenant_id, tokens_needed, ttl_seconds=60):
        """预占配额"""
        quota = self.quotas.get(tenant_id)
        if not quota:
            raise NoQuotaError(tenant_id)

        # 检查剩余配额
        available = quota.total - quota.used - quota.reserved
        if available < tokens_needed:
            raise QuotaExceededError(tenant_id, available, tokens_needed)

        # 创建预占
        reservation_id = generate_id()
        self.reservations[reservation_id] = {
            "tenant_id": tenant_id,
            "tokens": tokens_needed,
            "expires_at": datetime.now() + timedelta(seconds=ttl_seconds)
        }
        quota.reserved += tokens_needed

        return reservation_id

    async def confirm(self, reservation_id):
        """确认使用配额"""
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            raise ReservationNotFoundError()

        quota = self.quotas[reservation["tenant_id"]]
        quota.reserved -= reservation["tokens"]
        quota.used += reservation["tokens"]

        del self.reservations[reservation_id]

    async def rollback(self, reservation_id):
        """回滚预占"""
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            return  # 可能已超时自动清理

        quota = self.quotas[reservation["tenant_id"]]
        quota.reserved -= reservation["tokens"]

        del self.reservations[reservation_id]
```

### 配额 + MCP 集成

```python
class MCPWithQuota:
    def __init__(self, quota_manager, mcp_client):
        self.quota_manager = quota_manager
        self.mcp_client = mcp_client

    async def call_tool_with_quota(self, tenant_id, tool_name, params):
        # 预估 token 消耗
        estimated_tokens = estimate_tokens(params)

        # 预占配额
        reservation = await self.quota_manager.reserve(
            tenant_id, estimated_tokens
        )

        try:
            # 调用 MCP 工具
            result = await self.mcp_client.call_tool(tool_name, params)

            # 确认配额
            await self.quota_manager.confirm(reservation)

            return result

        except Exception as e:
            # 回滚配额
            await self.quota_manager.rollback(reservation)
            raise e
```

## 💼 FDE 应用场景

### 场景 1: 多租户 API 服务

**需求**: 多个客户共享 LLM API，需公平分配资源

**方案**:
1. 每个租户设置配额（每分钟/每小时 tokens）
2. 请求前预占配额
3. 超配额限流或拒绝

**效果**: 避免单一客户耗尽所有配额

### 场景 2: 成本控制

**需求**: 精确控制每月 LLM API 支出

**方案**:
1. 设置月度配额
2. 实时监控已用配额
3. 配额用尽前预警，用尽后降级

**效果**: 月度成本波动 < 5%

### 场景 3: MCP 工具治理

**需求**: 企业内部多个 MCP 工具，需统一管理访问权限

**方案**:
1. MCP Server 统一认证
2. 配额按工具/用户维度控制
3. 审计日志记录每次调用

**效果**: 工具访问可控可追溯

## 📊 关键指标

| 指标 | 说明 | 监控目标 |
|------|------|----------|
| 配额使用率 | 已用 / 总配额 | < 80% |
| 预占成功率 | 成功预占 / 总请求 | > 95% |
| 超配额拒绝率 | 拒绝数 / 总请求 | < 2% |
| 配额回滚率 | 回滚数 / 预占数 | < 10% |

## ⚠️ 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 预占后未确认 | 任务异常未完成 | TTL 自动清理 + 监控 |
| 配额预估不准 | token 估算偏差大 | 实际消耗 vs 预估对比调优 |
| 并发预占超量 | 竞态条件 | 原子操作 + 事务 |

## 🔗 相关知识

- [[并发熔断与容灾降级]] - 资源不足时的降级
- [[输出Guardrail与成本监控]] - 成本控制
- [[Agent]] - Agent 的资源调用

---

**向量检索标签**: MCP协议, 配额预占, API管理, 资源控制, 成本控制, 多租户