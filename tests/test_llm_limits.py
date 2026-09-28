"""Application output budgets, not provider capability limits."""

import unittest

from tests import qt_test_support  # noqa: F401 - project import paths
from llm_limits import resolve_max_tokens


class OutputBudgetTests(unittest.TestCase):
    def test_known_reasoning_models_have_larger_auto_budget(self):
        for model in (
            "deepseek-v4-pro", "deepseek-v4-flash", "deepseek-flash",
            "deepseek-reasoner", " DeepSeek-V4-Pro ",
        ):
            with self.subTest(model=model):
                self.assertEqual(resolve_max_tokens(model), 32768)
                self.assertEqual(resolve_max_tokens(model, None), 32768)

    def test_other_models_keep_conservative_auto_budget(self):
        for model in ("gpt-4o", "deepseek-chat", "unknown", "", None):
            with self.subTest(model=model):
                self.assertEqual(resolve_max_tokens(model), 4096)

    def test_explicit_budget_is_preserved_including_old_4096(self):
        for value in (1, 4096, 32768, 131072):
            self.assertEqual(resolve_max_tokens("deepseek-v4-pro", value), value)

    def test_invalid_values_are_not_silently_coerced_or_clamped(self):
        for value in (True, False, 0, -1, 131073, 4096.0, "4096", [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_max_tokens("deepseek-v4-pro", value)


if __name__ == "__main__":
    unittest.main()
