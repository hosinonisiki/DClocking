"""Command-line and transport safety tests for the local MCP server."""

from __future__ import annotations

import contextlib
import io
import os
import unittest
from unittest import mock

from FPGA_Agent import mcp_server


class MCPServerCLITests(unittest.TestCase):
    STRONG_TOKEN = "a" * 32

    def test_defaults_to_stdio_without_writing_protocol_noise_to_stdout(self):
        server = mock.Mock()
        stdout = io.StringIO()

        with (
            mock.patch.object(mcp_server, "create_mcp_server", return_value=server),
            contextlib.redirect_stdout(stdout),
        ):
            result = mcp_server.main([])

        self.assertEqual(result, 0)
        server.run.assert_called_once_with(transport="stdio")
        self.assertEqual(stdout.getvalue(), "")

    def test_keyboard_interrupt_stops_server_without_traceback(self):
        server = mock.Mock()
        server.run.side_effect = KeyboardInterrupt
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            mock.patch.object(mcp_server, "create_mcp_server", return_value=server),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            result = mcp_server.main([])

        self.assertEqual(result, 130)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_http_rejects_non_loopback_hosts_before_server_creation(self):
        stderr = io.StringIO()
        with (
            mock.patch.dict(
                os.environ, {"DCLOCKING_MCP_TOKEN": self.STRONG_TOKEN}
            ),
            mock.patch.object(mcp_server, "create_mcp_server") as create_server,
            contextlib.redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            mcp_server.main(
                [
                    "--transport",
                    "streamable-http",
                    "--host",
                    "0.0.0.0",
                ]
            )

        self.assertEqual(raised.exception.code, 2)
        create_server.assert_not_called()

    def test_http_rejects_scoped_ipv6_loopback_before_server_creation(self):
        stderr = io.StringIO()
        with (
            mock.patch.dict(
                os.environ, {"DCLOCKING_MCP_TOKEN": self.STRONG_TOKEN}
            ),
            mock.patch.object(mcp_server, "create_mcp_server") as create_server,
            contextlib.redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            mcp_server.main(
                ["--transport", "streamable-http", "--host", "::1%lo0"]
            )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("loopback host", stderr.getvalue())
        create_server.assert_not_called()

    def test_http_requires_nonempty_token_before_server_creation(self):
        stderr = io.StringIO()
        with (
            mock.patch.dict(os.environ, {}, clear=True),
            mock.patch.object(mcp_server, "create_mcp_server") as create_server,
            contextlib.redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            mcp_server.main(["--transport", "streamable-http"])

        self.assertEqual(raised.exception.code, 2)
        create_server.assert_not_called()

    def test_http_accepts_loopback_and_passes_transport_settings(self):
        server = mock.Mock()
        with (
            mock.patch.dict(
                os.environ, {"DCLOCKING_MCP_TOKEN": self.STRONG_TOKEN}
            ),
            mock.patch.object(
                mcp_server, "create_mcp_server", return_value=server
            ) as create_server,
        ):
            result = mcp_server.main(
                [
                    "--transport",
                    "streamable-http",
                    "--host",
                    "localhost",
                    "--port",
                    "9876",
                ]
            )

        self.assertEqual(result, 0)
        create_server.assert_called_once_with(
            http_token=self.STRONG_TOKEN,
            resource_server_url="http://localhost:9876/mcp",
        )
        server.run.assert_called_once()
        run_kwargs = server.run.call_args.kwargs
        self.assertEqual(run_kwargs["transport"], "streamable-http")
        self.assertEqual(run_kwargs["host"], "localhost")
        self.assertEqual(run_kwargs["port"], 9876)
        self.assertEqual(run_kwargs["max_request_body_size"], 1024 * 1024)
        self.assertEqual(run_kwargs["max_sessions"], 16)
        self.assertEqual(run_kwargs["session_idle_timeout"], 300.0)
        security = run_kwargs["transport_security"]
        self.assertEqual(security.allowed_hosts, ["localhost:9876"])
        self.assertEqual(security.allowed_origins, ["http://localhost:9876"])

    def test_http_accepts_another_numeric_loopback_with_explicit_protection(self):
        server = mock.Mock()
        with (
            mock.patch.dict(
                os.environ, {"DCLOCKING_MCP_TOKEN": self.STRONG_TOKEN}
            ),
            mock.patch.object(mcp_server, "create_mcp_server", return_value=server),
        ):
            result = mcp_server.main(
                [
                    "--transport",
                    "streamable-http",
                    "--host",
                    "127.0.0.2",
                    "--port",
                    "8765",
                ]
            )

        self.assertEqual(result, 0)
        security = server.run.call_args.kwargs["transport_security"]
        self.assertEqual(security.allowed_hosts, ["127.0.0.2:8765"])
        self.assertEqual(security.allowed_origins, ["http://127.0.0.2:8765"])

    def test_http_canonicalizes_loopback_aliases_before_binding(self):
        aliases = (
            ("LOCALHOST.", "localhost"),
            ("0:0:0:0:0:0:0:1", "::1"),
        )
        for supplied, canonical in aliases:
            with self.subTest(host=supplied):
                server = mock.Mock()
                with (
                    mock.patch.dict(
                        os.environ, {"DCLOCKING_MCP_TOKEN": self.STRONG_TOKEN}
                    ),
                    mock.patch.object(
                        mcp_server, "create_mcp_server", return_value=server
                    ),
                ):
                    result = mcp_server.main(
                        ["--transport", "streamable-http", "--host", supplied]
                    )

                self.assertEqual(result, 0)
                self.assertEqual(server.run.call_args.kwargs["host"], canonical)

    def test_http_rejects_weak_oversized_or_whitespace_tokens(self):
        invalid_tokens = (
            "a" * 31,
            "a" * 257,
            "a" * 31 + " ",
            "a" * 16 + "\n" + "b" * 16,
        )
        for token in invalid_tokens:
            with self.subTest(token_length=len(token)):
                stderr = io.StringIO()
                with (
                    mock.patch.dict(
                        os.environ, {"DCLOCKING_MCP_TOKEN": token}, clear=True
                    ),
                    mock.patch.object(mcp_server, "create_mcp_server") as create_server,
                    contextlib.redirect_stderr(stderr),
                    self.assertRaises(SystemExit) as raised,
                ):
                    mcp_server.main(["--transport", "streamable-http"])

                self.assertEqual(raised.exception.code, 2)
                create_server.assert_not_called()
                self.assertNotIn(token, stderr.getvalue())

    def test_http_rejects_out_of_range_port(self):
        stderr = io.StringIO()
        with (
            mock.patch.dict(
                os.environ, {"DCLOCKING_MCP_TOKEN": self.STRONG_TOKEN}
            ),
            mock.patch.object(mcp_server, "create_mcp_server") as create_server,
            contextlib.redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            mcp_server.main(
                ["--transport", "streamable-http", "--port", "70000"]
            )

        self.assertEqual(raised.exception.code, 2)
        create_server.assert_not_called()


if __name__ == "__main__":
    unittest.main()
