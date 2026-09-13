"""Cancellable OpenAI-compatible chat-completions client.

Each generation owns a dedicated curl process. This makes cancellation work
during DNS, TLS, response-header wait, and streamed response delivery without
leaving an abandoned Python network thread behind.
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import threading
from collections.abc import Iterable
from typing import Any


class LLMError(Exception):
    """Raised when the LLM API returns an error."""


class LLMCancelled(LLMError):
    """Raised when the caller cancels a specific in-flight request."""


class LLMClient:
    """Thin wrapper around an OpenAI-compatible /chat/completions endpoint."""

    _STATUS_PREFIX = b"__DCLOCKING_HTTP_STATUS__:"
    _MAX_RESPONSE_BYTES = 20 * 1024 * 1024
    _MAX_JSON_RESPONSE_BYTES = 8 * 1024 * 1024
    _MAX_STREAM_LINES = 100_000
    _MAX_TOOL_CALLS = 128

    def __init__(self, endpoint: str, api_key: str, model: str = "gpt-4o",
                 temperature: float = 0.1, max_tokens: int = 4096,
                 timeout: float = 120.0):
        self._configuration_lock = threading.RLock()
        self.endpoint = ""
        self.api_key = ""
        self.model = ""
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.timeout = float(timeout)
        self.configure(endpoint=endpoint, api_key=api_key, model=model)
        self._curl_binary = shutil.which("curl")
        self._active_lock = threading.Lock()
        self._active_requests: dict[object, dict[str, Any]] = {}

    @staticmethod
    def _chat_completions_endpoint(endpoint: str) -> str:
        base = str(endpoint).strip().rstrip("/")
        if not base:
            raise ValueError("API endpoint is required")
        if base.endswith("/chat/completions"):
            return base
        return base + "/chat/completions"

    def configure(self, *, endpoint: str, api_key: str, model: str) -> None:
        """Atomically publish one provider/model/credential configuration."""

        normalized_endpoint = self._chat_completions_endpoint(endpoint)
        key = str(api_key or "")
        model_name = str(model or "").strip()
        if not normalized_endpoint or any(
            mark in normalized_endpoint for mark in ("\r", "\n", "\x00")
        ):
            raise ValueError("API endpoint is invalid")
        if any(mark in key for mark in ("\r", "\n", "\x00")):
            raise ValueError("API key contains an invalid control character")
        if not model_name:
            raise ValueError("Model name is required")
        with self._configuration_lock:
            self.endpoint = normalized_endpoint
            self.api_key = key
            self.model = model_name

    def configuration_snapshot(self) -> dict[str, Any]:
        with self._configuration_lock:
            return {
                "endpoint": self.endpoint,
                "api_key": self.api_key,
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "timeout": self.timeout,
            }

    def chat(self, messages: list[dict],
             tools: list[dict] | None = None, *,
             cancel_event: threading.Event | None = None,
             request_id: object | None = None) -> dict:
        """Send one cancellable, streaming chat-completion request."""
        if not self._curl_binary:
            raise LLMError("curl is required for cancellable LLM requests")
        configuration = self.configuration_snapshot()
        if not configuration["api_key"]:
            raise LLMError("API key is not configured")
        if "\r" in configuration["api_key"] or "\n" in configuration["api_key"]:
            raise LLMError("API key contains an invalid line break")

        payload = {
            "model": configuration["model"],
            "messages": messages,
            "temperature": configuration["temperature"],
            "max_tokens": configuration["max_tokens"],
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        cancel_event = cancel_event or threading.Event()
        request_id = request_id or object()
        self._raise_if_cancelled(cancel_event)

        process = subprocess.Popen(
            [self._curl_binary, "--disable", "--config", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        with self._active_lock:
            self._active_requests[request_id] = {
                "process": process,
                "cancel_event": cancel_event,
            }

        try:
            self._raise_if_cancelled(cancel_event)
            config = self._build_curl_config(
                payload,
                endpoint=configuration["endpoint"],
                api_key=configuration["api_key"],
                timeout=configuration["timeout"],
            )
            try:
                process.stdin.write(config.encode("utf-8"))
                process.stdin.close()
            except (BrokenPipeError, OSError) as exc:
                if cancel_event.is_set():
                    raise LLMCancelled("Request cancelled")
                raise LLMError(f"Unable to start LLM request: {exc}")

            body, status_code = self._read_process_output(process, cancel_event)
            stderr = process.stderr.read(2000).decode("utf-8", errors="replace")
            return_code = process.wait()
            self._raise_if_cancelled(cancel_event)

            if return_code != 0:
                detail = stderr.strip() or f"curl exited with code {return_code}"
                raise LLMError(f"Network error: {detail}")
            if status_code != 200:
                detail = self._error_detail(body)
                raise LLMError(f"API returned {status_code}: {detail}")

            return self._parse_response_body(body, cancel_event)
        finally:
            with self._active_lock:
                self._active_requests.pop(request_id, None)
            self._stop_process(process)

    def cancel_request(self, request_id: object) -> bool:
        """Terminate only the transport belonging to one Agent generation."""
        with self._active_lock:
            active = self._active_requests.get(request_id)
            if active is None:
                return False
            active["cancel_event"].set()
            process = active["process"]
        self._terminate_process(process)
        return True

    def test_connection(self) -> dict:
        """Send a minimal request to verify credentials and connectivity."""
        try:
            result = self.chat(
                messages=[{"role": "user", "content": "Hi"}],
                tools=None,
            )
            return {"ok": True, "model": self.configuration_snapshot()["model"],
                    "response": result.get("content", "")[:100]}
        except LLMError as e:
            return {"ok": False, "error": str(e)}

    def chat_async(self, messages: list[dict],
                   tools: list[dict] | None,
                   callback) -> threading.Thread:
        """Run chat() in a background thread; call callback(result) on finish."""
        def _run():
            try:
                result = self.chat(messages, tools)
                callback(result, None)
            except Exception as e:
                callback(None, str(e))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread

    def _build_curl_config(
        self,
        payload: dict,
        *,
        endpoint=None,
        api_key=None,
        timeout=None,
    ) -> str:
        if endpoint is None or api_key is None or timeout is None:
            configuration = self.configuration_snapshot()
            endpoint = configuration["endpoint"] if endpoint is None else endpoint
            api_key = configuration["api_key"] if api_key is None else api_key
            timeout = configuration["timeout"] if timeout is None else timeout
        payload_text = json.dumps(
            payload, ensure_ascii=False, separators=(",", ":")
        )
        status_template = (
            "\n" + self._STATUS_PREFIX.decode() + "%{http_code}\n"
        )
        lines = [
            f"url = {self._curl_quote(endpoint)}",
            'request = "POST"',
            'header = "Content-Type: application/json"',
            'header = "Accept: text/event-stream"',
            f"header = {self._curl_quote('Authorization: Bearer ' + api_key)}",
            f"data-binary = {self._curl_quote(payload_text)}",
            "no-buffer",
            "silent",
            "show-error",
            f"connect-timeout = {max(1.0, min(float(timeout), 30.0))}",
            f"max-time = {max(1.0, float(timeout))}",
            f"write-out = {self._curl_quote(status_template)}",
        ]
        return "\n".join(lines) + "\n"

    @staticmethod
    def _curl_quote(value: str) -> str:
        escaped = (value.replace("\\", "\\\\")
                        .replace('"', '\\"')
                        .replace("\r", "\\r")
                        .replace("\n", "\\n")
                        .replace("\t", "\\t"))
        return f'"{escaped}"'

    def _read_process_output(self, process, cancel_event) -> tuple[bytes, int]:
        output = bytearray()
        # Reserve a small allowance for curl's trailing HTTP-status marker.
        # Fixed-size reads prevent one malicious, unterminated line from being
        # allocated in full before the response-size limit can be enforced.
        transport_limit = self._MAX_RESPONSE_BYTES + 256

        while True:
            chunk = process.stdout.read(64 * 1024)
            if not chunk:
                break
            self._raise_if_cancelled(cancel_event)
            if len(output) + len(chunk) > transport_limit:
                self._terminate_process(process)
                raise LLMError("API response exceeded the safety limit")
            output.extend(chunk)

        self._raise_if_cancelled(cancel_event)
        marker = b"\n" + self._STATUS_PREFIX
        marker_index = output.rfind(marker)
        status_code = 0
        if marker_index >= 0:
            status_start = marker_index + len(marker)
            try:
                status_code = int(bytes(output[status_start:]).strip())
            except ValueError:
                status_code = 0
            body = bytes(output[:marker_index])
        else:
            body = bytes(output)

        if len(body) > self._MAX_RESPONSE_BYTES:
            raise LLMError("API response exceeded the safety limit")
        return body, status_code

    def _parse_response_body(self, body: bytes,
                             cancel_event: threading.Event) -> dict:
        # OpenAI-compatible event streams start with either comments or data
        # lines. Iterate the bytes buffer directly so a malicious response with
        # millions of tiny lines cannot allocate a giant splitlines() list.
        is_event_stream = any(
            line.lstrip().startswith((b"data:", b":"))
            for line in io.BytesIO(body[:4096])
        )
        if is_event_stream:
            return self._parse_event_stream(io.BytesIO(body), cancel_event)
        if len(body) > self._MAX_JSON_RESPONSE_BYTES:
            raise LLMError("JSON API response exceeded the safety limit")
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LLMError(f"Invalid API response: {exc}")
        if data.get("error"):
            raise LLMError(self._format_api_error(data["error"]))
        return self._normalise_response(data)

    def _parse_event_stream(self, lines: Iterable[bytes],
                            cancel_event: threading.Event) -> dict:
        content = io.StringIO()
        tool_calls: dict[int, dict] = {}
        finish_reason = None
        done_received = False
        line_count = 0

        for raw_line in lines:
            line_count += 1
            if line_count > self._MAX_STREAM_LINES:
                raise LLMError("Streaming response contained too many events")
            self._raise_if_cancelled(cancel_event)
            try:
                line = raw_line.decode("utf-8", errors="strict").strip()
            except UnicodeDecodeError as exc:
                raise LLMError(f"Invalid streaming response: {exc}")
            if not line or line.startswith(":"):
                continue
            if not line.startswith("data:"):
                continue
            data_text = line[5:].strip()
            if data_text == "[DONE]":
                done_received = True
                break
            try:
                payload = json.loads(data_text)
            except json.JSONDecodeError as exc:
                raise LLMError(f"Invalid streaming response: {exc}")
            if payload.get("error"):
                raise LLMError(self._format_api_error(payload["error"]))
            choices = payload.get("choices") or []
            if not choices:
                continue
            choice = choices[0]
            delta = choice.get("delta") or choice.get("message") or {}
            if delta.get("content"):
                content.write(delta["content"])
            self._accumulate_tool_calls(
                tool_calls, delta.get("tool_calls") or []
            )
            if choice.get("finish_reason"):
                finish_reason = choice["finish_reason"]

        self._raise_if_cancelled(cancel_event)
        if not done_received:
            raise LLMError(
                "Streaming response ended before the completion marker"
            )

        assembled_tools = [
            self._assemble_tool_call(tool_calls[index])
            for index in sorted(tool_calls)
        ]
        self._validate_tool_calls(assembled_tools)
        return {
            "role": "assistant",
            "content": content.getvalue(),
            "tool_calls": assembled_tools or None,
            "finish_reason": finish_reason or "stop",
        }

    @classmethod
    def _accumulate_tool_calls(cls, target: dict[int, dict],
                               fragments: list[dict]):
        for fragment in fragments:
            index = int(fragment.get("index", len(target)))
            if index not in target and len(target) >= cls._MAX_TOOL_CALLS:
                raise LLMError(
                    "Streaming response contained too many tool calls"
                )
            accumulated = target.setdefault(index, {
                "id": "",
                "type": "function",
                "name_parts": [],
                "argument_parts": [],
            })
            if fragment.get("id"):
                accumulated["id"] = fragment["id"]
            if fragment.get("type"):
                accumulated["type"] = fragment["type"]
            function = fragment.get("function") or {}
            accumulated["name_parts"].append(function.get("name") or "")
            accumulated["argument_parts"].append(
                function.get("arguments") or ""
            )

    @staticmethod
    def _assemble_tool_call(accumulated: dict) -> dict:
        """Join streamed fragments once, avoiding quadratic concatenation."""
        return {
            "id": accumulated["id"],
            "type": accumulated["type"],
            "function": {
                "name": "".join(accumulated["name_parts"]),
                "arguments": "".join(accumulated["argument_parts"]),
            },
        }

    @staticmethod
    def _validate_tool_calls(tool_calls: list[dict]) -> None:
        for tool_call in tool_calls:
            function = tool_call.get("function") or {}
            if not tool_call.get("id") or not function.get("name"):
                raise LLMError(
                    "Streaming response contained an incomplete tool call"
                )
            try:
                json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError as exc:
                raise LLMError(
                    f"Streaming tool arguments were incomplete: {exc}"
                )

    @staticmethod
    def _normalise_response(data: dict) -> dict:
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message", {})
        return {
            "role": message.get("role", "assistant"),
            "content": message.get("content") or "",
            "tool_calls": message.get("tool_calls"),
            "finish_reason": choice.get("finish_reason", "stop"),
        }

    def _error_detail(self, body: bytes) -> str:
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            return body.decode("utf-8", errors="replace")[:500]
        error = data.get("error", data)
        return self._format_api_error(error)

    @staticmethod
    def _format_api_error(error: Any) -> str:
        if isinstance(error, dict):
            return str(error.get("message") or error)[:500]
        return str(error)[:500]

    @staticmethod
    def _raise_if_cancelled(cancel_event: threading.Event) -> None:
        if cancel_event.is_set():
            raise LLMCancelled("Request cancelled")

    @staticmethod
    def _terminate_process(process) -> None:
        if process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass

    @classmethod
    def _stop_process(cls, process) -> None:
        if process.poll() is None:
            cls._terminate_process(process)
            try:
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except OSError:
                    pass
                process.wait(timeout=0.5)
        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe is not None and not pipe.closed:
                pipe.close()

    @classmethod
    def from_config(cls, config: dict) -> "LLMClient":
        """Create an LLMClient from a config dictionary."""
        llm_cfg = config.get("llm", config)
        return cls(
            endpoint=llm_cfg.get("endpoint", "https://api.openai.com/v1"),
            api_key=llm_cfg.get("api_key", ""),
            model=llm_cfg.get("model", "gpt-4o"),
            temperature=llm_cfg.get("temperature", 0.1),
            max_tokens=llm_cfg.get("max_tokens", 4096),
        )
