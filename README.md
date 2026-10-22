# 🍔 麦门资产助手 (McD Asset Assistant)

> 把你的麦当劳**积分、优惠券、订单**，当成一笔会贬值的「资产」管起来。
> 查询 · 优化 · 监控，三层合一。麦当劳程序员节创意开发大赛作品（非官方）。

## 🎮 30 秒看到你自己的资产

**打开 `demo/index.html` 所在目录，起一个服务，粘贴你的 MCP Token，就能看到你自己的真实积分、优惠券和消费洞察：**

```bash
cd demo
python server.py          # → http://127.0.0.1:8899
```

然后在页面里粘贴你在 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 获取的 Token，点「查我的资产」。

- **真实数据**：读的是你自己的麦当劳账户（积分 / 券 / 订单 / 麦麦省可领券），不是示例数字
- **免登录**：Token 存在浏览器 localStorage，下次打开自动查
- **安全**：Token 只在浏览器与本次请求中，服务端不落盘、不写日志、不外传
- **纯只读**：后端有只读工具白名单，`create-order` / `draw-lottery` 等写操作一律拒绝

> 为什么需要后端？麦当劳 MCP 未开放 CORS，浏览器无法直连，必须由服务端转发。`demo/server.py` **零第三方依赖**，只用 Python 标准库。

**不想接 Token？** 页面上的「先看示例」按钮会直接展示一份示例报告——用来理解这个工具在解决什么问题。

## 这是什么

大多数人手机里有大把**即将过期的积分**和**躺平的优惠券**，却从没被提醒「该用了」。
「麦门资产助手」基于**麦当劳 MCP** 真实读取你的账户数据，自动告诉你：

- 哪些积分快过期了、怎么花最不亏；
- 手里哪些券该优先用、怎么叠加最省钱；
- 麦麦省有没有新券可领、本月有什么活动；
- 顺手给你一份可分享的「麦门资产报告」。

## 为什么做

排行榜调研显示，104 个参赛项目里**前三全是「省钱」、还有一批「营养/卡路里」**——这两个方向已红海。
而 `query-my-account`（含**即将过期/冻结积分**）、`order-list` 这类**个人资产数据几乎没人做透**。
「把积分当资产管」是差异化强、痛点真、又容易做出传播性的切口。

## 三大能力 × 真实 MCP 工具

| 能力 | 说明 | 调用的麦当劳 MCP 工具 |
| --- | --- | --- |
| **查询** | 拉取积分 / 券 / 订单真实数据 | `query-my-account`、`query-my-coupons`、`available-coupons`、`order-list` |
| **优化** | 积分过期前最优用法、券组合建议 | `mall-points-products`、`query-lottery-info`、`query-my-coupons`（结合订单金额） |
| **监控** | 新券 / 活动 / 积分临期主动提醒 | `available-coupons`、`campaign-calendar`、`query-my-account` |

> 所有数据均通过麦当劳官方 MCP 实时获取，仅做只读分析，**不自动下单、不自动消费**（支付由人完成，安全边界清晰）。

## 快速开始

### 方式一：WorkBuddy（推荐，参赛正途）

1. 在麦当劳 MCP 开放平台（open.mcd.cn/mcp）用手机号登录 → 控制台 → 激活 → 复制 **MCP Token**。
2. 打开 WorkBuddy → 左侧「专家·技能·连接器」→「连接器」→「自定义连接器」→「配置 MCP」，粘贴：
   ```json
   {
     "mcpServers": {
       "mcd-mcp": {
         "type": "streamablehttp",
         "url": "https://mcp.mcd.cn",
         "headers": { "Authorization": "Bearer 你的MCP_TOKEN" }
       }
     }
   }
   ```
3. 启用 `mcd-mcp`，在对话框里直接说需求即可（例如「帮我看看积分会不会过期、券怎么用最划算」）。

### 方式二：本地运行（本仓库代码）

```bash
pip install -r requirements.txt

# 1) 离线演示（无需 Token，立刻看效果）
python -m mcd_asset_assistant --demo --format md

# 2) 真实拉取并生成报告（需配置 Token）
export MCD_MCP_TOKEN="你的MCP_TOKEN"
python -m mcd_asset_assistant --query --format md

# 3) 一次监控扫描（发现新券 / 临期积分）
python -m mcd_asset_assistant --monitor
```

> 也可加 `--out report.md` 把结果写入文件；`--format html` / `card` 可生成网页报告或分享卡片。

