"""Static portability checks for the local MCP launchers."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class MCPLauncherTests(unittest.TestCase):
    def test_mcp_dependency_is_pinned_consistently(self):
        app_requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        mcp_requirements = (ROOT / "requirements-mcp.txt").read_text(
            encoding="utf-8"
        )

        self.assertIn("mcp==2.2.0", app_requirements.splitlines())
        self.assertEqual(mcp_requirements.splitlines(), ["mcp==2.2.0"])

    def test_launchers_install_only_the_mcp_dependency_set(self):
        shell = (ROOT / "scripts" / "start-mcp-server.sh").read_text(
            encoding="utf-8"
        )
        powershell = (ROOT / "scripts" / "start-mcp-server.ps1").read_text(
            encoding="utf-8"
        )

        self.assertIn("requirements-mcp.txt", shell)
        self.assertIn(".mcp-requirements.sha256", shell)
        self.assertIn("requirements-mcp.txt", powershell)
        self.assertIn(".mcp-requirements.sha256", powershell)
        self.assertIn("for CANDIDATE in python3 python", shell)
        self.assertIn("foreach ($Candidate in $PythonCandidates)", powershell)
        self.assertIn("sys.version_info >= (3, 10)", shell)
        self.assertIn("sys.version_info >= (3, 10)", powershell)

    def test_posix_launcher_has_valid_shell_syntax(self):
        result = subprocess.run(
            ["sh", "-n", str(ROOT / "scripts" / "start-mcp-server.sh")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
