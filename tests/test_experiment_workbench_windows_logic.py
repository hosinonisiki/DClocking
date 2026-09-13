"""Platform-neutral tests for the Windows ReplaceFileW recovery state machine.

The real handle and junction tests run only on Windows.  These tests emulate
the documented file-name transitions so macOS development still exercises the
data-preservation branches on every local run.
"""

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import tempfile
import types
import unittest

from tests import qt_test_support  # noqa: F401 - installs project import paths
from qt_experiment_storage_windows import (
    WindowsExperimentRepository,
    WindowsStorageCommitUncertainError,
    WindowsStorageExternalModificationError,
)


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


if __name__ == "__main__":
    unittest.main()
