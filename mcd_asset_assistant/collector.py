"""采集层：调用麦当劳 MCP 工具，归一化为统一 profile。

真实工具返回结构（基于实测 query-my-account 等）：
  - 干净数据位于 result.structuredContent.data
  - 字段以麦当劳官方命名（注意 currentMouthExpirePoint 中 Mouth 为官方拼写）
字段映射如需校准，集中在此文件修改即可，不影响上层逻辑。
"""
from __future__ import annotations

import datetime as _dt
import re
from .adapter import McDMCPClient

_PRICE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*元")


def _price_from_text(text: str) -> int:
    """从券标题里提取金额（如「11.9元麦辣鸡腿堡」→ 11）。无则 0。"""
    m = _PRICE_RE.search(text or "")
    return int(float(m.group(1))) if m else 0


def _now() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _as_int(v, default: int = 0) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _as_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _month_end() -> str:
    today = _dt.date.today()
    if today.month == 12:
        nxt = today.replace(year=today.year + 1, month=1, day=1)
    else:
        nxt = today.replace(month=today.month + 1, day=1)
    return (nxt - _dt.timedelta(days=1)).isoformat()


def _list_from(data, key=None):
    """从工具返回里稳健地取出列表：支持直接返回 list，或 dict 里某个 key 为 list。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if key and key in data and isinstance(data[key], list):
            return data[key]
        for v in data.values():
            if isinstance(v, list):
                return v
    return []


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
        expiring = _as_int(
            acc.get("currentMouthExpirePoint") or acc.get("expiringPoints") or acc.get("expiring")
        )
        exp_date = acc.get("expiringDate") or acc.get("expiring_date")
        if expiring and not exp_date:
            exp_date = _month_end()  # “本月过期”推断为月底前
        profile["account"] = {
            "available": _as_int(acc.get("availablePoint") or acc.get("available")),
            "accumulated": _as_int(
                acc.get("accumulativePoint") or acc.get("totalPoints") or acc.get("accumulated")
            ),
            "frozen": _as_int(acc.get("frozenPoint") or acc.get("frozen")),
            "expiring": expiring,
            "expiring_next": _as_int(acc.get("nextMouthExpirePoint") or acc.get("nextMonthExpirePoint")),
            "expired": _as_int(acc.get("expiredPoint") or acc.get("expired")),
            "used": _as_int(acc.get("usedPoint") or acc.get("used")),
            "expiring_date": exp_date,
        }
    except Exception as e:  # noqa: BLE001
        profile["account_error"] = str(e)

    # —— 2. 已有优惠券 ——
    try:
        coupons = client.call_tool("query-my-coupons") or {}
        coupons = _list_from(coupons, "coupons")
        profile["coupons"] = [
            {
                "name": c.get("title", c.get("name", "优惠券")),
                "value": _as_int(c.get("reducePrice") or c.get("reducePriceText")) or _price_from_text(c.get("title", "")),
                "expire": c.get("tradeEndDate") or c.get("tradeEndDateTime") or c.get("expireDate"),
            }
            for c in coupons
        ]
    except Exception as e:  # noqa: BLE001
        profile["coupons_error"] = str(e)

    # —— 3. 麦麦省可领券 ——
    try:
        avail = client.call_tool("available-coupons") or []
        avail = _list_from(avail)
        profile["available_coupons"] = [
            {"name": c.get("couponName", c.get("name", "可领券"))} for c in avail
        ]
    except Exception as e:  # noqa: BLE001
        profile["available_coupons_error"] = str(e)

    # —— 4. 历史订单 ——
    try:
        orders = client.call_tool("order-list") or {}
        orders = _list_from(orders, "list")
        profile["orders"] = [
            {
                "date": (o.get("createTime") or o.get("orderTime") or "")[:10],
                "amount": _as_float(o.get("realTotalAmount") or o.get("totalAmount") or o.get("amount")),
                "summary": o.get("storeName", o.get("summary", "")),
            }
            for o in orders
        ]
    except Exception as e:  # noqa: BLE001
        profile["orders_error"] = str(e)

    # —— 5. 积分商城可兑换商品 ——
    try:
        malls = client.call_tool("mall-points-products") or []
        malls = _list_from(malls)
        profile["mall_products"] = [
            {"name": m.get("spuName", m.get("name", "")), "points": _as_int(m.get("point") or m.get("points"))}
            for m in malls
        ]
    except Exception as e:  # noqa: BLE001
        profile["mall_products_error"] = str(e)

    # —— 6. 积分抽奖活动 ——
    try:
        lot = client.call_tool("query-lottery-info") or {}
        if isinstance(lot, dict):
            prizes = _list_from(lot, "prizes")
            profile["lottery"] = {
                "active": bool(lot.get("status") or lot.get("activityStatusText") or lot.get("active")),
                "name": lot.get("activityName", ""),
                "prizes": [p.get("name", "") for p in prizes],
            }
        else:
            profile["lottery"] = {"active": False, "prizes": []}
    except Exception as e:  # noqa: BLE001
        profile["lottery_error"] = str(e)

    return profile
