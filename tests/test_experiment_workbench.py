import tempfile
import unittest
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QDir, QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

from tests.qt_test_support import ensure_app
from qt_experiment_workbench import ExperimentWorkbench
from qt_ui_mainwindow import MainWindow


class ExperimentWorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "records"
        self.settings = QSettings(
            f"{self.temp_dir.name}/ui.ini", QSettings.IniFormat
        )
        self.workbench = ExperimentWorkbench(
            settings=self.settings,
            default_root=self.root,
        )
        self.workbench.show()
        self.app.processEvents()

    def tearDown(self):
        self.workbench._close_without_prompt = True
        self.workbench.close()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def test_default_repository_is_created_and_persisted(self):
        self.assertEqual(self.workbench.repository_root, self.root.resolve())
        self.assertTrue(self.root.is_dir())
        self.assertEqual(
            Path(self.settings.value("experiment_workspace/root")),
            self.root.resolve(),
        )
        self.assertEqual(
            Path(self.workbench.file_model.rootPath()), self.root.resolve()
        )
        self.assertFalse(self.workbench.editor.isEnabled())

    def test_create_edit_preview_and_atomic_save_round_trip(self):
        record = self.workbench.create_record(
            "激光锁定测试", when=datetime(2026, 9, 10, 14, 30)
        )
        self.assertEqual(
            record.relative_to(self.root.resolve()).as_posix(),
            "2026-09-10/1430-激光锁定测试.md",
        )
        self.workbench.editor.setPlainText("# 激光锁定测试\n\n**结果：稳定**")
        self.app.processEvents()
        self.assertTrue(self.workbench.is_dirty)
        self.assertIn("激光锁定测试", self.workbench.preview.toPlainText())

        self.assertTrue(self.workbench.save_document())
        self.assertFalse(self.workbench.is_dirty)
        self.assertEqual(
            record.read_text(encoding="utf-8"),
            "# 激光锁定测试\n\n**结果：稳定**",
        )
        self.assertFalse(any(record.parent.glob(".experiment_*.tmp")))
        QTest.qWait(100)
        source_index = self.workbench.file_model.index(str(record))
        self.assertTrue(source_index.isValid())
        self.assertTrue(self.workbench.file_proxy.mapFromSource(source_index).isValid())

        self.workbench.editor.setPlainText("临时内容")
        self.workbench.open_document(record, prompt_unsaved=False)
        self.assertEqual(
            self.workbench.editor.toPlainText(),
            "# 激光锁定测试\n\n**结果：稳定**",
        )

    def test_save_action_uses_standard_save_shortcut(self):
        record = self.workbench.create_record(
            "快捷保存", when=datetime(2026, 9, 10, 14, 31)
        )
        self.workbench.editor.setPlainText("由快捷键保存")

        self.assertFalse(self.workbench.save_action.shortcut().isEmpty())
        self.workbench.save_action.trigger()

        self.assertEqual(record.read_text(encoding="utf-8"), "由快捷键保存")
        self.assertFalse(self.workbench.is_dirty)

    def test_rejects_outside_symlink_binary_and_oversized_files(self):
        outside = Path(self.temp_dir.name) / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        link = self.root / "escape.md"
        link.symlink_to(outside)
        binary = self.root / "capture.dat"
        binary.write_bytes(b"abc\x00def")
        oversized = self.root / "large.txt"
        oversized.write_bytes(b"x" * (ExperimentWorkbench.MAX_FILE_BYTES + 1))

        for candidate in (outside, link, binary, oversized):
            with self.subTest(candidate=candidate.name):
                with patch("qt_experiment_workbench.QMessageBox.warning"):
                    self.assertFalse(self.workbench.open_document(candidate))

        outside_dir = Path(self.temp_dir.name) / "outside-directory"
        outside_dir.mkdir()
        escaped_child = outside_dir / "child.md"
        escaped_child.write_text("outside child", encoding="utf-8")
        (self.root / "linked-directory").symlink_to(outside_dir, target_is_directory=True)
        with patch("qt_experiment_workbench.QMessageBox.warning"):
            self.assertFalse(
                self.workbench.open_document(self.root / "linked-directory" / "child.md")
            )

        self.assertTrue(self.workbench.file_model.filter() & QDir.NoSymLinks)
        self.assertFalse(self.workbench.preview.openLinks())
        self.assertFalse(self.workbench.preview.openExternalLinks())

    def test_cancel_preserves_dirty_document_and_blocks_close(self):
        self.workbench.create_record(
            "未保存", when=datetime(2026, 9, 10, 14, 32)
        )
        self.workbench.editor.setPlainText("尚未保存")
        with patch(
            "qt_experiment_workbench.QMessageBox.question",
            return_value=QMessageBox.Cancel,
        ):
            self.workbench.close()
        self.app.processEvents()

        self.assertTrue(self.workbench.isVisible())
        self.assertTrue(self.workbench.is_dirty)

    def test_discard_restores_disk_content_before_reopening_workbench(self):
        record = self.workbench.create_record(
            "放弃修改", when=datetime(2026, 9, 10, 14, 34)
        )
        original = record.read_text(encoding="utf-8")
        self.workbench.editor.setPlainText("不应保留的临时修改")
        with patch(
            "qt_experiment_workbench.QMessageBox.question",
            return_value=QMessageBox.Discard,
        ):
            self.workbench.close()
        self.app.processEvents()

        self.assertFalse(self.workbench.isVisible())
        self.assertFalse(self.workbench.is_dirty)
        self.assertEqual(self.workbench.editor.toPlainText(), original)
        self.workbench.show()
        self.assertEqual(self.workbench.editor.toPlainText(), original)

    def test_deleted_repository_reports_error_instead_of_raising(self):
        shutil.rmtree(self.root)
        with patch("qt_experiment_workbench.QMessageBox.warning") as warning:
            created = self.workbench.create_record(
                "掉线仓库", when=datetime(2026, 9, 10, 14, 35)
            )

        self.assertIsNone(created)
        warning.assert_called_once()

    def test_save_rejects_content_larger_than_open_limit(self):
        record = self.workbench.create_record(
            "大文件保护", when=datetime(2026, 9, 10, 14, 36)
        )
        original = record.read_text(encoding="utf-8")
        with patch.object(ExperimentWorkbench, "MAX_FILE_BYTES", 64):
            self.workbench.editor.setPlainText("x" * 65)
            with patch("qt_experiment_workbench.QMessageBox.warning") as warning:
                self.assertFalse(self.workbench.save_document())

        self.assertEqual(record.read_text(encoding="utf-8"), original)
        self.assertTrue(self.workbench.is_dirty)
        warning.assert_called_once()

    def test_two_workbenches_do_not_overwrite_same_new_record_name(self):
        other_settings = QSettings(
            f"{self.temp_dir.name}/other.ini", QSettings.IniFormat
        )
        other = ExperimentWorkbench(
            settings=other_settings,
            default_root=self.root,
        )
        try:
            when = datetime(2026, 9, 10, 14, 37)
            first = self.workbench.create_record("并发记录", when=when)
            second = other.create_record("并发记录", when=when)
            self.assertNotEqual(first, second)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())
        finally:
            other._close_without_prompt = True
            other.close()

    def test_same_metadata_external_change_is_saved_as_conflict_copy(self):
        record = self.workbench.create_record(
            "冲突保护", when=datetime(2026, 9, 10, 14, 38)
        )
        original_bytes = record.read_bytes()
        original_stat = record.stat()
        external_bytes = b"X" * len(original_bytes)
        record.write_bytes(external_bytes)
        record.touch()
        # Restore mtime and keep size/inode unchanged; the content hash must still detect it.
        import os

        os.utime(
            record,
            ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
        )
        self.workbench.editor.setPlainText("内部尚未保存的版本")

        with (
            patch(
                "qt_experiment_workbench.QMessageBox.question",
                return_value=QMessageBox.Save,
            ),
            patch("qt_experiment_workbench.QMessageBox.information"),
        ):
            self.assertTrue(self.workbench.save_document())

        self.assertEqual(record.read_bytes(), external_bytes)
        self.assertIn("冲突副本", self.workbench.current_path.name)
        self.assertEqual(
            self.workbench.current_path.read_text(encoding="utf-8"),
            "内部尚未保存的版本",
        )

    def test_deleted_open_file_can_be_recovered_as_conflict_copy(self):
        record = self.workbench.create_record(
            "删除恢复", when=datetime(2026, 9, 10, 14, 39)
        )
        self.workbench.editor.setPlainText("需要恢复的本地修改")
        record.unlink()

        with (
            patch(
                "qt_experiment_workbench.QMessageBox.question",
                return_value=QMessageBox.Save,
            ),
            patch("qt_experiment_workbench.QMessageBox.information"),
        ):
            self.assertTrue(self.workbench.save_document())

        self.assertFalse(record.exists())
        self.assertIn("冲突副本", self.workbench.current_path.name)
        self.assertEqual(
            self.workbench.current_path.read_text(encoding="utf-8"),
            "需要恢复的本地修改",
        )

    def test_deleted_parent_directory_recovers_copy_under_repository_root(self):
        record = self.workbench.create_record(
            "目录恢复", when=datetime(2026, 9, 10, 14, 41)
        )
        self.workbench.editor.setPlainText("父目录消失后的本地修改")
        shutil.rmtree(record.parent)

        with (
            patch(
                "qt_experiment_workbench.QMessageBox.question",
                return_value=QMessageBox.Save,
            ),
            patch("qt_experiment_workbench.QMessageBox.information"),
        ):
            self.assertTrue(self.workbench.save_document())

        self.assertEqual(self.workbench.current_path.parent.name, "恢复记录")
        self.assertEqual(
            self.workbench.current_path.read_text(encoding="utf-8"),
            "父目录消失后的本地修改",
        )

    def test_renamed_and_recreated_repository_is_rejected(self):
        moved = Path(self.temp_dir.name) / "moved-records"
        self.root.rename(moved)
        self.root.mkdir()

        with patch("qt_experiment_workbench.QMessageBox.warning") as warning:
            created = self.workbench.create_record(
                "错误仓库", when=datetime(2026, 9, 10, 14, 40)
            )

        self.assertIsNone(created)
        self.assertFalse(any(moved.rglob("*错误仓库*")))
        warning.assert_called_once()

    def test_repository_open_rejects_ancestor_symlink_swap(self):
        container = Path(self.temp_dir.name) / "candidate-container"
        candidate = container / "repo"
        candidate.mkdir(parents=True)
        moved = Path(self.temp_dir.name) / "candidate-container-original"
        outside = Path(self.temp_dir.name) / "outside-container"
        (outside / "repo").mkdir(parents=True)
        original_open = self.workbench._open_absolute_directory_no_symlinks

        def swap_then_open(path):
            container.rename(moved)
            container.symlink_to(outside, target_is_directory=True)
            return original_open(path)

        with (
            patch.object(
                self.workbench,
                "_open_absolute_directory_no_symlinks",
                side_effect=swap_then_open,
            ),
            patch("qt_experiment_workbench.QMessageBox.warning") as warning,
        ):
            self.assertFalse(self.workbench.set_repository_root(candidate))

        self.assertEqual(self.workbench.repository_root, self.root.resolve())
        warning.assert_called_once()

    def test_atomic_exchange_preserves_external_write_during_save(self):
        record = self.workbench.create_record(
            "交换冲突", when=datetime(2026, 9, 10, 14, 42)
        )
        self.workbench.editor.setPlainText("本地版本")
        original_exchange = self.workbench._exchange_names
        raced = False

        def race_before_exchange(parent_fd, first, second):
            nonlocal raced
            if not raced:
                raced = True
                record.write_text("外部抢先版本", encoding="utf-8")
            return original_exchange(parent_fd, first, second)

        with (
            patch.object(
                self.workbench,
                "_exchange_names",
                side_effect=race_before_exchange,
            ),
            patch(
                "qt_experiment_workbench.QMessageBox.question",
                return_value=QMessageBox.Save,
            ),
            patch("qt_experiment_workbench.QMessageBox.information"),
        ):
            self.assertTrue(self.workbench.save_document())

        self.assertEqual(record.read_text(encoding="utf-8"), "外部抢先版本")
        self.assertIn("冲突副本", self.workbench.current_path.name)
        self.assertEqual(
            self.workbench.current_path.read_text(encoding="utf-8"), "本地版本"
        )

    def test_post_publish_external_write_creates_recovery_copy(self):
        record = self.workbench.create_record(
            "发布后冲突", when=datetime(2026, 9, 10, 14, 43)
        )
        self.workbench.editor.setPlainText("本地待保存版本")
        original_read = self.workbench._read_document
        first_read = True

        def race_before_verification(path):
            nonlocal first_read
            if first_read:
                first_read = False
                record.write_text("发布后的外部版本", encoding="utf-8")
            return original_read(path)

        with (
            patch.object(
                self.workbench,
                "_read_document",
                side_effect=race_before_verification,
            ),
            patch("qt_experiment_workbench.QMessageBox.information"),
        ):
            self.assertTrue(self.workbench.save_document())

        self.assertEqual(record.read_text(encoding="utf-8"), "发布后的外部版本")
        self.assertIn("冲突副本", self.workbench.current_path.name)
        self.assertEqual(
            self.workbench.current_path.read_text(encoding="utf-8"),
            "本地待保存版本",
        )

    def test_failed_exchange_rollback_exposes_original_as_recovery_file(self):
        record = self.workbench.create_record(
            "回滚失败", when=datetime(2026, 9, 10, 14, 44)
        )
        self.workbench.editor.setPlainText("本地交换版本")
        original_exchange = self.workbench._exchange_names
        exchange_count = 0

        def fail_second_exchange(parent_fd, first, second):
            nonlocal exchange_count
            exchange_count += 1
            if exchange_count == 1:
                record.write_text("需要保留的外部版本", encoding="utf-8")
                return original_exchange(parent_fd, first, second)
            raise OSError("injected rollback failure")

        with (
            patch.object(
                self.workbench,
                "_exchange_names",
                side_effect=fail_second_exchange,
            ),
            patch("qt_experiment_workbench.QMessageBox.warning") as warning,
        ):
            self.assertFalse(self.workbench.save_document())

        self.assertEqual(record.read_text(encoding="utf-8"), "本地交换版本")
        recovered = list(record.parent.glob("*原版本恢复*"))
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0].read_text(encoding="utf-8"), "需要保留的外部版本")
        self.assertTrue(self.workbench.is_dirty)
        warning.assert_called_once()

    def test_directory_fsync_failure_rolls_back_before_conflict_save(self):
        record = self.workbench.create_record(
            "同步失败", when=datetime(2026, 9, 10, 14, 45)
        )
        original = record.read_text(encoding="utf-8")
        self.workbench.editor.setPlainText("本地同步版本")
        import qt_experiment_workbench

        original_fsync = qt_experiment_workbench.os.fsync
        fsync_count = 0

        def fail_exchange_fsync(descriptor):
            nonlocal fsync_count
            fsync_count += 1
            if fsync_count == 2:
                raise OSError("injected directory fsync failure")
            return original_fsync(descriptor)

        with (
            patch("qt_experiment_workbench.os.fsync", side_effect=fail_exchange_fsync),
            patch(
                "qt_experiment_workbench.QMessageBox.question",
                return_value=QMessageBox.Save,
            ),
            patch("qt_experiment_workbench.QMessageBox.information"),
        ):
            self.assertTrue(self.workbench.save_document())

        self.assertEqual(record.read_text(encoding="utf-8"), original)
        self.assertIn("冲突副本", self.workbench.current_path.name)
        self.assertEqual(
            self.workbench.current_path.read_text(encoding="utf-8"),
            "本地同步版本",
        )

    def test_second_external_write_during_rollback_is_preserved(self):
        record = self.workbench.create_record(
            "二次外部写入", when=datetime(2026, 9, 10, 14, 46)
        )
        self.workbench.editor.setPlainText("本地编辑版本")
        original_exchange = self.workbench._exchange_names
        exchange_count = 0

        def race_on_both_exchanges(parent_fd, first, second):
            nonlocal exchange_count
            exchange_count += 1
            if exchange_count == 1:
                record.write_text("外部版本一", encoding="utf-8")
            elif exchange_count == 2:
                record.write_text("外部版本二", encoding="utf-8")
            return original_exchange(parent_fd, first, second)

        with (
            patch.object(
                self.workbench,
                "_exchange_names",
                side_effect=race_on_both_exchanges,
            ),
            patch(
                "qt_experiment_workbench.QMessageBox.question",
                return_value=QMessageBox.Save,
            ),
            patch("qt_experiment_workbench.QMessageBox.information"),
        ):
            self.assertTrue(self.workbench.save_document())

        self.assertEqual(record.read_text(encoding="utf-8"), "外部版本一")
        recovered = list(record.parent.glob("*原版本恢复*"))
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0].read_text(encoding="utf-8"), "外部版本二")
        self.assertIn("冲突副本", self.workbench.current_path.name)
        self.assertEqual(
            self.workbench.current_path.read_text(encoding="utf-8"),
            "本地编辑版本",
        )

    def test_switch_repository_restores_last_selected_root(self):
        selected = Path(self.temp_dir.name) / "another-repository"
        self.assertTrue(self.workbench.set_repository_root(selected))
        self.assertEqual(self.workbench.repository_root, selected.resolve())
        self.workbench._close_without_prompt = True
        self.workbench.close()

        restored = ExperimentWorkbench(
            settings=self.settings,
            default_root=self.root,
        )
        try:
            self.assertEqual(restored.repository_root, selected.resolve())
        finally:
            restored._close_without_prompt = True
            restored.close()


class MainWindowExperimentWorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = QSettings(
            f"{self.temp_dir.name}/main.ini", QSettings.IniFormat
        )
        self.repository = Path(self.temp_dir.name) / "records"
        self.window = MainWindow(
            settings=self.settings,
            experiment_repository_path=self.repository,
        )
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        if self.window._experiment_workbench is not None:
            self.window._experiment_workbench._close_without_prompt = True
        self.window.close()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def test_left_rail_opens_and_reuses_one_workbench(self):
        self.assertEqual(
            self.window.experiment_rail_btn.accessibleName(), "打开实验记录工作台"
        )
        self.assertFalse(self.window.experiment_rail_btn.isCheckable())

        self.window.experiment_rail_btn.click()
        self.app.processEvents()
        first = self.window._experiment_workbench
        self.window.experiment_rail_btn.click()
        self.app.processEvents()

        self.assertIsNotNone(first)
        self.assertIs(first, self.window._experiment_workbench)
        self.assertTrue(first.isVisible())
        self.assertFalse(first.isModal())

    def test_main_window_close_is_cancelled_when_record_is_dirty(self):
        workbench = self.window.open_experiment_workbench()
        workbench.create_record(
            "关闭保护", when=datetime(2026, 9, 10, 14, 33)
        )
        workbench.editor.setPlainText("未保存")
        with patch(
            "qt_experiment_workbench.QMessageBox.question",
            return_value=QMessageBox.Cancel,
        ):
            self.window.close()
        self.app.processEvents()

        self.assertTrue(self.window.isVisible())
        self.assertTrue(workbench.isVisible())


if __name__ == "__main__":
    unittest.main()
