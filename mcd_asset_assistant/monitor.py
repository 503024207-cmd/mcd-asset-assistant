"""监控层：一次扫描，产出"值得你注意"的提醒。

设计为可定时触发（cron / 云函数），每次只做少量只读调用，
严格遵守 600 次/分钟限流。返回结构化 alerts 列表。
"""
from __future__ import annotations

from .adapter import McDMCPClient


def _as_int(v, default: int = 0) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def scan_once(client: McDMCPClient) -> list[dict]:
    alerts: list[dict] = []

    # 1) 临期积分
    try:
        acc = client.call_tool("query-my-account") or {}
        expiring = _as_int(acc.get("currentMouthExpirePoint") or acc.get("expiringPoints") or acc.get("expiring"))
        if expiring > 0:
            alerts.append({
                "type": "points_expiring",
                "level": "high",
                "text": f"你有 {expiring} 积分即将过期，建议尽快兑换或抽奖。",
            })
    except Exception:  # noqa: BLE001
        pass

    # 2) 新可领券
    try:
        avail = client.call_tool("available-coupons") or []
        avail = avail if isinstance(avail, list) else []
        if avail:
            alerts.append({
                "type": "new_coupons",
                "level": "normal",
                "text": f"麦麦省有 {len(avail)} 张券可一键领取，例如：{avail[0].get('couponName', avail[0].get('name', ''))}。",
            })
    except Exception:  # noqa: BLE001
        pass

    # 3) 当月活动日历
    try:
        cal = client.call_tool("campaign-calendar") or {}
        campaigns = (cal.get("dailyList") or []) + (cal.get("subscribedEvents") or [])
        if campaigns:
            alerts.append({
                "type": "campaign",
                "level": "low",
                "text": f"本月有 {len(campaigns)} 个营销活动进行中，可关注限时优惠。",
            })
    except Exception:  # noqa: BLE001
        pass

    return alerts
