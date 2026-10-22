"""麦当劳 MCP 适配器（数据源适配层）。

把"麦当劳 MCP"这一具体数据源隔离在 adapter 层。上层 optimizer / monitor /
report 只依赖结构化数据，不关心传输细节。未来接入星巴克 / 航司等其它积分
体系时，只需新增一个实现同一接口的 adapter。
"""
from __future__ import annotations

import os
import json
import time
import requests

MCD_MCP_URL = os.getenv("MCD_MCP_URL", "https://mcp.mcd.cn")
MCD_MCP_TOKEN = os.getenv("MCD_MCP_TOKEN", "")


class McDMCPClient:
    """最小可用的麦当劳 MCP (Streamable HTTP) 客户端。"""

    def __init__(self, token: str | None = None, url: str | None = None, timeout: int = 30):
        self.url = url or MCD_MCP_URL
        self.token = token or MCD_MCP_TOKEN
        if not self.token:
            raise RuntimeError("缺少 MCD_MCP_TOKEN，请在环境变量中配置麦当劳 MCP Token。")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        })
        self.session_id: str | None = None
        self._initialize()

    def _post(self, payload: dict, with_session: bool = True) -> dict:
        headers: dict[str, str] = {}
        if with_session and self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        resp = self.session.post(self.url, json=payload, headers=headers, timeout=30)
        if sid := resp.headers.get("Mcp-Session-Id"):
            self.session_id = sid
        return self._parse(resp)

    @staticmethod
    def _parse(resp) -> dict:
        text = resp.text
        if "data:" in text:
            for line in text.splitlines():
                if line.startswith("data:"):
                    frag = line[len("data:"):].strip()
                    try:
                        return json.loads(frag)
                    except json.JSONDecodeError:
                        continue
        try:
            return resp.json()
        except Exception:
            return {"raw": text}

    def _initialize(self):
        init = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcd-asset-assistant", "version": "0.1.0"},
            },
        }
        self._post(init, with_session=False)
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, with_session=True)

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        payload = {
            "jsonrpc": "2.0", "id": int(time.time() * 1000),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
        res = self._post(payload)
        # MCP tool 结果通常包在 result.content[].text（JSON 字符串）中
        result = res.get("result", res)
        content = result.get("content") if isinstance(result, dict) else None
        if isinstance(content, list) and content:
            text = content[0].get("text", "")
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return {"text": text}
        return result
