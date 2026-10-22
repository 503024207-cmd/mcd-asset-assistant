"""麦门资产助手 · 轻量后端（零第三方依赖，只用 Python 标准库）

为什么需要后端？
    麦当劳 MCP (https://mcp.mcd.cn) 未开放 CORS，浏览器无法直接调用，
    必须由服务端转发。前端只负责展示与交互，Token 由用户粘贴、
    仅在本次请求的 header 中透传，服务端不落盘、不写日志。

接口：
    GET  /                 → 前端页面
    GET  /api/health       → 探活
    POST /api/asset-report → body: {"token": "<MCP_TOKEN>"}
        服务端用该 token 调麦当劳 MCP 的只读工具，返回归一化的资产档案。

运行：
    python demo/server.py            # 默认 http://127.0.0.1:8899
    PORT=8080 python demo/server.py   # 指定端口（发布到线上时用 PORT）
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MCD_MCP_URL = os.getenv("MCD_MCP_URL", "https://mcp.mcd.cn")
HERE = Path(__file__).resolve().parent

# 只读工具白名单：绝不调用下单 / 抽奖 / 领券等写操作
READONLY_TOOLS = {
    "query-my-account",
    "query-my-coupons",
    "available-coupons",
    "order-list",
    "mall-points-products",
    "query-lottery-info",
    "campaign-calendar",
}


# --------------------------------------------------------------------------
# MCP 客户端（Streamable HTTP）
# --------------------------------------------------------------------------
def mcp_call(token: str, tool: str, arguments: dict | None = None, timeout: int = 25):
    """调用一个 MCP 工具，返回 structuredContent.data（干净结构化数据）。"""
    if tool not in READONLY_TOOLS:
        raise PermissionError(f"工具 {tool} 不在只读白名单内，已拒绝调用")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments or {}},
    }
    req = urllib.request.Request(
        MCD_MCP_URL, data=json.dumps(payload).encode("utf-8"), method="POST"
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", "replace")

    # Streamable HTTP 可能返回 SSE 片段
    if "data:" in raw:
        for line in raw.splitlines():
            if line.startswith("data:"):
                frag = line[len("data:"):].strip()
                try:
                    raw = frag
                    break
                except Exception:
                    continue
    obj = json.loads(raw)
    if "error" in obj:
        raise RuntimeError(obj["error"].get("message") or "MCP 返回错误")
    result = obj.get("result", obj)
    sc = result.get("structuredContent")
    if isinstance(sc, dict):
        data = sc.get("data")
        if isinstance(data, (dict, list)):
            return data
        return sc
    content = result.get("content")
    if isinstance(content, list) and content:
        text = content[0].get("text", "")
        try:
            return json.loads(text)
        except Exception:
            return {"text": text}
    return result


# --------------------------------------------------------------------------
# 归一化：把麦当劳的官方字段转成前端要的形状
# --------------------------------------------------------------------------
def _num(v, default=0):
    """积分等字段可能返回字符串 "0"，必须转数值再判断。"""
    try:
        if v is None or v == "":
            return default
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _amount_from_title(title: str) -> float:
    """券没有数值字段时，从券名解析金额，如「11.9元麦辣鸡腿堡」→ 11.9。"""
    import re

    m = re.search(r"(\d+(?:\.\d+)?)\s*元", title or "")
    return float(m.group(1)) if m else 0.0


def _days_left(date_str: str):
    import datetime as dt

    if not date_str:
        return None
    s = str(date_str).strip().replace("/", "-")
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y%m%d"):
        try:
            d = dt.datetime.strptime(s[: len(fmt) + 6], fmt).date()
            return (d - dt.date.today()).days
        except ValueError:
            continue
    return None


def build_profile(token: str) -> dict:
    """调用只读工具，产出归一化的资产档案。"""
    # 1) 积分
    acc = mcp_call(token, "query-my-account") or {}
    if not isinstance(acc, dict):
        acc = {}
    account = {
        "available": _num(acc.get("availablePoint")),
        "accumulated": _num(acc.get("accumulativePoint")),
        "frozen": _num(acc.get("frozenPoint")),
        "expiring": _num(acc.get("currentMouthExpirePoint")),
        "next_expiring": _num(acc.get("nextMouthExpirePoint")),
        "expired": _num(acc.get("expiredPoint")),
    }

    # 2) 我的券
    coupons = []
    try:
        cdata = mcp_call(token, "query-my-coupons") or {}
        items = cdata.get("coupons") if isinstance(cdata, dict) else cdata
        for c in (items or []):
            if not isinstance(c, dict):
                continue
            title = c.get("title") or c.get("couponName") or ""
            value = _num(c.get("reducePrice") or c.get("reducePriceText"), 0)
            if not value:
                value = _amount_from_title(title)
            end = c.get("tradeEndDate") or c.get("tradeEndDateTime") or ""
            coupons.append({
                "name": title,
                "value": float(value),
                "expire": str(end)[:10],
                "days_left": _days_left(end),
            })
    except Exception as e:
        coupons = []
        coupon_error = str(e)
    else:
        coupon_error = ""

    # 3) 可领券（只要名字，作为「监控」信息）
    available = []
    try:
        adata = mcp_call(token, "available-coupons") or []
        for a in (adata if isinstance(adata, list) else []):
            if isinstance(a, dict):
                name = a.get("couponName") or a.get("title") or ""
                if name:
                    available.append(name)
    except Exception:
        pass

    # 4) 订单
    orders = []
    total = 0.0
    try:
        odata = mcp_call(token, "order-list") or {}
        items = odata.get("list") if isinstance(odata, dict) else odata
        for o in (items or []):
            if not isinstance(o, dict):
                continue
            amt = o.get("realTotalAmount")
            try:
                amt = float(amt)
            except (TypeError, ValueError):
                amt = 0.0
            total += amt
            orders.append({
                "date": str(o.get("createTime") or "")[:10],
                "amount": amt,
                "summary": o.get("storeName") or o.get("orderType") or "",
            })
    except Exception:
        pass

    return {
        "account": account,
        "coupons": coupons,
        "available_coupons": available,
        "orders": orders,
        "order_total": round(total, 2),
        "order_count": len(orders),
        "coupon_error": coupon_error,
    }


# --------------------------------------------------------------------------
# HTTP 处理
# --------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "McdAssetAssistant/1.0"

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, code: int, obj: dict):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            try:
                html = (HERE / "index.html").read_bytes()
            except OSError:
                self._json(500, {"error": "index.html 缺失"})
                return
            self._send(200, html, "text/html; charset=utf-8")
        elif path == "/api/health":
            self._json(200, {"ok": True, "mcp": MCD_MCP_URL})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path.split("?")[0] != "/api/asset-report":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self._json(400, {"error": "请求体不是合法 JSON"})
            return

        token = (payload.get("token") or "").strip()
        if not token:
            self._json(400, {"error": "缺少 token：请先粘贴你的麦当劳 MCP Token"})
            return
        if len(token) < 10:
            self._json(400, {"error": "token 格式不正确，请检查是否完整粘贴"})
            return

        try:
            profile = build_profile(token)
        except urllib.error.HTTPError as e:
            code = e.code
            if code in (401, 403):
                self._json(401, {"error": "Token 无效或已过期，请到 open.mcd.cn/mcp 重新获取"})
            else:
                self._json(502, {"error": f"麦当劳 MCP 返回 {code}，请稍后重试"})
            return
        except urllib.error.URLError:
            self._json(502, {"error": "无法连接麦当劳 MCP，请检查网络"})
            return
        except Exception as e:
            self._json(500, {"error": f"查询失败：{e}"})
            return

        profile["source"] = "mcd-mcp (real)"
        self._json(200, profile)

    def log_message(self, fmt, *args):
        # 静默访问日志，避免把请求内容写进日志
        pass


def main():
    port = int(os.getenv("PORT") or 8899)
    host = os.getenv("HOST") or "0.0.0.0"
    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"🍔 麦门资产助手 → http://127.0.0.1:{port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
