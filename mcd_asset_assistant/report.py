"""报告层：把分析结果渲染为可分享的「麦门资产报告」。

支持三种产物：
  - markdown：GitHub README / 聊天框直接贴
  - html    ：独立网页报告
  - card_html：社交分享用的高颜值卡片（利于传播 → 拉 Star）
"""
from __future__ import annotations

from . import optimizer as opt


def build_report(profile: dict) -> dict:
    pts = opt.analyze_points(profile)
    cps = opt.optimize_coupons(profile)
    ins = opt.order_insights(profile)

    md_lines = [
        "# 🍔 麦门资产报告",
        f"> 生成时间：{profile.get('generated_at', '')}　数据源：{profile.get('source', '')}",
        "",
        "## 一、积分资产",
        f"- 可用积分：**{pts['available']}**　累计：{pts['accumulated']}　冻结：{pts['frozen']}",
        f"- 即将过期：**{pts['expiring']}** 分（{pts['expiring_date'] or '未知'}）",
        f"- {pts['alert']}",
    ]
    for s in pts["suggestions"]:
        md_lines.append(f"  - 💡 {s}")
    md_lines += [
        "",
        "## 二、优惠券",
        f"- 名下券合计价值约 ¥{cps['total_value']}",
    ]
    for p in cps["plan"]:
        md_lines.append(f"  - {p}")
    md_lines += [
        "",
        "## 三、消费洞察",
        f"- {ins['note']}",
        "",
        "## 四、下一步行动",
        "1. 先处理临期积分与临期券，避免无偿作废。",
        "2. 大额订单优先叠加高价值券。",
        "3. 关注麦麦省新券与本月活动，主动领取。",
        "",
        "---",
        "_由「麦门资产助手」生成 · 麦当劳程序员节创意开发大赛作品 · 非官方产品_",
    ]
    markdown = "\n".join(md_lines)

    card_html = f"""
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:420px;margin:0 auto;
            border-radius:18px;padding:24px;background:linear-gradient(135deg,#ffd200,#ff8a00);color:#3a2a00;
            box-shadow:0 10px 30px rgba(0,0,0,.15)">
  <div style="font-size:20px;font-weight:800">🍔 我的麦门资产</div>
  <div style="margin-top:14px;font-size:34px;font-weight:900">{pts['available']} <span style="font-size:16px">可用积分</span></div>
  <div style="margin-top:6px;opacity:.85">{pts['alert']}</div>
  <div style="margin-top:14px;background:rgba(255,255,255,.7);border-radius:12px;padding:12px">
    <div>🎟️ 优惠券价值约 ¥{cps['total_value']}</div>
    <div>🧾 近 {ins['count']} 笔订单累计 ¥{ins['total_spend']}</div>
  </div>
  <div style="margin-top:12px;font-size:12px;opacity:.7">麦门资产助手 · 非官方作品</div>
</div>"""

    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>麦门资产报告</title></head><body style="background:#fff8e6;padding:24px">
<h1>🍔 麦门资产报告</h1>
<pre style="background:#fff;padding:16px;border-radius:10px;overflow:auto">{markdown}</pre>
<h2>分享卡片</h2>
{card_html}
</body></html>"""

    return {"markdown": markdown, "html": html, "card_html": card_html}
