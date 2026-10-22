# 架构设计 (ARCHITECTURE.md)

## 设计原则

**数据源适配器模式（Data-Source Adapter）**：把「麦当劳 MCP」这一具体数据源隔离在 `adapter` 层，
上层 `collector / optimizer / monitor / report` 只依赖**结构化 profile**，不感知传输协议与字段细节。
这样既能降低耦合，也为「横向扩展更多积分体系」留出干净接口。

## 模块依赖图

```
                 ┌─────────────────────────────────────────┐
   CLI / WorkBuddy│            mcd_asset_assistant           │
        └────────┤                                         │
                 │  cli.py ──► collector.py ──► optimizer.py │
                 │     │                │        │          │
                 │     └── monitor.py ◄┘        └─► report.py
                 │            │                             │
                 │       adapter.py ◄── 麦当劳 MCP          │
                 │       (Streamable HTTP)                  │
                 └─────────────────────────────────────────┘
                            mock_data.py（离线演示，绕过 adapter）
```

## 数据契约：Profile

所有上层逻辑围绕统一 `profile` 结构工作：

```python
profile = {
  "generated_at": str,
  "account": {"available", "accumulated", "frozen", "expiring", "expiring_date"},
  "coupons": [{"name", "value", "expire"}],
  "available_coupons": [{"name"}],
  "orders": [{"date", "amount", "summary"}],
  "mall_products": [{"name", "points"}],
  "lottery": {"active", "prizes": [str]},
}
```

真实路径由 `collector.collect_profile(client)` 从 MCP 工具结果填充；
演示路径由 `mock_data.build_profile()` 填充。两者结构一致，上层无感切换。

## 如何扩展

### 1. 接入新的积分体系（如星巴克）

新增适配器，实现同样的「返回 profile」契约即可：

```python
class StarbucksMCPClient:
    def collect_profile(self) -> dict:
        # 调用星巴克 MCP，返回与麦当劳同构的 profile
        ...
```

`optimizer / report` 无需改动，因为只认 profile 结构。

### 2. 新增分析维度

在 `optimizer.py` 增加纯函数（输入 profile、输出建议），并在 `report.py` 渲染即可。

### 3. 监控即服务

`monitor.scan_once(client)` 已是「少量只读调用 + 结构化告警」。可挂：

- 本地 cron：`0 9 * * * python -m mcd_asset_assistant --monitor --out alert.md`
- 云函数（SCF / 定时触发器）：结果推送到 IM / 邮件。

## 安全边界

- 配置仅用环境变量占位符（`${MCD_MCP_TOKEN}`），仓库不含任何真实凭证。
- 坚持只读：不调用下单 / 抽奖 / 领券等写操作，处置建议由用户决策。
- Token 每分钟 600 次限流，监控路径单次调用极少，不会触顶。
