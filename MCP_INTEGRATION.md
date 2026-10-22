# MCP 接入说明 (MCP_INTEGRATION.md)

## 一、使用的麦当劳 MCP Server

| 项 | 值 |
| --- | --- |
| 提供方 | 麦当劳中国（金拱门） |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 鉴权方式 | 请求头 `Authorization: Bearer <MCP_TOKEN>` |
| Token 申请 | 麦当劳 MCP 开放平台 open.mcd.cn/mcp（手机号登录 → 控制台 → 激活） |
| 限流 | 每 Token 600 次/分钟，超限返回 429 |

> 脱敏配置示例见 `mcp-config.example.json`（仅使用 `${MCD_MCP_TOKEN}` 环境变量占位符，不含任何真实凭证）。

## 二、实际调用的工具（Tool）

| 工具名 | 用途 | 在本项目中的作用 |
| --- | --- | --- |
| `query-my-account` | 查询积分账户（可用/累计/冻结/**即将过期**） | **核心**：识别临期积分并给出处置建议 |
| `query-my-coupons` | 查询账户可用优惠券 | 优惠券清单 + 价值统计 + 临期优先 |
| `available-coupons` | 查询麦麦省当前可领券 | 监控新券、提示一键领取 |
| `query-store-coupons` | 查询当前门店可用券 | （扩展）门店级券组合 |
| `order-list` | 查询近期到店/外送历史订单 | 消费洞察、客单价分析 |
| `mall-order-list` | 查询麦麦商城订单 | （扩展）积分消费记录 |
| `mall-points-products` | 查询积分商城可兑换商品 | 临期积分「怎么花最值」 |
| `query-lottery-info` | 查询积分抽奖活动 | 临期积分替代去向 |
| `campaign-calendar` | 查询当月营销活动日历 | 监控本月限时活动 |
| `now-time-info` | 获取当前时间 | 计算积分/券剩余天数 |

> 本项目坚持**只读分析**原则：不调用 `create-order` / `draw-lottery` / `auto-bind-coupons` 等写操作，所有「处置建议」由用户自行决策执行，安全边界清晰。

## 三、调用流程（Call Flow）

```
用户/CLI
   │
   ▼
McDMCPClient（adapter.py）
   ├─ initialize 握手（protocolVersion 2024-11-05，获取 Mcp-Session-Id）
   └─ tools/call 调用上述工具
   │
   ▼
collector.collect_profile()   把各工具返回归一化为统一 profile
   │
   ▼
optimizer 分析（积分/券/订单）
   │
   ▼
report.build_report()         渲染 Markdown / HTML / 分享卡片
```

## 四、业务价值

1. **痛点真实**：积分/优惠券过期是全民高频痛点，现有项目几乎无人覆盖「个人资产视角」。
2. **数据真实**：全部基于麦当劳官方 MCP 实时读取，非估算、非样例。
3. **差异显著**：相对红海的「省钱/营养」方向，本作品切入「资产管家 + 监控提醒」，在 100+ 项目中辨识度高。
4. **可扩展**：数据源隔离在 adapter 层，理论上可平滑接入其它积分体系，具备产品化潜力。
