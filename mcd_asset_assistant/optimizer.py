"""优化层：把"资产数据"转换成"可执行建议"。

纯函数，只依赖 profile 结构，不触碰 MCP。便于单测与复用。
"""
from __future__ import annotations

import datetime as _dt


def _days_left(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        d = _dt.date.fromisoformat(str(date_str)[:10])
        return (d - _dt.date.today()).days
    except ValueError:
        return None


def analyze_points(profile: dict) -> dict:
    acc = profile.get("account", {})
    expiring = acc.get("expiring", 0)
    exp_date = acc.get("expiring_date")
    days = _days_left(exp_date)
    alert = ""
    if expiring:
        if days is not None:
            if days <= 0:
                alert = f"⚠️ 有 {expiring} 积分已过期作废！"
            elif days <= 15:
                alert = f"⏰ {expiring} 积分将在 {days} 天后（{exp_date}）过期，建议尽快使用。"
            else:
                alert = f"✅ {expiring} 积分将于 {exp_date} 过期，尚有余量。"
        else:
            alert = f"⏰ 有 {expiring} 积分即将过期，建议尽快使用。"
    else:
        alert = "✅ 当前没有即将过期的积分，可安心累积。"
    # 处置建议：优先用掉临期积分
    mall = profile.get("mall_products", [])
    lottery = profile.get("lottery", {})
    suggestions = []
    if expiring:
        if any(p.get("points", 0) <= expiring for p in mall):
            cheap = min((p for p in mall if p.get("points", 0) <= expiring), key=lambda p: p["points"])
            suggestions.append(f"用临期积分兑换「{cheap['name']}」（{cheap['points']} 分），不浪费。")
        if lottery.get("active"):
            suggestions.append("参与当前积分抽奖，把临期积分转化为抽奖机会。")
    return {
        "available": acc.get("available", 0),
        "accumulated": acc.get("accumulated", 0),
        "frozen": acc.get("frozen", 0),
        "expiring": expiring,
        "expiring_date": exp_date,
        "days_left": days,
        "alert": alert,
        "suggestions": suggestions,
    }


def optimize_coupons(profile: dict) -> dict:
    coupons = profile.get("coupons", [])
    if not coupons:
        return {"total_value": 0, "expiring_soon": [], "plan": ["当前没有可用券。"]}
    total = sum(c.get("value", 0) or 0 for c in coupons)
    expiring_soon = [c for c in coupons if (d := _days_left(c.get("expire"))) is not None and d <= 7]
    plan = [f"名下共 {len(coupons)} 张券，合计价值约 ¥{total}。"]
    if expiring_soon:
        names = "、".join(c["name"] for c in expiring_soon)
        plan.append(f"优先用掉 7 天内过期的：{names}。")
    # 简单组合：高价值券用于高客单价订单
    best = max(coupons, key=lambda c: c.get("value", 0) or 0)
    plan.append(f"大额订单优先叠加「{best['name']}」（¥{best.get('value', 0)}）。")
    return {"total_value": total, "expiring_soon": expiring_soon, "plan": plan}


def order_insights(profile: dict) -> dict:
    orders = profile.get("orders", [])
    if not orders:
        return {"count": 0, "total_spend": 0, "avg": 0, "note": "暂无历史订单。"}
    amounts = [o.get("amount", 0) or 0 for o in orders]
    total = sum(amounts)
    return {
        "count": len(orders),
        "total_spend": total,
        "avg": round(total / len(orders), 1),
        "note": f"近 {len(orders)} 笔订单累计 ¥{total}，均价 ¥{round(total / len(orders), 1)}。",
    }
