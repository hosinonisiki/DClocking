"""Platform-neutral Windows path-boundary and ReplaceFileW recovery tests.

The real handle and junction tests run only on Windows.  These tests emulate
the documented file-name transitions so macOS development still exercises the
data-preservation branches on every local run.
"""

from contextlib import contextmanager
import hashlib
import ntpath
import os
from pathlib import Path, PureWindowsPath
import tempfile
import types
import unittest
from unittest.mock import patch

from tests import qt_test_support  # noqa: F401 - installs project import paths
import qt_experiment_storage_windows as windows_storage
from qt_experiment_storage_windows import (
    WindowsExperimentRepository,
    WindowsStorageCommitUncertainError,
    WindowsStorageExternalModificationError,
)


class _LexicalWindowsPath(PureWindowsPath):
    """Exercise Windows lexical paths without touching the host filesystem."""

    def expanduser(self):
        # These cases use absolute paths or repository-relative names, never ~.
        return self


class WindowsPathBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.root = _LexicalWindowsPath(
            r"C:\Users\runneradmin\AppData\Local\Temp\test-records\records"
        )
        self.repository = WindowsExperimentRepository(1024, api=object())
        self.enterContext(
            patch.object(self.repository, "require_root", return_value=self.root)
        )
        self.enterContext(patch.object(windows_storage, "Path", _LexicalWindowsPath))
        # Patch only this module's os binding, not the process-wide os.path.
        self.enterContext(
            patch.object(
                windows_storage,
                "os",
                types.SimpleNamespace(path=ntpath, fspath=os.fspath),
            )
        )

    def test_canonical_case_insensitive_and_relative_paths_are_accepted(self):
        for path in (
            self.root / "note.md",
            str(self.root).upper() + r"\note.md",
            "note.md",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.repository.relative_parts(path), ("note.md",))

    def test_short_alias_is_not_a_substitute_for_the_returned_canonical_root(self):
        short_root = str(self.root).replace("runneradmin", "RUNNER~1")
        with self.assertRaisesRegex(ValueError, "文件不在当前实验仓库内"):
            self.repository.relative_parts(short_root + r"\note.md")
        self.assertEqual(
            self.repository.relative_parts(self.root / "note.md"), ("note.md",)
        )

    def test_outside_paths_remain_rejected(self):
        for path in (
            self.root.parent / "records-other" / "note.md",
            r"..\outside\note.md",
            r"D:\records\note.md",
            r"\\server\share\records\note.md",
        ):
            with self.subTest(path=path), self.assertRaisesRegex(
                ValueError, "文件不在当前实验仓库内"
            ):
                self.repository.relative_parts(path)


class _PortableNameApi:
    ERROR_UNABLE_TO_MOVE_REPLACEMENT_2 = 1177

    @staticmethod
    def delete(path, *, missing_ok=False):
        try:
            Path(path).unlink()
        except FileNotFoundError:
            if not missing_ok:
                raise


class WindowsRecoveryStateMachineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _repository(self):
        repository = object.__new__(WindowsExperimentRepository)
        repository.max_file_bytes = 1024 * 1024
        repository._api = _PortableNameApi()

        @contextmanager
        def hold_parent(_self, path):
            yield Path(path)

        def write_temp(_self, parent, payload):
            path = _self._temporary_path(parent, ".tmp")
            path.write_bytes(payload)
            return path

        def read_payload(_self, path):
            target = Path(path)
            payload = target.read_bytes()
            snapshot = hashlib.sha256(payload).hexdigest()
            return target, payload, snapshot

        def move_new(_self, source, target):
            source = Path(source)
            target = Path(target)
            if target.exists():
                raise FileExistsError(target)
            source.rename(target)

        def replace_file(_self, target, replacement, backup):
            os.replace(target, backup)
            os.replace(replacement, target)

        repository._hold_parent = types.MethodType(hold_parent, repository)
        repository._write_temp = types.MethodType(write_temp, repository)
        repository._read_payload = types.MethodType(read_payload, repository)
        repository._move_new_file = types.MethodType(move_new, repository)
        repository._replace_file = types.MethodType(replace_file, repository)
        return repository

    @staticmethod
    def _partial_replace_error():
        error = OSError(1177, "simulated ERROR_UNABLE_TO_MOVE_REPLACEMENT_2")
        error.winerror = 1177
        return error

    def test_initial_partial_replace_restores_original_and_keeps_local_copy(self):
        repository = self._repository()
        target = self.root / "initial.md"
        target.write_text("original", encoding="utf-8")
        _path, _payload, snapshot = repository._read_payload(target)

        def partial_replace(existing, _replacement, backup):
            os.replace(existing, backup)
            raise self._partial_replace_error()

        repository._replace_file = partial_replace
        with self.assertRaises(WindowsStorageCommitUncertainError) as raised:
            repository.write_text(target, "local", expected_snapshot=snapshot)

        self.assertEqual(target.read_text(encoding="utf-8"), "original")
        recovery = target.parent / raised.exception.recovery_name
        self.assertEqual(recovery.read_text(encoding="utf-8"), "local")

    def test_partial_rollback_restores_external_and_keeps_local_copy(self):
        repository = self._repository()
        target = self.root / "rollback.md"
        target.write_text("opened", encoding="utf-8")
        _path, _payload, snapshot = repository._read_payload(target)
        normal_replace = repository._replace_file
        calls = 0

        def race_then_partial_rollback(existing, replacement, backup):
            nonlocal calls
            calls += 1
            if calls == 1:
                Path(existing).write_text("external", encoding="utf-8")
                return normal_replace(existing, replacement, backup)
            os.replace(existing, backup)
            raise self._partial_replace_error()

        repository._replace_file = race_then_partial_rollback
        with self.assertRaises(WindowsStorageExternalModificationError) as raised:
            repository.write_text(target, "local", expected_snapshot=snapshot)

        self.assertEqual(target.read_text(encoding="utf-8"), "external")
        recovery = target.parent / raised.exception.recovery_name
        self.assertEqual(recovery.read_text(encoding="utf-8"), "local")

    def test_missing_parent_with_snapshot_is_typed_as_external_modification(self):
        repository = self._repository()
        target = self.root / "deleted" / "note.md"

        @contextmanager
        def missing_parent(_self, _path):
            raise FileNotFoundError("simulated deleted parent directory")
            yield  # pragma: no cover - keeps this a context manager generator

        repository._hold_parent = types.MethodType(missing_parent, repository)

        with self.assertRaises(WindowsStorageExternalModificationError) as raised:
            repository.write_text(
                target,
                "local edit",
                expected_snapshot="opened-snapshot",
            )

        self.assertIn("不可用", str(raised.exception))
        self.assertIsInstance(raised.exception.__cause__, FileNotFoundError)
        self.assertIsNone(raised.exception.recovery_name)

    def test_missing_parent_without_snapshot_keeps_original_error(self):
        repository = self._repository()
        target = self.root / "deleted" / "new-note.md"

        @contextmanager
        def missing_parent(_self, _path):
            raise FileNotFoundError("simulated deleted parent directory")
            yield  # pragma: no cover - keeps this a context manager generator

        repository._hold_parent = types.MethodType(missing_parent, repository)

        with self.assertRaises(FileNotFoundError) as raised:
            repository.write_text(target, "new document", exclusive=True)

        self.assertNotIsInstance(
            raised.exception,
            WindowsStorageExternalModificationError,
        )

    def test_write_failure_after_parent_entry_is_not_reclassified(self):
        repository = self._repository()
        target = self.root / "write-failure.md"

        def fail_write(_self, _parent, _payload):
            raise OSError("simulated disk write failure")

        repository._write_temp = types.MethodType(fail_write, repository)

        with self.assertRaises(OSError) as raised:
            repository.write_text(
                target,
                "local edit",
                expected_snapshot="opened-snapshot",
            )

        self.assertNotIsInstance(
            raised.exception,
            WindowsStorageExternalModificationError,
        )


if __name__ == "__main__":
    unittest.main()
