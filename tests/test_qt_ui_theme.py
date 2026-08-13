import unittest

from PySide6.QtWidgets import QWidget

from tests.qt_test_support import ensure_app
from qt_ui_theme import UiColors, apply_application_theme, build_application_stylesheet


class ThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def test_brand_and_canvas_tokens_match_approved_design(self):
        self.assertEqual(UiColors.PKU_WINE, "#85172E")
        self.assertEqual(UiColors.CANVAS_BG, "#171B1D")
        self.assertEqual(UiColors.SURFACE, "#FBFBF9")

    def test_stylesheet_covers_named_shell_widgets_and_states(self):
        qss = build_application_stylesheet()
        for selector in (
            "#left_rail",
            "#command_bar",
            "#inspector_panel",
            "#status_bar",
            "#agent_toggle_button",
            ":disabled",
            ":focus",
        ):
            self.assertIn(selector, qss)

    def test_apply_theme_sets_font_and_stylesheet_without_dependency(self):
        widget = QWidget()
        apply_application_theme(widget)
        self.assertIn("#85172E", widget.styleSheet())
        self.assertIn(
            widget.font().family(),
            {"Helvetica Neue", "PingFang SC", ".AppleSystemUIFont"},
        )


if __name__ == "__main__":
    unittest.main()
