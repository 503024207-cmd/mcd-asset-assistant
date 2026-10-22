"""采集层：调用麦当劳 MCP 工具，归一化为统一 profile。

真实工具返回结构可能随版本微调，这里做「尽力解析 + 安全兜底」，
字段映射如需校准，集中在此文件修改即可，不影响上层逻辑。
"""
from __future__ import annotations

import datetime as _dt
from .adapter import McDMCPClient


def _now() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _as_int(v, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def collect_profile(client: McDMCPClient) -> dict:
    """拉取账户 / 券 / 订单等真实数据，返回归一化 profile。"""
    profile: dict = {
        "generated_at": _now(),
        "source": "mcd-mcp (real)",
        "account": {},
        "coupons": [],
        "available_coupons": [],
        "orders": [],
        "mall_products": [],
        "lottery": {},
    }

    # —— 1. 积分账户（核心差异化数据源）——
    try:
        acc = client.call_tool("query-my-account") or {}
        profile["account"] = {
            "available": _as_int(acc.get("availablePoints") or acc.get("available")),
            "accumulated": _as_int(acc.get("totalPoints") or acc.get("accumulated")),
            "frozen": _as_int(acc.get("frozenPoints") or acc.get("frozen")),
            "expiring": _as_int(acc.get("expiringPoints") or acc.get("expiring")),
            "expiring_date": acc.get("expiringDate") or acc.get("expiring_date"),
        }
    except Exception as e:  # noqa: BLE001
        profile["account_error"] = str(e)

    # —— 2. 已有优惠券 ——
    try:
        coupons = client.call_tool("query-my-coupons") or []
        coupons = coupons if isinstance(coupons, list) else coupons.get("list", [])
        profile["coupons"] = [
            {"name": c.get("name", "优惠券"), "value": _as_int(c.get("value")), "expire": c.get("expireDate")}
            for c in coupons
        ]
    except Exception as e:  # noqa: BLE001
        profile["coupons_error"] = str(e)

    # —— 3. 麦麦省可领券 ——
    try:
        avail = client.call_tool("available-coupons") or []
        avail = avail if isinstance(avail, list) else avail.get("list", [])
        profile["available_coupons"] = [{"name": c.get("name", "可领券")} for c in avail]
    except Exception as e:  # noqa: BLE001
        profile["available_coupons_error"] = str(e)

    # —— 4. 历史订单 ——
    try:
        orders = client.call_tool("order-list") or []
        orders = orders if isinstance(orders, list) else orders.get("list", [])
        profile["orders"] = [
            {"date": o.get("orderTime", "")[:10], "amount": _as_int(o.get("totalAmount")), "summary": o.get("summary", "")}
            for o in orders
        ]
    except Exception as e:  # noqa: BLE001
        profile["orders_error"] = str(e)

    # —— 5. 积分商城可兑换商品 ——
    try:
        malls = client.call_tool("mall-points-products") or []
        malls = malls if isinstance(malls, list) else malls.get("list", [])
        profile["mall_products"] = [
            {"name": m.get("name", ""), "points": _as_int(m.get("points"))} for m in malls
        ]
    except Exception as e:  # noqa: BLE001
        profile["mall_products_error"] = str(e)

    # —— 6. 积分抽奖活动 ——
    try:
        lot = client.call_tool("query-lottery-info") or {}
        profile["lottery"] = {
            "active": bool(lot.get("active") or lot.get("status") == "active"),
            "prizes": [p.get("name", "") for p in (lot.get("prizes") or [])],
        }
    except Exception as e:  # noqa: BLE001
        profile["lottery_error"] = str(e)

    return profile
