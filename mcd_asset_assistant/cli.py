"""CLI 入口：三件事 —— 查询 / 监控 / 演示。

用法：
  python -m mcd_asset_assistant --demo            # 离线演示（无需 Token）
  python -m mcd_asset_assistant --query           # 真实拉取并生成报告
  python -m mcd_asset_assistant --monitor         # 一次监控扫描
  --format md|html|card                            # 报告格式（默认 md）
  --out report.md                                  # 可选：写入文件
"""
from __future__ import annotations

import argparse
import sys

from . import monitor as mon
from .adapter import McDMCPClient
from .collector import collect_profile
from .mock_data import build_profile
from .report import build_report


def _emit(text: str, out: str | None):
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已写入：{out}")
    else:
        print(text)


def main(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description="麦门资产助手 CLI")
    p.add_argument("--demo", action="store_true", help="使用 mock 数据离线演示")
    p.add_argument("--query", action="store_true", help="连接麦当劳 MCP 拉取真实数据并生成报告")
    p.add_argument("--monitor", action="store_true", help="执行一次监控扫描")
    p.add_argument("--format", choices=["md", "html", "card"], default="md")
    p.add_argument("--out", help="将结果写入文件（可选）")
    args = p.parse_args(argv)

    if args.demo:
        profile = build_profile()
        rep = build_report(profile)
        payload = {"md": rep["markdown"], "html": rep["html"], "card": rep["card_html"]}[args.format]
        _emit(payload, args.out)
        return

    if args.monitor:
        try:
            client = McDMCPClient()
        except RuntimeError as e:
            print(f"❌ {e}")
            sys.exit(1)
        alerts = mon.scan_once(client)
        lines = ["# 🔔 麦门资产监控", ""] + [f"- [{a['level']}] {a['text']}" for a in alerts] or ["- 暂无提醒"]
        _emit("\n".join(lines), args.out)
        return

    if args.query:
        try:
            client = McDMCPClient()
        except RuntimeError as e:
            print(f"❌ {e}")
            sys.exit(1)
        profile = collect_profile(client)
        rep = build_report(profile)
        payload = {"md": rep["markdown"], "html": rep["html"], "card": rep["card_html"]}[args.format]
        _emit(payload, args.out)
        return

    p.print_help()


if __name__ == "__main__":
    main()
