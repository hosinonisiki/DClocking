"""Bounded, real-loopback HTTP tests; no FPGA, Qt, LLM or external service."""

from __future__ import annotations

import asyncio
import json
import socket
import unittest
from urllib.parse import quote

import anyio
import httpx2
import uvicorn
from mcp.client import Client
from mcp.client.streamable_http import streamable_http_client

from FPGA_Agent import mcp_server


class MCPHTTPEndToEndTests(unittest.IsolatedAsyncioTestCase):
    """Use the production app/security settings through an actual TCP listener."""

    async def asyncSetUp(self):
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.addCleanup(self.listener.close)
        port = self.listener.getsockname()[1]
        self.url = f"http://127.0.0.1:{port}/mcp"
        self.token = "local-test-only-not-a-user-secret-123456789"
        server = mcp_server.create_mcp_server(
            http_token=self.token, resource_server_url=self.url
        )
        app = server.streamable_http_app(
            host="127.0.0.1",
            transport_security=mcp_server._transport_security_settings("127.0.0.1", port),
            max_request_body_size=mcp_server.HTTP_MAX_REQUEST_BODY_SIZE,
            max_sessions=mcp_server.HTTP_MAX_SESSIONS,
            session_idle_timeout=mcp_server.HTTP_SESSION_IDLE_TIMEOUT,
        )
        self.http_server = uvicorn.Server(
            uvicorn.Config(app, log_level="error", lifespan="on", timeout_graceful_shutdown=2)
        )
        self.server_task = asyncio.create_task(self.http_server.serve(sockets=[self.listener]))
        self.addAsyncCleanup(self._stop_server)

        async def wait_until_started():
            while not self.http_server.started:
                if self.server_task.done():
                    await self.server_task
                    self.fail("HTTP server exited before becoming ready")
                await asyncio.sleep(0.01)

        await asyncio.wait_for(wait_until_started(), timeout=10)

    async def _stop_server(self):
        self.http_server.should_exit = True
        try:
            await asyncio.wait_for(self.server_task, timeout=5)
        finally:
            if not self.server_task.done():
                self.server_task.cancel()

    async def _exercise_client(self, mode):
        requests = []
        responses = []

        async def record_request(request):
            method = None
            if request.method == "POST":
                method = json.loads(request.content).get("method")
            requests.append((request.method, method))

        async def record_response(response):
            responses.append((response.request.method, response.status_code,
                              response.headers.get("mcp-session-id")))

        with anyio.fail_after(15):
            async with httpx2.AsyncClient(
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5,
                trust_env=False,
                event_hooks={"request": [record_request], "response": [record_response]},
            ) as http:
                transport = streamable_http_client(self.url, http_client=http)
                async with Client(transport, mode=mode, read_timeout_seconds=5) as client:
                    self.assertEqual(client.server_info.name, "dclocking-local")
                    tools = await client.list_tools()
                    self.assertEqual(len(tools.tools), 5)
                    self.assertTrue(all(tool.annotations.read_only_hint for tool in tools.tools))
                    catalog = await client.call_tool("list_module_types", {})
                    self.assertGreater(catalog.structured_content["count"], 0)
                    pdh = await client.call_tool("get_module_spec", {"module_type": "PDH状态机"})
                    self.assertFalse(pdh.is_error)
                    self.assertEqual(pdh.structured_content["module"]["module_type"], "PDH状态机")
                    valid = await client.call_tool("validate_parameters", {
                        "module_type": "PDH状态机", "parameters": {"pc_cmd": 1}
                    })
                    invalid = await client.call_tool("validate_parameters", {
                        "module_type": "PDH状态机", "parameters": {"pc_cmd": 99}
                    })
                    self.assertTrue(valid.structured_content["ok"])
                    self.assertFalse(invalid.structured_content["ok"])
                    connection = await client.call_tool("validate_connection", {
                        "source_module": "三角函数运算器", "source_port": "SIN",
                        "destination_module": "混频器", "destination_port": "IN_A",
                    })
                    self.assertTrue(connection.structured_content["ok"])
                    valid_design = await client.call_tool("validate_design", {
                        "design": {"nodes": [{"id": "pdh", "module_type": "PDH状态机"}],
                                   "connections": []}
                    })
                    invalid_design = await client.call_tool("validate_design", {
                        "design": {"nodes": [{"id": "bad", "module_type": "unknown"}],
                                   "connections": []}
                    })
                    self.assertTrue(valid_design.structured_content["ok"])
                    self.assertFalse(invalid_design.structured_content["ok"])
                    resources = await client.list_resources()
                    self.assertIn("dclocking://project/info", [str(r.uri) for r in resources.resources])
                    templates = await client.list_resource_templates()
                    self.assertEqual(templates.resource_templates[0].uri_template,
                                     "dclocking://modules/{module_type}")
                    info = await client.read_resource("dclocking://project/info")
                    self.assertEqual(json.loads(info.contents[0].text)["access"], "read-only")
                    spec = await client.read_resource("dclocking://modules/" + quote("PDH状态机"))
                    self.assertTrue(json.loads(spec.contents[0].text)["ok"])
                    denied = await client.call_tool("write_hardware_register", {})
                    self.assertTrue(denied.is_error)
                    protocol = client.protocol_version

                if mode == "legacy":
                    self.assertIn(("POST", "initialize"), requests)
                    self.assertIn(("POST", "notifications/initialized"), requests)
                    self.assertTrue(any(method == "DELETE" and status in (200, 204)
                                        for method, status, _ in responses), responses)
                    session_id = next(session for _, _, session in responses if session)
                    # A successfully closed session cannot be reused by accident.
                    closed = await http.post(self.url, headers={
                        "mcp-session-id": session_id, "MCP-Protocol-Version": protocol,
                        "Accept": "application/json, text/event-stream",
                    }, json={"jsonrpc": "2.0", "id": 999, "method": "tools/list", "params": {}})
                    self.assertEqual(closed.status_code, 404)
                else:
                    self.assertIn(("POST", "server/discover"), requests)

    async def test_classic_initialize_call_resource_and_session_termination(self):
        await self._exercise_client("legacy")

    async def test_modern_discovery_call_resource_and_client_close(self):
        await self._exercise_client("auto")

    async def test_network_rejects_missing_wrong_token_host_origin_and_large_body(self):
        with anyio.fail_after(10):
            async with httpx2.AsyncClient(timeout=3, trust_env=False) as http:
                for auth in (None, "Bearer wrong-token"):
                    headers = {} if auth is None else {"Authorization": auth}
                    result = await http.get(self.url, headers=headers)
                    self.assertEqual(result.status_code, 401)
                auth = {"Authorization": f"Bearer {self.token}"}
                for extra, expected in (({"Host": "evil.invalid"}, 421),
                                        ({"Origin": "http://evil.invalid"}, 403)):
                    with self.assertLogs("mcp.server.transport_security", level="WARNING"):
                        result = await http.get(self.url, headers={**auth, **extra})
                    self.assertEqual(result.status_code, expected)
                oversized = await http.post(self.url, headers=auth,
                                            content=b" " * (mcp_server.HTTP_MAX_REQUEST_BODY_SIZE + 1))
                self.assertEqual(oversized.status_code, 413)


if __name__ == "__main__":
    unittest.main()
