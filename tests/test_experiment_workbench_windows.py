import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from qt_experiment_storage_windows import (
    WindowsExperimentRepository,
    WindowsStorageCommitUncertainError,
    WindowsStorageExternalModificationError,
)


@unittest.skipUnless(os.name == "nt", "Windows handle backend tests")
class WindowsExperimentStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "records"
        self.repository = WindowsExperimentRepository(5 * 1024 * 1024)
        self.repository.set_root(self.root)

    def tearDown(self):
        self.repository.close()
        self.temp_dir.cleanup()

    def test_unc_and_device_namespaces_are_rejected_before_access(self):
        for path in (
            r"\\server\share\records",
            r"\\?\UNC\server\share\records",
            r"\\.\PhysicalDrive0",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.repository.set_root(path)

    def test_existing_junction_is_rejected(self):
        outside = Path(self.temp_dir.name) / "outside"
        outside.mkdir()
        junction = self.root / "junction"
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            self.skipTest(f"junction creation unavailable: {completed.stderr}")
        with self.assertRaises(ValueError):
            self.repository.read_text(junction / "secret.md", {".md"})

    def test_atomic_update_restores_external_edit_from_commit_boundary(self):
        target = self.root / "race.md"
        self.repository.write_text(target, "opened", exclusive=True)
        _path, _text, snapshot = self.repository.read_text(target, {".md"})
        original_replace = self.repository._replace_file
        first = True

        def race_then_replace(existing, replacement, backup):
            nonlocal first
            if first:
                first = False
                Path(existing).write_text("external", encoding="utf-8")
            return original_replace(existing, replacement, backup)

        with patch.object(
            self.repository, "_replace_file", side_effect=race_then_replace
        ):
            with self.assertRaises(WindowsStorageExternalModificationError):
                self.repository.write_text(
                    target,
                    "local",
                    expected_snapshot=snapshot,
                )

        self.assertEqual(target.read_text(encoding="utf-8"), "external")

    def test_exclusive_publish_never_overwrites_racing_creator(self):
        target = self.root / "new.md"
        original_move = self.repository._move_new_file

        def create_then_move(source, destination):
            Path(destination).write_text("external", encoding="utf-8")
            return original_move(source, destination)

        with patch.object(
            self.repository, "_move_new_file", side_effect=create_then_move
        ):
            with self.assertRaises(FileExistsError):
                self.repository.write_text(target, "local", exclusive=True)

        self.assertEqual(target.read_text(encoding="utf-8"), "external")

    def test_replace_error_1177_restores_original_and_preserves_local_edit(self):
        target = self.root / "recover.md"
        self.repository.write_text(target, "original", exclusive=True)
        _path, _text, snapshot = self.repository.read_text(target, {".md"})

        def simulate_partial_replace(existing, _replacement, backup):
            os.replace(existing, backup)
            error = OSError(1177, "simulated ERROR_UNABLE_TO_MOVE_REPLACEMENT_2")
            error.winerror = 1177
            raise error

        with patch.object(
            self.repository,
            "_replace_file",
            side_effect=simulate_partial_replace,
        ):
            with self.assertRaises(WindowsStorageCommitUncertainError) as raised:
                self.repository.write_text(
                    target,
                    "local edit",
                    expected_snapshot=snapshot,
                )

        self.assertEqual(target.read_text(encoding="utf-8"), "original")
        recovery = target.parent / raised.exception.recovery_name
        self.assertEqual(recovery.read_text(encoding="utf-8"), "local edit")

    def test_rollback_error_1177_restores_external_and_preserves_local_edit(self):
        target = self.root / "rollback-recover.md"
        self.repository.write_text(target, "opened", exclusive=True)
        _path, _text, snapshot = self.repository.read_text(target, {".md"})
        original_replace = self.repository._replace_file
        calls = 0

        def race_then_partial_rollback(existing, replacement, backup):
            nonlocal calls
            calls += 1
            if calls == 1:
                Path(existing).write_text("external", encoding="utf-8")
                return original_replace(existing, replacement, backup)

            # Emulate ERROR_UNABLE_TO_MOVE_REPLACEMENT_2 during the
            # compensating ReplaceFileW call: the local target has already
            # moved to the recovery name while the external version remains
            # under the backup name.
            os.replace(existing, backup)
            error = OSError(1177, "simulated rollback partial replace")
            error.winerror = 1177
            raise error

        with patch.object(
            self.repository,
            "_replace_file",
            side_effect=race_then_partial_rollback,
        ):
            with self.assertRaises(WindowsStorageExternalModificationError) as raised:
                self.repository.write_text(
                    target,
                    "local",
                    expected_snapshot=snapshot,
                )

        self.assertEqual(target.read_text(encoding="utf-8"), "external")
        recovery = target.parent / raised.exception.recovery_name
        self.assertEqual(recovery.read_text(encoding="utf-8"), "local")

    def test_open_parent_handle_blocks_replacing_directory_with_junction(self):
        guarded = self.root / "guarded"
        outside = Path(self.temp_dir.name) / "outside-race"
        guarded.mkdir()
        outside.mkdir()

        with self.repository._hold_parent(guarded / "note.md"):
            command = f'rmdir "{guarded}" & mklink /J "{guarded}" "{outside}"'
            completed = subprocess.run(
                ["cmd", "/d", "/c", command],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(guarded.is_dir())
        handle = self.repository._api.open_directory(guarded)
        try:
            info = self.repository._api.info(handle)
            self.assertFalse(
                int(info.dwFileAttributes)
                & self.repository._api.FILE_ATTRIBUTE_REPARSE_POINT
            )
        finally:
            self.repository._api.close(handle)


if __name__ == "__main__":
    unittest.main()
