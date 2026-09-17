"""Protocol-level tests for the local DClocking MCP server."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

from mcp import StdioServerParameters
from mcp.client import Client

from FPGA_Agent import mcp_server
from FPGA_Agent.mcp_server import create_mcp_server


class _RecordingCatalogService:
    """Small service double that keeps protocol tests independent of the registry."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    def _return(self, operation: str, *args, **kwargs) -> dict:
        self.calls.append((operation, args, kwargs))
        return {"ok": True, "operation": operation, "args": list(args), "kwargs": kwargs}

    def list_module_types(self, category=None) -> dict:
        return self._return("list_module_types", category)

    def get_module_spec(self, module_type: str) -> dict:
        return self._return("get_module_spec", module_type)

    def validate_parameters(self, module_type: str, parameters: dict) -> dict:
        return self._return("validate_parameters", module_type, parameters)

    def validate_connection(
        self,
        source_module: str,
        source_port: str | int,
        destination_module: str,
        destination_port: str | int,
        developer_mode: bool = False,
    ) -> dict:
        return self._return(
            "validate_connection",
            source_module,
            source_port,
            destination_module,
            destination_port,
            developer_mode,
        )

    def validate_design(self, design: dict) -> dict:
        return self._return("validate_design", design)


def _tool_result_json(result) -> dict:
    assert result.is_error is False
    assert len(result.content) == 1
    return json.loads(result.content[0].text)


async def _asgi_get_status(app, headers: list[tuple[bytes, bytes]]) -> int:
    sent: list[dict] = []
    request_delivered = False

    async def receive() -> dict:
        nonlocal request_delivered
        if not request_delivered:
            request_delivered = True
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/mcp",
        "raw_path": b"/mcp",
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "client": ("127.0.0.1", 50000),
        "server": ("127.0.0.2", 8765),
        "state": {},
    }
    await app(scope, receive, send)
    return next(message["status"] for message in sent if message["type"] == "http.response.start")


class MCPServerProtocolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.service = _RecordingCatalogService()
        self.server = create_mcp_server(self.service)

    async def test_discovers_exact_read_only_tool_surface(self):
        async with Client(self.server, raise_exceptions=True) as client:
            result = await client.list_tools()
        self.assertEqual(
            {tool.name for tool in result.tools},
            {
                "list_module_types",
                "get_module_spec",
                "validate_parameters",
                "validate_connection",
                "validate_design",
            },
        )

        by_name = {tool.name: tool for tool in result.tools}
        self.assertEqual(
            by_name["validate_connection"].input_schema["properties"]["developer_mode"][
                "default"
            ],
            False,
        )

    async def test_tools_forward_typed_arguments_and_return_json(self):
        cases = [
            ("list_module_types", {"category": "filter"}, "list_module_types"),
            ("get_module_spec", {"module_type": "PID控制器"}, "get_module_spec"),
            (
                "validate_parameters",
                {"module_type": "PID控制器", "parameters": {"gain_p": 3}},
                "validate_parameters",
            ),
            (
                "validate_connection",
                {
                    "source_module": "三角函数运算器",
                    "source_port": "SIN",
                    "destination_module": "混频器",
                    "destination_port": 0,
                    "developer_mode": True,
                },
                "validate_connection",
            ),
            (
                "validate_design",
                {"design": {"nodes": [], "connections": []}},
                "validate_design",
            ),
        ]

        async with Client(self.server, raise_exceptions=True) as client:
            for tool_name, arguments, expected_operation in cases:
                with self.subTest(tool_name=tool_name):
                    result = await client.call_tool(tool_name, arguments)
                    payload = _tool_result_json(result)
                    self.assertTrue(payload["ok"])
                    self.assertEqual(payload["operation"], expected_operation)

    async def test_unknown_tool_is_rejected_by_protocol(self):
        async with Client(self.server, raise_exceptions=True) as client:
            result = await client.call_tool("write_hardware_register", {})

        self.assertTrue(result.is_error)
        self.assertIn("Unknown tool", result.content[0].text)
        self.assertEqual(self.service.calls, [])

    async def test_protocol_does_not_coerce_ports_or_developer_mode(self):
        invalid_calls = (
            {
                "source_module": "三角函数运算器",
                "source_port": True,
                "destination_module": "混频器",
                "destination_port": 0,
            },
            {
                "source_module": "三角函数运算器",
                "source_port": 0,
                "destination_module": "混频器",
                "destination_port": 0,
                "developer_mode": 1,
            },
            {
                "source_module": "三角函数运算器",
                "source_port": 0,
                "destination_module": "混频器",
                "destination_port": 0,
                "developer_mode": "yes",
            },
        )

        async with Client(self.server, raise_exceptions=True) as client:
            for arguments in invalid_calls:
                with self.subTest(arguments=arguments):
                    result = await client.call_tool(
                        "validate_connection", arguments
                    )
                    self.assertTrue(result.is_error)

        self.assertEqual(self.service.calls, [])

    async def test_discovers_and_reads_json_resources(self):
        async with Client(self.server, raise_exceptions=True) as client:
            resources = await client.list_resources()
            self.assertEqual(
                {str(resource.uri) for resource in resources.resources},
                {"dclocking://project/info", "dclocking://modules/catalog"},
            )
            self.assertTrue(
                all(
                    resource.mime_type == "application/json"
                    for resource in resources.resources
                )
            )

            templates = await client.list_resource_templates()
            self.assertEqual(
                {template.uri_template for template in templates.resource_templates},
                {"dclocking://modules/{module_type}"},
            )

            project = await client.read_resource("dclocking://project/info")
            project_payload = json.loads(project.contents[0].text)
            self.assertEqual(project_payload["name"], "DClocking")
            self.assertEqual(project_payload["access"], "read-only")

            catalog = await client.read_resource("dclocking://modules/catalog")
            catalog_payload = json.loads(catalog.contents[0].text)
            self.assertEqual(catalog_payload["operation"], "list_module_types")

            module = await client.read_resource(
                "dclocking://modules/%E7%B4%AF%E5%8A%A0%E5%99%A8"
            )
            module_payload = json.loads(module.contents[0].text)
            self.assertEqual(module_payload["operation"], "get_module_spec")
            self.assertEqual(module_payload["args"], ["累加器"])

    async def test_unexpected_service_failure_is_sanitized(self):
        def fail(_module_type: str) -> dict:
            raise RuntimeError("secret=/Users/alice/private/key.txt")

        self.service.get_module_spec = fail
        with self.assertLogs("FPGA_Agent.mcp_server", level="ERROR") as logs:
            async with Client(self.server, raise_exceptions=True) as client:
                result = await client.call_tool(
                    "get_module_spec", {"module_type": "PID控制器"}
                )
        payload = _tool_result_json(result)

        self.assertFalse(payload["ok"])
        self.assertEqual(payload["errors"][0]["code"], "internal_error")
        self.assertNotIn("secret", json.dumps(payload))
        self.assertNotIn("/Users/", json.dumps(payload))
        self.assertNotIn("secret", "\n".join(logs.output))
        self.assertNotIn("/Users/", "\n".join(logs.output))

    async def test_real_stdio_subprocess_completes_mcp_handshake(self):
        project_root = Path(__file__).resolve().parent.parent
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "FPGA_Agent.mcp_server"],
            cwd=str(project_root),
            # The SDK intentionally sanitizes an implicit child environment.
            # Preserve the test runner's explicit dependency path so this also
            # works when desktop and MCP dependencies live in separate local
            # environments (as they do in the lightweight launcher setup).
            env=os.environ.copy(),
        )

        async with Client(parameters, raise_exceptions=True) as client:
            tools = await client.list_tools()
            result = await client.call_tool(
                "get_module_spec", {"module_type": "PID控制器"}
            )

        self.assertIn("get_module_spec", {tool.name for tool in tools.tools})
        payload = _tool_result_json(result)
        self.assertTrue(payload["ok"], payload)
        self.assertEqual(payload["module"]["module_type"], "PID控制器")

    async def test_http_app_requires_bearer_token_and_valid_host_and_origin(self):
        token = "a" * 32
        server = create_mcp_server(
            self.service,
            http_token=token,
            resource_server_url="http://127.0.0.2:8765/mcp",
        )
        app = server.streamable_http_app(
            host="127.0.0.2",
            transport_security=mcp_server._transport_security_settings(
                "127.0.0.2", 8765
            ),
            max_request_body_size=mcp_server.HTTP_MAX_REQUEST_BODY_SIZE,
            max_sessions=mcp_server.HTTP_MAX_SESSIONS,
            session_idle_timeout=mcp_server.HTTP_SESSION_IDLE_TIMEOUT,
        )
        bearer = (b"authorization", f"Bearer {token}".encode("ascii"))
        malformed_bearer = (b"authorization", b"Bearer \xe9")

        async with app.router.lifespan_context(app):
            unauthorized = await _asgi_get_status(
                app, [(b"host", b"127.0.0.2:8765")]
            )
            with self.assertLogs("mcp.server.transport_security", level="WARNING"):
                wrong_host = await _asgi_get_status(
                    app, [(b"host", b"evil.local:8765"), bearer]
                )
                wrong_origin = await _asgi_get_status(
                    app,
                    [
                        (b"host", b"127.0.0.2:8765"),
                        (b"origin", b"http://evil.local:8765"),
                        bearer,
                    ],
                )
            malformed = await _asgi_get_status(
                app, [(b"host", b"127.0.0.2:8765"), malformed_bearer]
            )
            authenticated = await _asgi_get_status(
                app, [(b"host", b"127.0.0.2:8765"), bearer]
            )

        self.assertEqual(unauthorized, 401)
        self.assertEqual(wrong_host, 421)
        self.assertEqual(wrong_origin, 403)
        self.assertEqual(malformed, 401)
        self.assertEqual(authenticated, 406)


if __name__ == "__main__":
    unittest.main()
