"""Hardened local experiment storage for Windows.

The implementation uses Win32 handles instead of validating a path and then
re-opening it later.  Every directory component is opened with
``FILE_FLAG_OPEN_REPARSE_POINT`` and held without ``FILE_SHARE_DELETE`` while
an operation is in progress.  Existing documents are replaced with
``ReplaceFileW`` and a backup, allowing a concurrent external edit to be
detected and restored without silently discarding either version.
"""

from __future__ import annotations

from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path
import secrets


class WindowsStorageExternalModificationError(OSError):
    def __init__(self, message, recovery_name=None):
        super().__init__(message)
        self.recovery_name = recovery_name


class WindowsStorageCommitUncertainError(OSError):
    def __init__(self, recovery_name, message=None):
        super().__init__(
            message or "Windows 原子替换结果需要人工确认，请检查保留的恢复文件"
        )
        self.recovery_name = recovery_name


class _WindowsReplaceError(OSError):
    def __init__(self, number, message):
        super().__init__(number, message)
        self.winerror = int(number)


class _ByHandleFileInformation(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", wintypes.FILETIME),
        ("ftLastAccessTime", wintypes.FILETIME),
        ("ftLastWriteTime", wintypes.FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


class _Win32FileApi:
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    FILE_READ_ATTRIBUTES = 0x0080
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    OPEN_EXISTING = 3
    OPEN_ALWAYS = 4
    CREATE_NEW = 1
    FILE_ATTRIBUTE_NORMAL = 0x00000080
    FILE_ATTRIBUTE_TEMPORARY = 0x00000100
    FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILE_FLAG_SEQUENTIAL_SCAN = 0x08000000
    FILE_FLAG_WRITE_THROUGH = 0x80000000
    MOVEFILE_WRITE_THROUGH = 0x00000008
    REPLACEFILE_WRITE_THROUGH = 0x00000001
    DRIVE_REMOTE = 4
    ERROR_FILE_EXISTS = 80
    ERROR_ALREADY_EXISTS = 183
    ERROR_UNABLE_TO_REMOVE_REPLACED = 1175
    ERROR_UNABLE_TO_MOVE_REPLACEMENT = 1176
    ERROR_UNABLE_TO_MOVE_REPLACEMENT_2 = 1177
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    def __init__(self):
        if os.name != "nt" or not hasattr(ctypes, "WinDLL"):
            raise RuntimeError("Windows 实验存储后端只能在 Windows 上使用")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._configure_signatures()

    def _configure_signatures(self):
        k32 = self.kernel32
        k32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        k32.CreateFileW.restype = wintypes.HANDLE
        k32.CloseHandle.argtypes = [wintypes.HANDLE]
        k32.CloseHandle.restype = wintypes.BOOL
        k32.GetFileInformationByHandle.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(_ByHandleFileInformation),
        ]
        k32.GetFileInformationByHandle.restype = wintypes.BOOL
        k32.GetFinalPathNameByHandleW.argtypes = [
            wintypes.HANDLE,
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        k32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
        k32.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
        k32.GetDriveTypeW.restype = wintypes.UINT
        k32.ReadFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        k32.ReadFile.restype = wintypes.BOOL
        k32.WriteFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPCVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        k32.WriteFile.restype = wintypes.BOOL
        k32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
        k32.FlushFileBuffers.restype = wintypes.BOOL
        k32.ReplaceFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.LPVOID,
        ]
        k32.ReplaceFileW.restype = wintypes.BOOL
        k32.MoveFileExW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
        k32.MoveFileExW.restype = wintypes.BOOL
        k32.DeleteFileW.argtypes = [wintypes.LPCWSTR]
        k32.DeleteFileW.restype = wintypes.BOOL

    @staticmethod
    def _native_path(path) -> str:
        value = os.path.abspath(os.fspath(path))
        if value.startswith("\\\\?\\"):
            return value
        return "\\\\?\\" + value

    @staticmethod
    def _error(message):
        number = ctypes.get_last_error()
        raise OSError(number, f"{message}: {ctypes.FormatError(number).strip()}")

    def open_handle(self, path, access, share, disposition, flags):
        handle = self.kernel32.CreateFileW(
            self._native_path(path),
            access,
            share,
            None,
            disposition,
            flags,
            None,
        )
        if handle == self.INVALID_HANDLE_VALUE:
            number = ctypes.get_last_error()
            if disposition == self.CREATE_NEW and number in (
                self.ERROR_FILE_EXISTS,
                self.ERROR_ALREADY_EXISTS,
            ):
                raise FileExistsError(os.fspath(path))
            self._error(f"无法打开 {Path(path).name or path}")
        return handle

    def open_directory(self, path):
        return self.open_handle(
            path,
            self.FILE_READ_ATTRIBUTES,
            # Freeze the directory against write-handle operations such as
            # converting an empty directory into a junction after validation.
            self.FILE_SHARE_READ,
            self.OPEN_EXISTING,
            self.FILE_FLAG_BACKUP_SEMANTICS | self.FILE_FLAG_OPEN_REPARSE_POINT,
        )

    def open_read(self, path):
        return self.open_handle(
            path,
            self.GENERIC_READ,
            self.FILE_SHARE_READ,
            self.OPEN_EXISTING,
            self.FILE_ATTRIBUTE_NORMAL
            | self.FILE_FLAG_OPEN_REPARSE_POINT
            | self.FILE_FLAG_SEQUENTIAL_SCAN,
        )

    def open_lock(self, path):
        return self.open_handle(
            path,
            self.GENERIC_READ | self.GENERIC_WRITE,
            self.FILE_SHARE_READ,
            self.OPEN_ALWAYS,
            self.FILE_ATTRIBUTE_NORMAL | self.FILE_FLAG_OPEN_REPARSE_POINT,
        )

    def create_temp(self, path):
        return self.open_handle(
            path,
            self.GENERIC_WRITE,
            self.FILE_SHARE_READ,
            self.CREATE_NEW,
            self.FILE_ATTRIBUTE_TEMPORARY | self.FILE_FLAG_WRITE_THROUGH,
        )

    def close(self, handle):
        if handle not in (None, self.INVALID_HANDLE_VALUE):
            self.kernel32.CloseHandle(handle)

    def info(self, handle):
        result = _ByHandleFileInformation()
        if not self.kernel32.GetFileInformationByHandle(handle, ctypes.byref(result)):
            self._error("无法读取 Windows 文件标识")
        return result

    @staticmethod
    def identity(info):
        file_index = (int(info.nFileIndexHigh) << 32) | int(info.nFileIndexLow)
        return int(info.dwVolumeSerialNumber), file_index

    @staticmethod
    def snapshot_fields(info):
        size = (int(info.nFileSizeHigh) << 32) | int(info.nFileSizeLow)
        modified = (
            (int(info.ftLastWriteTime.dwHighDateTime) << 32)
            | int(info.ftLastWriteTime.dwLowDateTime)
        )
        return (*_Win32FileApi.identity(info), size, modified * 100)

    def final_path(self, handle) -> str:
        needed = self.kernel32.GetFinalPathNameByHandleW(handle, None, 0, 0)
        if not needed:
            self._error("无法解析 Windows 文件最终路径")
        buffer = ctypes.create_unicode_buffer(needed + 1)
        written = self.kernel32.GetFinalPathNameByHandleW(
            handle, buffer, len(buffer), 0
        )
        if not written or written >= len(buffer):
            self._error("无法解析 Windows 文件最终路径")
        value = buffer.value
        if value.startswith("\\\\?\\UNC\\"):
            return "\\\\" + value[8:]
        if value.startswith("\\\\?\\"):
            return value[4:]
        return value

    def drive_type(self, root: str) -> int:
        return int(self.kernel32.GetDriveTypeW(root))

    def read_all(self, handle, limit: int) -> bytes:
        chunks = []
        total = 0
        while True:
            allowed = min(64 * 1024, limit + 1 - total)
            if allowed <= 0:
                raise ValueError("文件超过 5 MiB，已拒绝在编辑器中打开")
            buffer = ctypes.create_string_buffer(allowed)
            count = wintypes.DWORD()
            if not self.kernel32.ReadFile(
                handle, buffer, allowed, ctypes.byref(count), None
            ):
                self._error("无法读取实验记录")
            if count.value == 0:
                break
            chunks.append(buffer.raw[: count.value])
            total += int(count.value)
            if total > limit:
                raise ValueError("文件超过 5 MiB，已拒绝在编辑器中打开")
        return b"".join(chunks)

    def write_all(self, handle, payload: bytes):
        offset = 0
        while offset < len(payload):
            chunk = payload[offset : offset + 64 * 1024]
            buffer = ctypes.create_string_buffer(chunk)
            count = wintypes.DWORD()
            if not self.kernel32.WriteFile(
                handle, buffer, len(chunk), ctypes.byref(count), None
            ):
                self._error("无法写入实验记录")
            if count.value <= 0:
                raise OSError("实验记录写入不完整")
            offset += int(count.value)
        if not self.kernel32.FlushFileBuffers(handle):
            self._error("无法同步实验记录到磁盘")

    def move_new(self, source, target):
        if not self.kernel32.MoveFileExW(
            self._native_path(source),
            self._native_path(target),
            self.MOVEFILE_WRITE_THROUGH,
        ):
            number = ctypes.get_last_error()
            if number in (self.ERROR_FILE_EXISTS, self.ERROR_ALREADY_EXISTS):
                raise FileExistsError(os.fspath(target))
            self._error("无法发布新的实验记录")

    def replace(self, target, replacement, backup):
        if not self.kernel32.ReplaceFileW(
            self._native_path(target),
            self._native_path(replacement),
            self._native_path(backup),
            # REPLACEFILE_WRITE_THROUGH is documented as unsupported. The
            # replacement contents were already flushed before publication.
            0,
            None,
            None,
        ):
            number = ctypes.get_last_error()
            raise _WindowsReplaceError(
                number,
                f"无法原子替换实验记录: {ctypes.FormatError(number).strip()}",
            )

    def delete(self, path, *, missing_ok=False):
        if self.kernel32.DeleteFileW(self._native_path(path)):
            return
        number = ctypes.get_last_error()
        if missing_ok and number == 2:
            return
        self._error("无法删除临时实验文件")


class WindowsExperimentRepository:
    """Local-only, handle-validated repository used by Windows builds."""

    LOCK_NAME = ".dclocking-experiment.lock"
    _RESERVED_NAMES = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }

    def __init__(self, max_file_bytes: int, api=None):
        self.max_file_bytes = int(max_file_bytes)
        self._api = api or _Win32FileApi()
        self.root: Path | None = None
        self._root_handle = None
        self._root_identity = None
        self._root_final_normalized = None

    @staticmethod
    def _reject_remote_or_device_path(path):
        raw = os.fspath(path).strip().replace("/", "\\")
        folded = raw.casefold()
        if (
            raw.startswith("\\\\")
            or folded.startswith("\\?\\")
            or folded.startswith("\\.\\")
            or folded.startswith("\\??\\")
        ):
            raise ValueError("实验仓库仅支持本机磁盘，不允许 UNC、设备或网络路径")

    @classmethod
    def _validate_component(cls, value: str):
        if (
            not value
            or value in (".", "..")
            or value.endswith((" ", "."))
            or any(mark in value for mark in ("/", "\\", "\x00", ":"))
        ):
            raise ValueError("实验文件路径包含 Windows 不安全名称")
        stem = value.split(".", 1)[0].upper()
        if stem in cls._RESERVED_NAMES:
            raise ValueError("实验文件路径使用了 Windows 保留设备名")

    @staticmethod
    def _normalized(path) -> str:
        return os.path.normcase(os.path.abspath(os.fspath(path)))

    def _assert_local_drive(self, path):
        drive, _tail = os.path.splitdrive(os.path.abspath(os.fspath(path)))
        if not drive:
            raise ValueError("实验仓库必须位于本机盘符下")
        if self._api.drive_type(drive + "\\") == self._api.DRIVE_REMOTE:
            raise ValueError("实验仓库不能位于映射网络盘")

    def _inspect_directory(self, handle):
        info = self._api.info(handle)
        attributes = int(info.dwFileAttributes)
        if attributes & self._api.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("实验仓库路径不允许 Windows junction 或重解析点")
        if not attributes & self._api.FILE_ATTRIBUTE_DIRECTORY:
            raise ValueError("实验仓库路径不是文件夹")
        return info

    def _open_directory_chain(self, path, *, create_missing=False):
        absolute = Path(os.path.abspath(os.fspath(path)))
        drive, _tail = os.path.splitdrive(str(absolute))
        if not drive:
            raise ValueError("实验仓库必须位于本机盘符下")
        handles = []
        current = Path(drive + "\\")
        try:
            root_handle = self._api.open_directory(current)
            self._inspect_directory(root_handle)
            handles.append(root_handle)
            relative = os.path.relpath(str(absolute), str(current))
            if relative != ".":
                for part in Path(relative).parts:
                    self._validate_component(part)
                    current /= part
                    try:
                        handle = self._api.open_directory(current)
                    except OSError as exc:
                        error_number = getattr(exc, "winerror", None) or exc.errno
                        if not create_missing or error_number not in (2, 3):
                            raise
                        try:
                            current.mkdir()
                        except FileExistsError:
                            pass
                        handle = self._api.open_directory(current)
                    self._inspect_directory(handle)
                    handles.append(handle)
            return handles
        except Exception:
            for handle in reversed(handles):
                self._api.close(handle)
            raise

    def set_root(self, root) -> Path:
        self._reject_remote_or_device_path(root)
        requested = Path(root).expanduser()
        requested = Path(os.path.abspath(os.fspath(requested)))
        self._assert_local_drive(requested)
        handles = self._open_directory_chain(requested, create_missing=True)
        root_handle = handles[-1]
        try:
            info = self._inspect_directory(root_handle)
            final = Path(self._api.final_path(root_handle))
            self._assert_local_drive(final)
        except Exception:
            for handle in reversed(handles):
                self._api.close(handle)
            raise
        for handle in reversed(handles[:-1]):
            self._api.close(handle)
        old_handle = self._root_handle
        self.root = final
        self._root_handle = root_handle
        self._root_identity = self._api.identity(info)
        self._root_final_normalized = self._normalized(final)
        self._api.close(old_handle)
        return final

    def close(self):
        self._api.close(self._root_handle)
        self._root_handle = None

    def require_root(self) -> Path:
        if self.root is None or self._root_handle is None:
            raise ValueError("实验仓库尚未初始化，请先切换仓库")
        stored = self._inspect_directory(self._root_handle)
        handles = self._open_directory_chain(self.root)
        try:
            visible = self._inspect_directory(handles[-1])
            if (
                self._api.identity(stored) != self._root_identity
                or self._api.identity(visible) != self._root_identity
                or self._normalized(self._api.final_path(handles[-1]))
                != self._root_final_normalized
            ):
                raise ValueError("当前实验仓库路径已发生变化，请重新选择仓库")
        finally:
            for handle in reversed(handles):
                self._api.close(handle)
        return self.root

    def relative_parts(self, path) -> tuple[str, ...]:
        root = self.require_root()
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = Path(os.path.abspath(os.fspath(candidate)))
        root_text = self._normalized(root)
        candidate_text = self._normalized(candidate)
        try:
            if os.path.commonpath((root_text, candidate_text)) != root_text:
                raise ValueError
            relative = os.path.relpath(candidate_text, root_text)
        except ValueError as exc:
            raise ValueError("文件不在当前实验仓库内") from exc
        parts = Path(relative).parts
        if relative == "." or not parts:
            raise ValueError("实验文件路径无效")
        for part in parts:
            self._validate_component(part)
        return tuple(parts)

    @contextmanager
    def _hold_parent(self, path):
        root = self.require_root()
        parts = self.relative_parts(path)
        handles = self._open_directory_chain(root)
        try:
            if self._api.identity(self._api.info(handles[-1])) != self._root_identity:
                raise ValueError("当前实验仓库路径已发生变化，请重新选择仓库")
            current = root
            for part in parts[:-1]:
                current /= part
                handle = self._api.open_directory(current)
                self._inspect_directory(handle)
                final = self._normalized(self._api.final_path(handle))
                if os.path.commonpath((self._root_final_normalized, final)) != self._root_final_normalized:
                    self._api.close(handle)
                    raise ValueError("实验文件父目录逃逸出当前仓库")
                handles.append(handle)
            yield current / parts[-1]
        finally:
            for handle in reversed(handles):
                self._api.close(handle)

    def ensure_directory(self, name: str) -> Path:
        self._validate_component(name)
        root = self.require_root()
        target = root / name
        with self._hold_parent(target):
            try:
                target.mkdir()
            except FileExistsError:
                pass
            handle = self._api.open_directory(target)
            try:
                self._inspect_directory(handle)
                final = self._normalized(self._api.final_path(handle))
                if os.path.commonpath((self._root_final_normalized, final)) != self._root_final_normalized:
                    raise ValueError("实验记录目录逃逸出当前仓库")
            finally:
                self._api.close(handle)
        return target

    @contextmanager
    def write_lock(self):
        root = self.require_root()
        lock_path = root / self.LOCK_NAME
        with self._hold_parent(lock_path):
            try:
                handle = self._api.open_lock(lock_path)
            except OSError as exc:
                raise OSError("另一个 DClocking 工作台正在保存，请稍后重试") from exc
            try:
                info = self._api.info(handle)
                attributes = int(info.dwFileAttributes)
                if (
                    attributes & self._api.FILE_ATTRIBUTE_REPARSE_POINT
                    or attributes & self._api.FILE_ATTRIBUTE_DIRECTORY
                ):
                    raise ValueError("实验仓库锁文件不是普通文件")
                yield
            finally:
                self._api.close(handle)

    def _read_payload(self, path):
        with self._hold_parent(path) as target:
            handle = self._api.open_read(target)
            try:
                before = self._api.info(handle)
                attributes = int(before.dwFileAttributes)
                if attributes & self._api.FILE_ATTRIBUTE_REPARSE_POINT:
                    raise ValueError("实验仓库内不允许 Windows 重解析点")
                if attributes & self._api.FILE_ATTRIBUTE_DIRECTORY:
                    raise ValueError("选择的路径不是普通文件")
                before_fields = self._api.snapshot_fields(before)
                if before_fields[2] > self.max_file_bytes:
                    raise ValueError("文件超过 5 MiB，已拒绝在编辑器中打开")
                final = self._normalized(self._api.final_path(handle))
                if os.path.commonpath((self._root_final_normalized, final)) != self._root_final_normalized:
                    raise ValueError("实验文件逃逸出当前仓库")
                payload = self._api.read_all(handle, self.max_file_bytes)
                after = self._api.info(handle)
                after_fields = self._api.snapshot_fields(after)
                if before_fields != after_fields:
                    raise OSError("文件在读取过程中被修改，请重试")
            finally:
                self._api.close(handle)
        snapshot = (*after_fields, hashlib.sha256(payload).hexdigest())
        return target, payload, snapshot

    def read_text(self, path, supported_suffixes):
        target = Path(path)
        if target.suffix.lower() not in supported_suffixes:
            raise ValueError("仅支持 Markdown、TXT、CSV、JSON、YAML 和日志文本")
        target, payload, snapshot = self._read_payload(target)
        if b"\x00" in payload:
            raise ValueError("检测到二进制内容，无法作为实验文本打开")
        try:
            text = payload.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("文件不是有效的 UTF-8 文本") from exc
        return target, text, snapshot

    def _temporary_path(self, parent: Path, suffix: str) -> Path:
        for _attempt in range(32):
            candidate = parent / f".dclocking-{secrets.token_hex(12)}{suffix}"
            if not candidate.exists():
                return candidate
        raise OSError("无法分配实验记录临时文件名")

    def _write_temp(self, parent: Path, payload: bytes) -> Path:
        for _attempt in range(32):
            path = self._temporary_path(parent, ".tmp")
            try:
                handle = self._api.create_temp(path)
            except FileExistsError:
                continue
            try:
                self._api.write_all(handle, payload)
            except Exception:
                self._api.close(handle)
                self._api.delete(path, missing_ok=True)
                raise
            self._api.close(handle)
            return path
        raise OSError("无法创建实验记录临时文件")

    def _move_new_file(self, source, target):
        self._api.move_new(source, target)

    def _replace_file(self, target, replacement, backup):
        self._api.replace(target, replacement, backup)

    def _preserve_replacement(self, source: Path, target: Path) -> Path:
        """Move a local edit to a visible, collision-safe recovery filename."""

        for _attempt in range(32):
            recovery = target.with_name(
                f"{target.stem}-恢复副本-{secrets.token_hex(6)}{target.suffix}"
            )
            try:
                self._move_new_file(source, recovery)
            except FileExistsError:
                continue
            return recovery
        raise OSError("无法为本地编辑版本分配恢复文件名")

    def _snapshot_matches_payload(self, path, payload):
        _target, disk_payload, _snapshot = self._read_payload(path)
        return disk_payload == payload

    def write_text(self, path, text: str, *, exclusive=False, expected_snapshot=None):
        payload = text.encode("utf-8")
        if len(payload) > self.max_file_bytes:
            raise ValueError("实验记录超过 5 MiB，已拒绝保存")

        with self._hold_parent(path) as target:
            parent = target.parent
            temp = self._write_temp(parent, payload)
            temp_exists = True
            backup = self._temporary_path(parent, ".backup")
            try:
                if exclusive:
                    self._move_new_file(temp, target)
                    temp_exists = False
                    return target

                if expected_snapshot is not None:
                    try:
                        _current, _current_payload, current_snapshot = self._read_payload(target)
                    except (OSError, ValueError) as exc:
                        raise WindowsStorageExternalModificationError(
                            "原文件目录或内容已不可用"
                        ) from exc
                    if current_snapshot != expected_snapshot:
                        raise WindowsStorageExternalModificationError("文件已在外部修改")

                try:
                    self._replace_file(target, temp, backup)
                except OSError as exc:
                    error_number = int(
                        getattr(exc, "winerror", 0) or getattr(exc, "errno", 0) or 0
                    )
                    if error_number == self._api.ERROR_UNABLE_TO_MOVE_REPLACEMENT_2:
                        # Per ReplaceFileW's contract, the original is now the
                        # backup and the local replacement is still at temp.
                        # Restore the original path first, then retain the local
                        # version under a visible recovery name.
                        temp_exists = False
                        try:
                            self._move_new_file(backup, target)
                        except OSError as restore_error:
                            raise WindowsStorageCommitUncertainError(
                                backup.name,
                                "Windows 替换中断；原版本和本地版本均已保留，"
                                f"请检查 {backup.name} 与 {temp.name}",
                            ) from restore_error
                        try:
                            recovery = self._preserve_replacement(temp, target)
                        except OSError as preserve_error:
                            raise WindowsStorageCommitUncertainError(
                                temp.name,
                                "原文件已恢复，但本地编辑仍保留在临时恢复文件中",
                            ) from preserve_error
                        raise WindowsStorageCommitUncertainError(
                            recovery.name,
                            "原文件已恢复，本地编辑已保留为恢复副本",
                        ) from exc

                    # Other documented ReplaceFileW failures retain the target
                    # and replacement names. If reality differs, preserve the
                    # local edit instead of deleting the only remaining copy.
                    if backup.exists() or not target.exists():
                        try:
                            recovery = self._preserve_replacement(temp, target)
                        except OSError:
                            recovery = temp
                        temp_exists = False
                        raise WindowsStorageCommitUncertainError(
                            recovery.name,
                            "Windows 返回了非标准替换状态；本地编辑已保留",
                        ) from exc
                    if expected_snapshot is not None:
                        try:
                            _current, _payload, current_snapshot = self._read_payload(target)
                        except (OSError, ValueError) as read_error:
                            try:
                                recovery = self._preserve_replacement(temp, target)
                            except OSError:
                                recovery = temp
                            temp_exists = False
                            raise WindowsStorageCommitUncertainError(
                                recovery.name,
                                "替换失败后无法确认原文件状态",
                            ) from read_error
                        if current_snapshot != expected_snapshot:
                            raise WindowsStorageExternalModificationError(
                                "文件在提交前被其他程序修改"
                            ) from exc
                    raise
                temp_exists = False

                try:
                    _old_target, _old_payload, replaced_snapshot = self._read_payload(backup)
                except (OSError, ValueError) as exc:
                    raise WindowsStorageCommitUncertainError(backup.name) from exc

                if expected_snapshot is not None and replaced_snapshot != expected_snapshot:
                    recovery = self._temporary_path(parent, ".recovery")
                    try:
                        self._replace_file(target, backup, recovery)
                    except OSError as exc:
                        error_number = getattr(exc, "winerror", None)
                        if error_number is None:
                            error_number = getattr(exc, "errno", None)
                        if error_number != self._api.ERROR_UNABLE_TO_MOVE_REPLACEMENT_2:
                            raise WindowsStorageCommitUncertainError(
                                backup.name,
                                "回滚外部修改时 Windows 返回错误；"
                                f"请检查 {target.name}、{backup.name} 与 {recovery.name}",
                            ) from exc

                        # ReplaceFileW error 1177 is a documented partial
                        # state: target was moved to ``recovery`` while the
                        # replacement remains at ``backup``.  Restore the
                        # external version to its requested name, then expose
                        # the displaced local edit as a visible recovery copy.
                        try:
                            self._move_new_file(backup, target)
                        except OSError as restore_error:
                            raise WindowsStorageCommitUncertainError(
                                backup.name,
                                "回滚被中断；外部版本和本地版本均已保留，"
                                f"请检查 {backup.name} 与 {recovery.name}",
                            ) from restore_error
                        try:
                            visible_recovery = self._preserve_replacement(
                                recovery, target
                            )
                        except OSError as preserve_error:
                            raise WindowsStorageCommitUncertainError(
                                recovery.name,
                                "外部版本已恢复，但本地版本仍位于临时恢复文件",
                            ) from preserve_error
                        raise WindowsStorageExternalModificationError(
                            "文件在提交瞬间被外部修改；外部版本已恢复",
                            recovery_name=visible_recovery.name,
                        ) from exc
                    recovery_name = None
                    try:
                        if self._snapshot_matches_payload(recovery, payload):
                            self._api.delete(recovery, missing_ok=True)
                        else:
                            recovery_name = recovery.name
                    except (OSError, ValueError):
                        recovery_name = recovery.name
                    raise WindowsStorageExternalModificationError(
                        "文件已在提交瞬间被外部修改",
                        recovery_name=recovery_name,
                    )

                try:
                    self._api.delete(backup, missing_ok=True)
                except OSError:
                    # The committed target is already durable and the backup
                    # only contains the verified previous version.  Leaving a
                    # recovery artifact is safer than reporting a false write
                    # failure after successful publication.
                    pass
                return target
            finally:
                if temp_exists:
                    self._api.delete(temp, missing_ok=True)
