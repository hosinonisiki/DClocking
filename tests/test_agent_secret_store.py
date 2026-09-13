import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import qt_test_support  # noqa: F401 - installs project import paths
from secret_store import (
    ACCOUNT_NAME,
    ENVIRONMENT_ENDPOINT,
    ENVIRONMENT_KEY,
    SERVICE_NAME,
    SecretStoreError,
    credential_account,
    load_agent_configuration,
    save_agent_settings,
    validate_endpoint,
)


class FakeKeyring:
    def __init__(self):
        self.values = {}

    def get_password(self, service, account):
        return self.values.get((service, account))

    def set_password(self, service, account, value):
        self.values[(service, account)] = value


class AgentSecretStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "config.json"
        self.keyring = FakeKeyring()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_legacy_plaintext_key_is_migrated_out_of_public_config(self):
        self.config_path.write_text(
            json.dumps(
                {
                    "llm": {
                        "endpoint": "https://api.deepseek.com/v1",
                        "api_key": "secret-value",
                        "model": "deepseek-chat",
                    },
                    "agent": {"max_tool_iterations": 3},
                }
            ),
            encoding="utf-8",
        )

        config, key, warning = load_agent_configuration(
            self.config_path, keyring_backend=self.keyring
        )

        self.assertEqual(key, "secret-value")
        self.assertIn("迁移", warning)
        self.assertNotIn("api_key", config["llm"])
        disk = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertNotIn("api_key", disk["llm"])
        self.assertEqual(
            self.keyring.get_password(
                SERVICE_NAME,
                credential_account("https://api.deepseek.com/v1"),
            ),
            "secret-value",
        )

    def test_saving_settings_never_serializes_api_key(self):
        config, key = save_agent_settings(
            self.config_path,
            endpoint="https://api.deepseek.com/v1/",
            api_key="new-secret",
            model="deepseek-chat",
            keyring_backend=self.keyring,
        )

        self.assertEqual(key, "new-secret")
        self.assertEqual(config["llm"]["endpoint"], "https://api.deepseek.com/v1")
        self.assertNotIn("new-secret", self.config_path.read_text(encoding="utf-8"))

    def test_environment_key_overrides_persistent_key(self):
        self.keyring.set_password(
            SERVICE_NAME,
            credential_account("https://api.openai.com/v1"),
            "stored",
        )
        with patch.dict(
            "os.environ",
            {
                ENVIRONMENT_KEY: "managed",
                ENVIRONMENT_ENDPOINT: "https://api.openai.com/v1/",
            },
            clear=True,
        ):
            _config, key, _warning = load_agent_configuration(
                self.config_path, keyring_backend=self.keyring
            )
        self.assertEqual(key, "managed")

    def test_environment_key_without_matching_endpoint_binding_is_ignored(self):
        self.keyring.set_password(
            SERVICE_NAME,
            credential_account("https://api.openai.com/v1"),
            "stored",
        )
        with patch.dict(
            "os.environ",
            {
                ENVIRONMENT_KEY: "deepseek-secret",
                ENVIRONMENT_ENDPOINT: "https://api.deepseek.com/v1",
            },
            clear=True,
        ):
            _config, key, warning = load_agent_configuration(
                self.config_path, keyring_backend=self.keyring
            )

        self.assertEqual(key, "stored")
        self.assertIn("Endpoint 与当前设置不一致", warning)

    def test_windows_migration_write_failure_disables_agent(self):
        self.config_path.write_text(
            json.dumps({"llm": {"api_key": "legacy-secret"}}),
            encoding="utf-8",
        )
        with (
            patch("secret_store._is_windows", return_value=True),
            patch(
                "secret_store._atomic_write_public_config",
                side_effect=OSError("simulated write failure"),
            ),
            patch.dict("os.environ", {}, clear=True),
        ):
            _config, key, warning = load_agent_configuration(
                self.config_path, keyring_backend=self.keyring
            )

        self.assertEqual(key, "")
        self.assertIn("Agent 已禁用", warning)
        self.assertIn("legacy-secret", self.config_path.read_text(encoding="utf-8"))

    def test_remote_plain_http_endpoint_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_endpoint("http://api.example.com/v1")
        self.assertEqual(validate_endpoint("http://127.0.0.1:8000/v1"), "http://127.0.0.1:8000/v1")

    def test_missing_credential_backend_never_falls_back_to_plaintext_save(self):
        with patch("secret_store._system_keyring", return_value=None):
            with self.assertRaises(SecretStoreError):
                save_agent_settings(
                    self.config_path,
                    endpoint="https://api.deepseek.com/v1",
                    api_key="must-not-hit-disk",
                    model="deepseek-chat",
                )
        self.assertFalse(self.config_path.exists())

    def test_missing_backend_does_not_delete_an_unmigrated_legacy_key(self):
        self.config_path.write_text(
            json.dumps({"llm": {"api_key": "legacy-secret"}}),
            encoding="utf-8",
        )
        with patch("secret_store._system_keyring", return_value=None):
            with self.assertRaises(SecretStoreError):
                save_agent_settings(
                    self.config_path,
                    endpoint="https://api.deepseek.com/v1",
                    api_key="",
                    model="deepseek-chat",
                )
        self.assertIn("legacy-secret", self.config_path.read_text(encoding="utf-8"))

    def test_credentials_are_isolated_by_api_origin(self):
        _config, deepseek_key = save_agent_settings(
            self.config_path,
            endpoint="https://api.deepseek.com/v1",
            api_key="deepseek-secret",
            model="deepseek-chat",
            keyring_backend=self.keyring,
        )
        self.assertEqual(deepseek_key, "deepseek-secret")

        _config, openai_key = save_agent_settings(
            self.config_path,
            endpoint="https://api.openai.com/v1",
            api_key="",
            model="gpt-4o",
            keyring_backend=self.keyring,
        )

        self.assertEqual(openai_key, "")
        self.assertEqual(
            self.keyring.get_password(
                SERVICE_NAME,
                credential_account("https://api.deepseek.com/v1"),
            ),
            "deepseek-secret",
        )

    def test_unscoped_legacy_keyring_entry_is_never_sent_to_current_endpoint(self):
        self.keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, "unscoped-secret")

        _config, key, warning = load_agent_configuration(
            self.config_path,
            keyring_backend=self.keyring,
        )

        self.assertEqual(key, "")
        self.assertIn("不会使用", warning)

    def test_windows_does_not_use_plaintext_legacy_key_without_keyring(self):
        self.config_path.write_text(
            json.dumps({"llm": {"api_key": "legacy-secret"}}),
            encoding="utf-8",
        )
        with (
            patch("secret_store._system_keyring", return_value=None),
            patch("secret_store._is_windows", return_value=True),
        ):
            _config, key, warning = load_agent_configuration(self.config_path)

        self.assertEqual(key, "")
        self.assertIn("Agent 已禁用", warning)
        self.assertIn("legacy-secret", self.config_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
