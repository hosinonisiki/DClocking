"""OS-backed LLM credential storage for the FPGA Agent.

Public settings remain in ``config.json``.  The API key is stored through the
system credential service (Windows Credential Manager/macOS Keychain) via
``keyring`` and can also be supplied ephemerally through an environment
variable for CI or managed deployments.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
from urllib.parse import urlparse


SERVICE_NAME = "DClocking FPGA Agent"
# Legacy unscoped account name. New credentials derive an account from the
# normalized API origin so one provider's key is never reused for another.
ACCOUNT_NAME = "llm-api-key"
ENVIRONMENT_KEY = "DCLOCKING_LLM_API_KEY"
ENVIRONMENT_ENDPOINT = "DCLOCKING_LLM_API_ENDPOINT"
DEFAULT_ENDPOINT = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o"


class SecretStoreError(RuntimeError):
    pass


def _is_windows() -> bool:
    return os.name == "nt"


def _system_keyring():
    try:
        import keyring
    except ImportError:
        return None
    return keyring


def _read_config(path: Path) -> dict:
    if not path.exists():
        return {"llm": {}, "agent": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Agent 配置文件不是有效 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("Agent 配置文件顶层必须是对象")
    if not isinstance(value.get("llm", {}), dict):
        raise ValueError("Agent 配置中的 llm 必须是对象")
    return value


def _atomic_write_public_config(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
            0o600,
        )
        try:
            payload = json.dumps(config, ensure_ascii=False, indent=2).encode("utf-8")
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("Agent 配置写入不完整")
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def validate_endpoint(value: str) -> str:
    endpoint = str(value or DEFAULT_ENDPOINT).strip().rstrip("/")
    if not endpoint or any(mark in endpoint for mark in ("\r", "\n", "\x00")):
        raise ValueError("API Endpoint 无效")
    parsed = urlparse(endpoint)
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("API Endpoint 必须是无内嵌凭据的完整 URL")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("API Endpoint 端口无效") from exc
    if parsed.params or parsed.query or parsed.fragment:
        raise ValueError("API Endpoint 不允许参数、查询字符串或片段")
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in local_hosts
    ):
        raise ValueError("API Endpoint 必须使用 HTTPS；仅本机服务允许 HTTP")

    # Use one canonical spelling for both credential lookup and environment
    # binding.  In particular, host case, a trailing slash and an explicit
    # default port must not create accidental credential aliases.
    scheme = parsed.scheme.casefold()
    host = parsed.hostname.casefold()
    if ":" in host:
        host = f"[{host}]"
    default_port = 443 if scheme == "https" else 80
    port = "" if parsed.port in (None, default_port) else f":{parsed.port}"
    path = parsed.path.rstrip("/")
    return f"{scheme}://{host}{port}{path}"


def _environment_key_for_endpoint(endpoint: str) -> tuple[str, str]:
    """Return a managed key only when it is explicitly bound to *endpoint*."""

    key = validate_api_key(os.environ.get(ENVIRONMENT_KEY, ""))
    if not key:
        return "", ""
    bound_value = os.environ.get(ENVIRONMENT_ENDPOINT, "").strip()
    if not bound_value:
        return "", (
            f"检测到 {ENVIRONMENT_KEY}，但未设置 {ENVIRONMENT_ENDPOINT}；"
            "为避免将密钥发送到错误服务，本次已忽略该环境密钥。"
        )
    try:
        bound_endpoint = validate_endpoint(bound_value)
    except ValueError:
        return "", (
            f"{ENVIRONMENT_ENDPOINT} 无效；为避免将密钥发送到错误服务，"
            "本次已忽略环境密钥。"
        )
    if bound_endpoint != validate_endpoint(endpoint):
        return "", (
            "环境 API Key 绑定的 Endpoint 与当前设置不一致；"
            "本次已忽略环境密钥。"
        )
    return key, ""


def credential_account(endpoint: str) -> str:
    """Return a stable, non-secret keyring account for one API origin."""

    parsed = urlparse(validate_endpoint(endpoint))
    host = parsed.hostname.casefold()
    if ":" in host:
        host = f"[{host}]"
    default_port = 443 if parsed.scheme == "https" else 80
    origin = f"{parsed.scheme}://{host}"
    if parsed.port is not None and parsed.port != default_port:
        origin += f":{parsed.port}"
    digest = hashlib.sha256(origin.encode("utf-8")).hexdigest()[:24]
    return f"{ACCOUNT_NAME}:{digest}"


def validate_model(value: str) -> str:
    model = str(value or DEFAULT_MODEL).strip()
    if not model or len(model) > 160 or any(mark in model for mark in ("\r", "\n", "\x00")):
        raise ValueError("模型名称无效")
    return model


def validate_api_key(value: str) -> str:
    key = str(value or "").strip()
    if len(key) > 4096 or any(mark in key for mark in ("\r", "\n", "\x00")):
        raise ValueError("API Key 包含非法控制字符或长度异常")
    return key


def load_agent_configuration(config_path, *, keyring_backend=None):
    """Return ``(public_config, api_key, warning)`` and migrate legacy keys."""

    path = Path(config_path)
    config = _read_config(path)
    llm = config.setdefault("llm", {})
    endpoint = validate_endpoint(llm.get("endpoint", DEFAULT_ENDPOINT))
    model = validate_model(llm.get("model", DEFAULT_MODEL))
    llm["endpoint"] = endpoint
    llm["model"] = model

    environment_key, environment_warning = _environment_key_for_endpoint(endpoint)
    backend = keyring_backend if keyring_backend is not None else _system_keyring()
    legacy_key = validate_api_key(llm.get("api_key", ""))
    account = credential_account(endpoint)
    stored_key = ""
    warning = ""
    if backend is not None:
        try:
            stored_key = validate_api_key(
                backend.get_password(SERVICE_NAME, account) or ""
            )
            if legacy_key:
                backend.set_password(SERVICE_NAME, account, legacy_key)
                llm.pop("api_key", None)
                _atomic_write_public_config(path, config)
                # Do not publish the migrated credential to the running Agent
                # until the plaintext copy has been removed from disk.
                stored_key = legacy_key
                warning = "已将旧版明文 API Key 迁移到当前 API 服务的系统凭据存储。"
            elif not stored_key:
                unscoped = validate_api_key(
                    backend.get_password(SERVICE_NAME, ACCOUNT_NAME) or ""
                )
                if unscoped:
                    warning = (
                        "检测到旧版未绑定服务的系统密钥；为避免发往错误服务，"
                        "本次不会使用，请在设置中为当前 Endpoint 重新输入。"
                    )
        except Exception as exc:
            if legacy_key:
                if _is_windows():
                    # A keyring write may have succeeded before the public
                    # config rewrite failed.  Windows stays fail-closed while
                    # plaintext is still present on disk.
                    stored_key = ""
                    warning = (
                        "Windows Credential Manager 暂不可用；为避免明文密钥泄露，"
                        "Agent 已禁用，请修复 keyring 后重新启动。"
                    )
                else:
                    try:
                        path.chmod(0o600)
                    except OSError:
                        pass
                    warning = "系统凭据存储暂不可用；旧密钥仅用于本次会话，尚未完成迁移。"
                    stored_key = legacy_key
            else:
                warning = f"系统凭据存储不可用：{exc}"
    elif legacy_key:
        if _is_windows():
            warning = (
                "Windows 缺少 keyring，不能安全读取旧版明文密钥；"
                "Agent 已禁用，请安装依赖后重新启动。"
            )
        else:
            try:
                path.chmod(0o600)
            except OSError:
                pass
            stored_key = legacy_key
            warning = "缺少 keyring，旧密钥仅用于本次会话；请安装依赖后重新启动以完成迁移。"

    if environment_warning:
        warning = f"{warning}\n{environment_warning}" if warning else environment_warning
    return config, environment_key or stored_key, warning


def save_agent_settings(
    config_path,
    *,
    endpoint: str,
    api_key: str,
    model: str,
    keyring_backend=None,
):
    path = Path(config_path)
    config = _read_config(path)
    llm = config.setdefault("llm", {})
    legacy_key = validate_api_key(llm.get("api_key", ""))
    previous_endpoint = validate_endpoint(llm.get("endpoint", DEFAULT_ENDPOINT))
    llm["endpoint"] = validate_endpoint(endpoint)
    llm["model"] = validate_model(model)
    account = credential_account(llm["endpoint"])

    entered_key = validate_api_key(api_key)
    backend = keyring_backend if keyring_backend is not None else _system_keyring()
    if entered_key:
        if backend is None:
            raise SecretStoreError("系统凭据组件 keyring 未安装，无法安全保存 API Key")
        try:
            backend.set_password(SERVICE_NAME, account, entered_key)
        except Exception as exc:
            raise SecretStoreError(f"系统凭据存储写入失败：{exc}") from exc
    elif legacy_key:
        if backend is None:
            raise SecretStoreError(
                "旧版配置仍含明文 API Key；请先安装 keyring 并重新启动完成迁移"
            )
        if credential_account(previous_endpoint) != account:
            raise SecretStoreError(
                "API Endpoint 已改变；为避免复用其他服务的密钥，请重新输入 API Key"
            )
        try:
            backend.set_password(SERVICE_NAME, account, legacy_key)
        except Exception as exc:
            raise SecretStoreError(f"旧版 API Key 迁移失败：{exc}") from exc

    llm.pop("api_key", None)

    _atomic_write_public_config(path, config)
    environment_key, _environment_warning = _environment_key_for_endpoint(
        llm["endpoint"]
    )
    stored_key = ""
    if backend is not None:
        try:
            stored_key = validate_api_key(
                backend.get_password(SERVICE_NAME, account) or ""
            )
        except Exception as exc:
            raise SecretStoreError(f"系统凭据存储读取失败：{exc}") from exc
    return config, environment_key or entered_key or stored_key or legacy_key
