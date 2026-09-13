import tempfile
import unittest
import stat
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMessageBox

from tests.qt_test_support import ensure_app
from qt_experiment_workbench import ExperimentWorkbench
from qt_experiment_storage import PortableExperimentRepository


class PortableExperimentStorageTests(unittest.TestCase):
    """Exercise the non-native fallback backend used by portable CI hosts."""

    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "records"
        settings = QSettings(
            f"{self.temp_dir.name}/portable.ini", QSettings.IniFormat
        )
        self.workbench = ExperimentWorkbench(
            settings=settings,
            default_root=self.root,
            storage_backend="portable",
        )
        self.workbench.show()
        self.app.processEvents()

    def tearDown(self):
        self.workbench._close_without_prompt = True
        self.workbench.close()
        self.workbench._close_root_descriptor()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def test_portable_backend_create_edit_and_save_round_trip(self):
        record = self.workbench.create_record(
            "Windows 实验", when=datetime(2026, 9, 13, 9, 30)
        )
        self.workbench.editor.setPlainText("# Windows\n\n跨平台保存")

        self.assertTrue(self.workbench.save_document())
        self.assertEqual(record.read_text(encoding="utf-8"), "# Windows\n\n跨平台保存")
        self.assertFalse(self.workbench.is_dirty)

    def test_portable_backend_preserves_external_edit_as_conflict(self):
        record = self.workbench.create_record(
            "冲突", when=datetime(2026, 9, 13, 9, 31)
        )
        record.write_text("外部版本", encoding="utf-8")
        self.workbench.editor.setPlainText("工作台版本")

        with (
            patch(
                "qt_experiment_workbench.QMessageBox.question",
                return_value=QMessageBox.Save,
            ),
            patch("qt_experiment_workbench.QMessageBox.information"),
        ):
            self.assertTrue(self.workbench.save_document())

        self.assertEqual(record.read_text(encoding="utf-8"), "外部版本")
        self.assertIn("冲突副本", self.workbench.current_path.name)
        self.assertEqual(
            self.workbench.current_path.read_text(encoding="utf-8"), "工作台版本"
        )

    def test_portable_backend_rejects_symlink_escape(self):
        outside = Path(self.temp_dir.name) / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        link = self.root / "escape.md"
        try:
            link.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable on this Windows host: {exc}")

        with patch("qt_experiment_workbench.QMessageBox.warning"):
            self.assertFalse(self.workbench.open_document(link))

    def test_windows_reparse_attribute_is_rejected_even_without_symlink_mode(self):
        fake_stat = type(
            "FakeStat",
            (),
            {
                "st_mode": stat.S_IFDIR,
                "st_file_attributes": getattr(
                    stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400
                ),
            },
        )()
        self.assertTrue(
            PortableExperimentRepository._is_reparse_or_symlink(
                self.root, fake_stat
            )
        )


if __name__ == "__main__":
    unittest.main()
