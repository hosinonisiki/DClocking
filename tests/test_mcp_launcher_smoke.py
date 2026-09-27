"""Opt-in native-launcher test, installing into a disposable, isolated checkout.

Set DCLOCKING_MCP_BOOTSTRAP_SMOKE=1 to enable the dependency installation.
Normal test discovery never needs package-index access. The test selects the
native POSIX or Windows launcher; it does not claim to emulate another OS.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import anyio
from mcp import StdioServerParameters
from mcp.client import Client


ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(os.environ.get("DCLOCKING_MCP_BOOTSTRAP_SMOKE") == "1",
                     "opt-in: installs MCP dependencies in a temporary environment")
class MCPNativeLauncherSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_clean_bootstrap_then_stdio_handshake_and_cached_restart(self):
        with tempfile.TemporaryDirectory(prefix="dclocking-mcp-bootstrap-") as temporary:
            checkout = Path(temporary) / "实验 checkout with spaces"
            checkout.mkdir()
            # Copy source only. In particular, never copy config.json, keys,
            # user documents, logs, the actual .venv, or the Git repository.
            for folder in ("FPGA_Agent", "python control"):
                (checkout / folder).mkdir()
                for source in (ROOT / folder).glob("*.py"):
                    shutil.copy2(source, checkout / folder / source.name)
            (checkout / "scripts").mkdir()
            for name in ("start-mcp-server.sh", "start-mcp-server.ps1"):
                shutil.copy2(ROOT / "scripts" / name, checkout / "scripts" / name)
            shutil.copy2(ROOT / "requirements-mcp.txt", checkout / "requirements-mcp.txt")
            command = self._native_command(checkout)
            env = {key: value for key, value in os.environ.items()
                   if key in {"PATH", "HOME", "SYSTEMROOT", "WINDIR", "TEMP", "TMP",
                              "USERPROFILE", "LANG", "LC_ALL"}}
            env.update({
                "PATH": str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", ""),
                "PYTHONUTF8": "1", "PIP_NO_INPUT": "1", "PIP_CONFIG_FILE": os.devnull,
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_DEFAULT_TIMEOUT": "15", "PIP_RETRIES": "0",
            })
            # Run outside the checkout: the launcher must locate its own root.
            bootstrap = await asyncio.to_thread(
                subprocess.run, [*command, "--help"], cwd=temporary, env=env,
                capture_output=True, text=True, encoding="utf-8", timeout=120,
            )
            self.assertEqual(bootstrap.returncode, 0, bootstrap.stderr)
            self.assertIn("Start the read-only local DClocking MCP server", bootstrap.stdout)
            self.assertNotIn("Installing collected packages", bootstrap.stdout)
            stamp = checkout / ".venv" / ".mcp-requirements.sha256"
            expected = hashlib.sha256((checkout / "requirements-mcp.txt").read_bytes()).hexdigest()
            self.assertEqual(stamp.read_text(encoding="ascii").strip().lower(), expected)
            installed_at = stamp.stat().st_mtime_ns

            python = checkout / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            packages = await asyncio.to_thread(
                subprocess.run, [str(python), "-m", "pip", "list", "--format=json"],
                env=env, capture_output=True, text=True, encoding="utf-8", timeout=15,
            )
            self.assertEqual(packages.returncode, 0, packages.stderr)
            names = {item["name"].lower() for item in json.loads(packages.stdout)}
            self.assertIn("mcp", names)
            self.assertFalse(names & {"pyqt5", "pyqt6", "pyside6", "scipy"})

            # Two real launches ensure cached startup keeps stdout protocol-only.
            parameters = StdioServerParameters(command=command[0], args=command[1:],
                                               cwd=temporary, env=env)
            for _ in range(2):
                with anyio.fail_after(20):
                    async with Client(parameters, mode="legacy", read_timeout_seconds=5) as client:
                        self.assertEqual(client.server_info.name, "dclocking-local")
                        self.assertEqual(len((await client.list_tools()).tools), 5)
                        spec = await client.call_tool("get_module_spec", {"module_type": "PDH状态机"})
                        self.assertTrue(spec.structured_content["ok"])
                        resource = await client.read_resource("dclocking://project/info")
                        self.assertEqual(json.loads(resource.contents[0].text)["access"], "read-only")
            self.assertEqual(stamp.stat().st_mtime_ns, installed_at)

    def _native_command(self, checkout):
        if os.name == "nt":
            powershell = shutil.which("powershell") or shutil.which("pwsh")
            if not powershell:
                self.skipTest("Native Windows PowerShell is unavailable")
            return [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    str(checkout / "scripts" / "start-mcp-server.ps1")]
        shell = shutil.which("sh")
        if not shell:
            self.skipTest("POSIX sh is unavailable")
        return [shell, str(checkout / "scripts" / "start-mcp-server.sh")]


if __name__ == "__main__":
    unittest.main()
