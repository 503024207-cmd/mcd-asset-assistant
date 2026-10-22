# 3 天冲刺排期 (DEVELOPMENT_PLAN.md)

> 背景：活动报名/排名截止 **2026-10-25 23:59**（北京时间），今天 10-22，仅约 3 天。
> 排名 100% 看 GitHub 公开 Star，因此「能跑的 demo + 易传播 + 早提交」优先于功能堆砌。

## Day 1（10-22）：接管道 + 跑通 MVP

- [ ] 在 open.mcd.cn/mcp 申请 MCP Token，WorkBuddy 接入 `mcd-mcp` 连接器（验证 `query-my-account` 能返回积分）。
- [ ] 本地 `git init`，按本脚手架建立仓库骨架，提交 README 初版。
- [ ] 跑通 `python -m mcd_asset_assistant --demo`（离线报告已验证可用）。
- [ ] 实装 `adapter.py` 真实握手 + `collector.collect_profile()`，本地 `--query` 出真实报告。
- [ ]  milestone：能生成一份真实「麦门资产报告」。

## Day 2（10-23）：做厚优化 + 监控 + 报告美化

- [ ] `optimizer` 增强：积分临期分级提醒、券组合省钱建议、订单洞察。
- [ ] `monitor` 实装：新券 / 活动 / 临期积分告警，验证限流友好。
- [ ] `report` 美化：高颜值分享卡片（HTML）+ 截图用于 README。
- [ ] 在 WorkBuddy 里用对话把 Skill 跑顺，导出对话到 `workbuddy.md`。

## Day 3（10-24 ~ 10-25）：提交 + 拉 Star

- [ ] 补齐 5 个标准文件：`README.md` / `CONTEST_DECLARATION.md`（官方原文）/ `MCP_INTEGRATION.md` / `mcp-config.example.json` / `workbuddy.md`。
- [ ] 写清 `SKILL.md`，让别人能一键复现。
- [ ] 多平台发开发实录（掘金 / V2EX / 朋友圈），README 放真实演示 GIF + 3 行命令跑起来。
- [ ] **10-25 23:59 前** 通过官方 Issue 模板提交（注意：标题与正文间、项目简介内暂不用换行；项目地址不用 Markdown 链接）。
- [ ] 提交后持续互动涨 Star（排行榜快照 10-26 00:00 定榜）。

## 风险与兜底

- 真实 MCP 字段若与 `collector.py` 假设不同 → 集中在 `collector.py` 校准映射，不影响上层。
- 若 Token/网络受限无法本地实跑 → 至少保证 `--demo` 可用 + `MCP_INTEGRATION.md` 写明真实工具，WorkBuddy 内用对话跑通即满足「真实使用 MCP」要求。
- 时间紧时优先：能跑的 demo + 完整 5 文件 + 早提交，而非功能完美。