## 示例输出（真实账户运行）

> 以下为接入 `mcd-mcp` 连接器、执行 `python -m mcd_asset_assistant --query --format md` 的真实输出：

```
# 🍔 麦门资产报告
> 生成时间：2026-10-22 15:30:18　数据源：mcd-mcp (real)

## 一、积分资产
- 可用积分：3353　累计：9393　冻结：0
- 即将过期：0 分（—）
- ✅ 当前没有即将过期的积分，可安心累积。

## 二、优惠券
- 名下券合计价值约 ¥39
  - 名下共 4 张券，合计价值约 ¥39。
  - 优先用掉 7 天内过期的：11.9元麦辣鸡腿堡、19.9元王牌炸鸡任选2、9.9元中杯冰美式、人气麦旋风买一送一。
  - 大额订单优先叠加「19.9元王牌炸鸡任选2」（¥19）。

## 三、消费洞察
- 近 10 笔订单累计 ¥387.8，均价 ¥38.8。

## 四、下一步行动
1. 先处理临期积分与临期券，避免无偿作废。
2. 大额订单优先叠加高价值券。
3. 关注麦麦省新券与本月活动，主动领取。
```

> 想看离线效果无需 Token：直接 `python -m mcd_asset_assistant --demo --format md` 即可。`--format html` 可生成网页报告，`--format card` 生成可分享卡片。

## 目标用户

- 麦当劳会员，尤其是**积分/优惠券长年积压**、总忘记用的人；
- 想「用 WorkBuddy + 麦当劳 MCP 做一个真正能用的 Skill」的开发者（本仓库即模板）；
- 对「个人数字资产可视化」感兴趣的产品 / 技术爱好者。

## 项目结构

```
mcd-asset-assistant/
├── README.md                 # 本文件
├── LICENSE                   # MIT 许可证
├── CONTEST_DECLARATION.md    # 参赛声明（官方原文，勿改）
├── MCP_INTEGRATION.md        # MCP 接入说明（必交）
├── mcp-config.example.json   # 脱敏配置示例（必交）
├── workbuddy.md              # WorkBuddy 对话上下文（参与专项奖励必交）
├── SKILL.md                  # WorkBuddy Skill 定义
├── ARCHITECTURE.md           # 扩展性设计
├── DEVELOPMENT_PLAN.md       # 3 天冲刺排期
├── SUBMISSION.md             # 报名 Issue 文案
├── demo/
│   ├── index.html            # 🎮 Web 界面：粘贴 Token 即见自己真实资产
│   └── server.py             # 轻量后端（零依赖，转发 MCP 请求）
└── mcd_asset_assistant/      # 源码
    ├── adapter.py            # 麦当劳 MCP 适配器（数据源隔离层）
    ├── collector.py          # 真实数据采集 → 归一化 profile
    ├── optimizer.py          # 积分/券/订单分析优化（纯函数）
    ├── monitor.py            # 监控扫描（可定时触发）
    ├── report.py             # Markdown/HTML/卡片报告
    ├── mock_data.py          # 离线演示数据
    └── cli.py                # 命令行入口
```

## 三种使用方式

| 方式 | 适合谁 | 命令 |
| --- | --- | --- |
| **Web 界面** | 想看自己真实资产的任何人 | `cd demo && python server.py` |
| **WorkBuddy Skill** | 在 WorkBuddy 里对话式使用 | 见 `SKILL.md` |
| **命令行** | 开发者 / CI | `python -m mcd_asset_assistant --query --format md` |

## 路线图（扩展性）

当前只接了麦当劳。架构上已把「数据源」隔离在 `adapter` 层，未来可低成本扩展：

- **多平台积分**：新增 `StarbucksAdapter` / `AirlineAdapter` 实现同一接口，即可把「积分资产管家」做成通用框架；
- **监控即服务**：`monitor` 已设计为「少量只读调用 + 结构化告警」，可挂 cron / 云函数做周期性推送；
- **消费洞察**：`order-list` 数据可生成「年度麦门账单」式分享卡片，天然利于传播。

## 声明

参赛作品，非麦当劳官方产品。输出仅供参考，不构成任何专业建议；餐品、价格、供应状态以麦当劳官方渠道为准。详见 `CONTEST_DECLARATION.md`。

## ⭐ 求 Star

排行榜 100% 看 GitHub 公开 Star。如果觉得「把积分当资产管」这个点子有意思，欢迎 Star + 提 Issue，一起把它做成真正好用的个人资产助手！
