"""Mock 数据层：无需 Token / 网络即可生成一份逼真的资产档案。

用于：
  - README 的离线演示（python -m mcd_asset_assistant --demo）
  - 用户无需接入麦当劳账号即可看到「资产报告」长什么样 → 利于传播与 Star
"""
from __future__ import annotations

import datetime as _dt


def build_profile() -> dict:
    today = _dt.date.today()
    expiring_date = (today + _dt.timedelta(days=12)).isoformat()
    return {
        "generated_at": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "mock (demo)",
        "account": {
            "available": 3280,
            "accumulated": 9120,
            "frozen": 0,
            "expiring": 1500,
            "expiring_date": expiring_date,
        },
        "coupons": [
            {"name": "麦辣鸡腿堡买一送一", "value": 22, "expire": (today + _dt.timedelta(days=3)).isoformat()},
            {"name": "满40减8 通用券", "value": 8, "expire": (today + _dt.timedelta(days=9)).isoformat()},
            {"name": "薯条中份立减5", "value": 5, "expire": (today + _dt.timedelta(days=20)).isoformat()},
        ],
        "available_coupons": [
            {"name": "麦麦省·指定套餐减10"},
            {"name": "麦麦省·免费升杯"},
        ],
        "orders": [
            {"date": "2026-10-18", "amount": 39, "summary": "麦辣鸡腿堡套餐 + 可乐"},
            {"date": "2026-10-12", "amount": 52, "summary": "双人分享盒"},
            {"date": "2026-10-05", "amount": 27, "summary": "1+1 随心配"},
        ],
        "mall_products": [
            {"name": "麦当劳保温杯", "points": 4800},
            {"name": "巨无霸兑换券", "points": 1500},
            {"name": "麦麦公仔", "points": 2200},
        ],
        "lottery": {"active": True, "prizes": ["1000积分", "巨无霸券", "谢谢参与"]},
    }
