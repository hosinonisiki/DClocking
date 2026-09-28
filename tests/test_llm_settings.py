"""Offline budget settings persistence and live client reconfiguration."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from tests import qt_test_support  # noqa: F401 - project import paths
from llm_client import LLMClient
from secret_store import load_agent_configuration, save_agent_settings


class ClientOutputBudgetTests(unittest.TestCase):
    def test_package_imports_remain_available_without_agent_path_injection(self):
        result = subprocess.run([sys.executable, "-c",
            "from FPGA_Agent.llm_client import LLMClient; "
            "from FPGA_Agent.secret_store import save_agent_settings; "
            "assert LLMClient('https://example.test/v1', '', 'deepseek-v4-pro').max_tokens == 32768"],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_constructor_and_config_use_auto_for_absent_or_null_budget(self):
        client = LLMClient("https://example.test/v1", "", "deepseek-v4-pro")
        self.assertEqual(client.configuration_snapshot()["max_tokens"], 32768)
        for llm in ({"model": "deepseek-reasoner"},
                    {"model": "deepseek-reasoner", "max_tokens": None}):
            self.assertEqual(LLMClient.from_config({"llm": llm}).max_tokens, 32768)

    def test_model_change_recalculates_auto_and_preserves_explicit_budget(self):
        client = LLMClient("https://example.test/v1", "", "gpt-4o")
        fields = dict(endpoint="https://example.test/v1", api_key="")
        client.configure(**fields, model="deepseek-v4-pro")
        self.assertEqual(client.max_tokens, 32768)
        client.configure(**fields, model="deepseek-v4-pro", max_tokens=8192)
        client.configure(**fields, model="gpt-4o")
        self.assertEqual(client.max_tokens, 8192)
        client.configure(**fields, model="deepseek-v4-pro", max_tokens=None)
        self.assertEqual(client.max_tokens, 32768)

    def test_invalid_configure_does_not_partially_mutate_live_client(self):
        client = LLMClient("https://example.test/v1", "old-key", "gpt-4o")
        before = client.configuration_snapshot()
        for value in (True, 0, -1, 131073, 4096.0, "4096"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                client.configure(endpoint="https://other.test/v1", api_key="new-key",
                                 model="deepseek-v4-pro", max_tokens=value)
            self.assertEqual(client.configuration_snapshot(), before)


class OutputBudgetPersistenceTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "config.json"
        self.keyring = Mock()
        self.keyring.get_password.return_value = None
        environment = patch.dict("os.environ", {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def save(self, **kwargs):
        return save_agent_settings(self.path, endpoint="https://example.test/v1",
                                   api_key="", model="deepseek-v4-pro",
                                   keyring_backend=self.keyring, **kwargs)

    def test_load_does_not_materialize_missing_auto_budget_or_write_disk(self):
        self.path.write_text('{"llm":{"model":"deepseek-v4-pro"}}', encoding="utf-8")
        before = self.path.read_bytes()
        config, _, _ = load_agent_configuration(self.path, keyring_backend=self.keyring)
        self.assertNotIn("max_tokens", config["llm"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_explicit_and_auto_round_trip_and_old_save_preserves_policy(self):
        for value in (4096, 65536, None):
            with self.subTest(value=value):
                self.save(max_tokens=value)
                self.save()
                config, _, _ = load_agent_configuration(self.path, keyring_backend=self.keyring)
                disk = json.loads(self.path.read_text(encoding="utf-8"))
                self.assertEqual(config["llm"]["max_tokens"], value)
                self.assertEqual(disk["llm"]["max_tokens"], value)

    def test_legacy_save_without_budget_keeps_absent_field(self):
        config, _ = self.save()
        self.assertNotIn("max_tokens", config["llm"])

    def test_invalid_budget_fails_before_credentials_or_config_are_written(self):
        for value in (True, 0, -1, 131073, "4096", 4096.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                save_agent_settings(self.path, endpoint="https://example.test/v1",
                                    api_key="test-secret", model="deepseek-v4-pro",
                                    max_tokens=value, keyring_backend=self.keyring)
            self.keyring.set_password.assert_not_called()
            self.assertFalse(self.path.exists())

    def test_invalid_loaded_budget_is_rejected_before_credential_migration(self):
        self.path.write_text('{"llm":{"max_tokens":true,"api_key":"test-secret"}}', encoding="utf-8")
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            load_agent_configuration(self.path, keyring_backend=self.keyring)
        self.keyring.set_password.assert_not_called()
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
