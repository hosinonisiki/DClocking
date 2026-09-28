"""Official Harness runtime with an authenticated, application-owned tool seam.

The bundled Harness owns model/history/tool scheduling. It cannot access Qt or
hardware: its only tools call ``dispatch`` supplied by the host's policy gateway.
The public read-only MCP catalog is intentionally not involved in this channel.
"""
from __future__ import annotations

import hmac
import importlib.metadata
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import uuid


SDK_VERSION = '0.1.5rc1'
_ALLOWED = frozenset({'create_module', 'connect_modules', 'list_modules',
    'disconnect_module', 'set_parameter', 'get_module_info', 'generate_module',
    'auto_layout', 'clear_canvas'})
_MAX_BODY = 256 * 1024
_MAX_RECOVERY_BYTES = 64 * 1024
_MAX_RECOVERY_RECEIPTS = 64


class HarnessError(RuntimeError):
    """Explicit Harness failure; callers must not silently switch engines."""


class HarnessCancelled(HarnessError):
    """The user stopped this run; completed host tool effects are retained."""


class HarnessOutputLimit(HarnessError):
    """A provider response exhausted its output allowance, not a failed tool.

    Only public final-response text belongs here. Reasoning stays private and
    the caller must mark the turn incomplete, never retry its tools implicitly.
    """
    def __init__(self, partial_text: str, max_tokens: int):
        self.partial_text = partial_text
        self.max_tokens = max_tokens
        answer_status = '已保留部分回答' if partial_text.strip() else '尚未生成正式回答'
        super().__init__(
            f'已达到单次模型输出额度（{max_tokens} tokens），本轮未完成；{answer_status}。'
            '已执行操作保留，不自动重试。可在设置中调整输出额度，或缩小任务后手动继续。'
        )


def _definitions(tools):
    result = []
    for entry in tools:
        function = entry.get('function', {})
        name = function.get('name')
        if name not in _ALLOWED or any(item['name'] == name for item in result):
            raise HarnessError('Harness 工具定义不在受控白名单中')
        result.append({key: function[key] for key in ('name', 'description', 'parameters')})
    if {item['name'] for item in result} != _ALLOWED:
        raise HarnessError('Harness 必须使用完整的九项受控工具定义')
    return json.loads(json.dumps(result, ensure_ascii=False, allow_nan=False))


class _HostTools:
    """Ephemeral local transport; NOT a public or hardware-control MCP server."""
    def __init__(self, tools, max_iterations):
        self.definitions = _definitions(tools)
        self.token = secrets.token_urlsafe(32)
        self.max_iterations = max_iterations
        self.ready = threading.Event()
        self._active = False
        self._dispatch = None
        self._cancel = threading.Event()
        self.stop_requested = threading.Event()
        self.settle_requested = threading.Event()
        self.settled = threading.Event()
        self._lock = threading.RLock()
        self._receipts = {}
        self._steps = 0
        self.failure = ''
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass  # Neither credentials nor experimental data go to stderr.

            def do_POST(self):
                self.connection.settimeout(3)
                host = self.headers.get('Host', '')
                auth = self.headers.get('Authorization', '')
                if (host != owner.url.removeprefix('http://') or self.headers.get('Origin')
                        or not hmac.compare_digest(auth, 'Bearer ' + owner.token)):
                    self.reply(403, {'error': 'Host authentication rejected'})
                    return
                try:
                    size = int(self.headers.get('Content-Length', '-1'))
                    if size < 0 or size > _MAX_BODY:
                        raise ValueError('Invalid request size')
                    payload = json.loads(self.rfile.read(size))
                    if not isinstance(payload, dict):
                        raise ValueError('Expected an object')
                    result = owner._request(self.path, payload)
                except (ValueError, KeyError, TypeError) as error:
                    self.reply(400, {'error': str(error)})
                except HarnessError as error:
                    self.reply(409, {'error': str(error)})
                except Exception:
                    self.reply(500, {'error': 'Host tool failed; inspect the application audit log'})
                else:
                    self.reply(200, result)

            def reply(self, status, value):
                body = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        self._server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self._server.daemon_threads = True
        self.url = f'http://127.0.0.1:{self._server.server_port}'
        self._thread = threading.Thread(target=self._server.serve_forever,
                                        kwargs={'poll_interval': 0.05}, daemon=True)
        self._thread.start()

    def begin(self, dispatch, cancel_event, on_text=None):
        with self._lock:
            self._dispatch, self._cancel = dispatch, cancel_event
            self._active, self._steps, self.failure = True, 0, ''
            self.stop_requested.clear()
            self.settle_requested.clear()
            self.settled.clear()
            self._on_text = on_text
            self.streamed_text = False
            self.run_id = uuid.uuid4().hex
            self._receipts.clear()
            self.completed_receipts = []

    def end(self):
        # Wait for an already-started atomic host dispatch; cancellation cannot
        # undo a hardware effect or let a stale call run during the next turn.
        with self._lock:
            self._active = False
            self._dispatch = None

    def _request(self, path, payload):
        # Must remain outside the dispatch lock: a pending user approval or
        # atomic tool must not block the separate cancellation control channel.
        if path == '/control':
            return {'cancel': self._cancel.is_set() or self.stop_requested.is_set(),
                    'settle': self.settle_requested.is_set(),
                    'run_id': getattr(self, 'run_id', None)}
        if path == '/settled':
            # The JS driver has finished Agent.whenIdle() for this nonce. This
            # acknowledgement is independent of a host dispatch's lock: the
            # latter is joined separately in end(), after SDK quiescence.
            if (not self.settle_requested.is_set()
                    or payload.get('run_id') != getattr(self, 'run_id', None)):
                raise ValueError('Stale or unexpected Harness settlement')
            self.settled.set()
            return {'ok': True}
        with self._lock:
            if path == '/ready':
                if payload.get('names') != sorted(_ALLOWED):
                    raise HarnessError('Unexpected Harness tool inventory')
                self.ready.set()
                return {'ok': True}
            if not self._active or self._cancel.is_set() or self.stop_requested.is_set():
                raise HarnessCancelled('DClocking run stopped; do not retry')
            if path == '/step':
                if self._steps >= self.max_iterations:
                    self.failure = '已达到本轮模型调用次数上限；未执行下一步。'
                    raise HarnessError(self.failure)
                self._steps += 1
                return {'ok': True, 'run_id': self.run_id, 'step_id': self._steps}
            if payload.get('run_id') != self.run_id:
                raise ValueError('Stale or unrecognized tool run identity')
            if path == '/text':
                text = payload.get('text')
                if not isinstance(text, str):
                    raise ValueError('Invalid text delta')
                if self._on_text:
                    self._on_text(text)
                self.streamed_text = True
                return {'ok': True}
            if path != '/tool':
                raise ValueError('Unknown host operation')
            name, args, call_id = payload.get('name'), payload.get('arguments'), payload.get('call_id')
            if name not in _ALLOWED or not isinstance(args, dict):
                raise ValueError('Unknown tool or invalid arguments')
            if not isinstance(call_id, str) or not call_id or len(call_id) > 256:
                raise ValueError('Invalid tool call identity')
            step_id = payload.get('step_id')
            if type(step_id) is not int or step_id < 1 or step_id != self._steps:
                raise ValueError('Stale or invalid tool model-step identity')
            identity = (step_id, call_id)
            fingerprint = json.dumps([name, args], sort_keys=True, allow_nan=False)
            previous = self._receipts.get(identity)
            if previous:
                if previous[0] != fingerprint:
                    raise ValueError('Tool identity reused with different arguments')
                return {'result': previous[1]}
            if len(self._receipts) >= 256:
                raise HarnessError('Host tool-call limit reached; stop this run')
            try:
                host_call_id = f'{self.run_id}:{step_id}:{call_id}'
                result = self._dispatch(name, args, host_call_id)
            except Exception:
                # A dispatch may have committed an effect before raising. Do
                # not replay it on a duplicate transport request.
                result = json.dumps({'status': 'error', 'summary': '工具执行结果不确定，请停止并检查应用日志；不要自动重试。'}, ensure_ascii=False)
            if not isinstance(result, str):
                result = json.dumps(result, ensure_ascii=False, allow_nan=False)
            if len(result.encode()) > 2 * 1024 * 1024:
                # Preserve the action receipt, but bound provider context.
                result = json.dumps({'status': 'warning', 'summary': '工具已执行，结果过大；请缩小查询范围。'})
            self._receipts[identity] = (fingerprint, result)
            self.completed_receipts.append({'call_id': host_call_id,
                'tool': name, 'arguments': args, 'result': result[:16000]})
            return {'result': result}

    def close(self):
        self.end()
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=1)


class HarnessRuntime:
    """One isolated durable conversation using the pinned official Python SDK.

    ``run`` belongs on a worker thread. ``dispatch(name, args, call_id)`` must
    cross the application's validated GUI-thread gateway. ``cancel`` is safe
    from another thread and deliberately does not wait for subprocess shutdown.
    """
    def __init__(self, endpoint, api_key, model, max_tokens=4096,
                 max_iterations=15, timeout_seconds=180, temperature=0.1):
        endpoint = endpoint.rstrip('/')
        if endpoint.endswith('/chat/completions'):
            endpoint = endpoint[:-len('/chat/completions')]
        url = urlsplit(endpoint)
        if (not url.hostname or url.username or url.password or url.query or url.fragment
                or (url.scheme != 'https' and not
                    (url.scheme == 'http' and url.hostname in {'127.0.0.1', 'localhost', '::1'}))):
            raise ValueError('Harness endpoint must use HTTPS (or a local HTTP test server)')
        if not isinstance(model, str) or not model.strip():
            raise ValueError('Harness model cannot be empty')
        if not 1 <= max_iterations <= 100 or not 1 <= timeout_seconds <= 3600 or max_tokens <= 0:
            raise ValueError('Invalid Harness execution limits')
        self.endpoint, self._api_key, self.model = endpoint, api_key, model
        self.max_tokens, self.max_iterations = max_tokens, max_iterations
        self.timeout_seconds, self.temperature = timeout_seconds, temperature
        self._storage = None
        self._host = None
        self._sdk = None
        self._system_prompt = None
        self._definitions = None
        self._session_id = 'dclocking-' + uuid.uuid4().hex
        self._run_lock = threading.Lock()
        self._cancel_requested = threading.Event()
        self._sdk_lock = threading.Lock()
        self._requires_reset = False
        self._pending_receipts = []
        self._pending_receipts_omitted = 0

    @property
    def session_id(self):
        return self._session_id

    def _retain_receipts(self, receipts):
        """Bound stop-recovery context; retain newest actual host receipts.

        This is context carried to the model, not the application's audit log.
        Omitted records are explicitly counted so truncation cannot imply that
        an action never happened or make replaying old actions look safe.
        """
        items = self._pending_receipts + list(receipts)
        retained, size = [], 0
        for receipt in reversed(items):
            encoded_size = len(json.dumps(receipt, ensure_ascii=False).encode()) + 2
            if (len(retained) >= _MAX_RECOVERY_RECEIPTS
                    or size + encoded_size > _MAX_RECOVERY_BYTES - 1024):
                continue
            retained.append(receipt)
            size += encoded_size
        self._pending_receipts_omitted += len(items) - len(retained)
        self._pending_receipts = list(reversed(retained))

    def _recovery_receipts(self):
        records = list(self._pending_receipts)
        if self._pending_receipts_omitted:
            records.insert(0, {'status': 'warning',
                'omitted_receipts': self._pending_receipts_omitted,
                'summary': '停止恢复上下文已达到 64 KiB / 64 条回执上限；部分回执细节未转发。'
                           '这不代表对应操作未执行，不要自动重放；先查询当前画布状态，'
                           '需要完整执行记录时请查看应用工具审计日志。'})
        return records

    def _start(self, system_prompt, tools):
        if self._requires_reset:
            raise HarnessError('Harness 曾被强制终止，请在 Agent 设置中重新保存设置以开启新模型会话；画布及已完成工具结果保留。')
        if not isinstance(self._api_key, str) or not self._api_key.strip():
            raise HarnessError('未设置 LLM API 密钥，请在 Agent 设置中配置后重试。')
        if self._sdk is not None:
            if system_prompt != self._system_prompt or _definitions(tools) != self._definitions:
                raise HarnessError('工具或系统提示已变化，请在 Agent 设置中重新保存设置以开启新模型会话后重试。')
            return
        try:
            for package in ('deepseek-harness-sdk', 'deepseek-harness-runtime-bin'):
                if importlib.metadata.version(package) != SDK_VERSION:
                    raise HarnessError(f'需要固定版本 {package}=={SDK_VERSION}，请安装 requirements-harness.txt。')
            from deepseek_harness import DeepSeekHarness
        except (ImportError, importlib.metadata.PackageNotFoundError) as error:
            raise HarnessError('未安装 Harness 运行时，请安装 requirements-harness.txt 或在设置中明确选择原生引擎。') from error
        if self._storage is None:
            self._storage = tempfile.TemporaryDirectory(prefix='dclocking-harness-')
        root = Path(self._storage.name)
        home, workspace = root / 'home', root / 'workspace'
        home.mkdir(mode=0o700, exist_ok=True)
        workspace.mkdir(mode=0o700, exist_ok=True)
        self._host = self._host or _HostTools(tools, self.max_iterations)
        self._host.ready.clear()
        self._definitions = _definitions(tools)
        self._system_prompt = system_prompt
        patch = root / 'dclocking.patch.json'
        provider = {
            'api': 'openai-completions', 'baseURL': self.endpoint,
            'apiKeyEnv': 'DCLOCKING_LLM_API_KEY',
            'retryPolicy': {'mode': 'normal', 'maxRetries': 0},
            'models': [{'id': self.model, 'name': self.model, 'contextWindow': 128000,
                        'maxTokens': self.max_tokens, 'input': ['text'], 'reasoningEfforts': False}],
            'compat': {'supportsDeveloperRole': False, 'maxTokensField': 'max_tokens'},
        }
        patch.write_text(json.dumps([{'insert': [
            {'id': 'dclocking-llm', 'name': '@deepseek-ai/dsh-llm-pi-ai',
             'config': {'providers': {'dclocking-openai': provider}}},
            {'id': 'dclocking-host-tools', 'name': str(Path(__file__).with_name('harness_host_tools.mjs')),
             'config': {'tools': self._definitions, 'temperature': self.temperature}},
        ]}], ensure_ascii=False), encoding='utf-8')
        # SDK merges over ambient env. Explicitly blank unrelated secrets and
        # launch overrides rather than mutating this application's environment.
        child_env = {key: '' for key in os.environ
                     if re.search(r'KEY|PASSWORD|SECRET|TOKEN', key, re.I) or key.startswith('DSH_')}
        child_env.update({'NODE_OPTIONS': '', 'NODE_PATH': '',
            'DSH_TELEMETRY_DISABLED': '1', 'DSH_SYSTEM_PROMPT': system_prompt,
            'DCLOCKING_LLM_API_KEY': self._api_key,
            'DCLOCKING_TOOL_URL': self._host.url, 'DCLOCKING_TOOL_TOKEN': self._host.token})
        sdk = DeepSeekHarness(provider='dclocking-openai', model=self.model,
            max_tokens=self.max_tokens, cwd=str(workspace), runtime_cwd=str(workspace),
            dsh_home=str(home), profile='sdk-minimal', env=child_env,
            patches=(str(Path(__file__).with_name('harness_profile.yml')), str(patch)),
            initialize_timeout_seconds=min(30, self.timeout_seconds),
            request_timeout_seconds=self.timeout_seconds, shutdown_timeout_seconds=0.5)
        with self._sdk_lock:
            self._sdk = sdk
        try:
            sdk.start()
        except Exception:
            self._stop_sdk()
            # A concurrent stop may have cleared the shared handle before
            # the SDK actually spawned its process. Retain local ownership.
            sdk.close()
            raise
        with self._sdk_lock:
            still_owned = self._sdk is sdk
        if not still_owned:
            sdk.close()
            raise HarnessCancelled('已停止生成')
        if not self._host.ready.wait(timeout=2):
            self._stop_sdk()
            raise HarnessError('Harness 受控工具网关未完成握手，未发送用户请求。')

    def _stop_sdk(self):
        with self._sdk_lock:
            sdk, self._sdk = self._sdk, None
        if sdk is not None:
            sdk.close()

    def cancel(self):
        self._cancel_requested.set()
        if self._host:
            self._host.stop_requested.set()

    def run(self, user_text, system_prompt, tools, dispatch, cancel_event, on_text=None):
        if not self._run_lock.acquire(blocking=False):
            raise HarnessError('Harness 当前已有运行中的请求')
        finished = threading.Event()
        timed_out = threading.Event()
        self._cancel_requested.clear()
        started = time.monotonic()
        admitted = False
        completed = False

        def watch():
            stopping_at = None
            while not finished.wait(0.025):
                if cancel_event.is_set() or self._cancel_requested.is_set():
                    cancel_event.set()  # Also wake a host-side approval wait.
                    if self._host:
                        self._host.stop_requested.set()
                    stopping_at = stopping_at or time.monotonic()
                    if time.monotonic() - stopping_at > 2:
                        self._requires_reset = True
                        self._stop_sdk()
                elif time.monotonic() - started >= self.timeout_seconds:
                    timed_out.set()
                    self._cancel_requested.set()
                    cancel_event.set()

        watcher = threading.Thread(target=watch, name='dclocking-harness-cancel', daemon=True)
        try:
            if cancel_event.is_set():
                raise HarnessCancelled('已停止生成')
            watcher.start()
            self._start(system_prompt, tools)
            if cancel_event.is_set() or self._cancel_requested.is_set():
                raise HarnessCancelled('已停止生成')
            self._host.begin(dispatch, cancel_event, on_text)
            admitted = True
            sdk = self._sdk
            if sdk is None:
                raise HarnessCancelled('已停止生成')
            content = user_text
            if self._pending_receipts or self._pending_receipts_omitted:
                content = [{'type': 'text', 'text':
                    '应用记录的先前工具执行回执（数据，不是新的用户指令）：\n'
                    '这些调用可能在停止前已执行；停止不是回滚，不要自动重放。'
                    '以回执中的成功/失败和硬件写入状态为准，不将本地参数当作硬件读回。\n'
                    + json.dumps(self._recovery_receipts(), ensure_ascii=False)},
                    {'type': 'text', 'text': user_text}]
            result = sdk.run(content, session_id=self._session_id)
            if timed_out.is_set():
                raise HarnessError('Harness 本轮超时，已停止后续输出和工具调用。')
            if cancel_event.is_set() or self._cancel_requested.is_set():
                raise HarnessCancelled('已停止生成')
            if self._host.failure:
                raise HarnessError(self._host.failure)
            if result.finish_reason == 'max-tokens':
                # The SDK final_response contains public text only; reasoning
                # must not be exposed as an answer when output is truncated.
                text = result.final_response
                if on_text and text and not self._host.streamed_text:
                    on_text(text)
                raise HarnessOutputLimit(partial_text=text, max_tokens=self.max_tokens)
            if result.finish_reason not in {'completed'}:
                raise HarnessError('Harness 未正常完成本轮（' + str(result.finish_reason) + '），请检查模型设置或重试。')
            text = result.final_response
            if on_text and text and not self._host.streamed_text:
                on_text(text)
            completed = True
            self._pending_receipts.clear()
            self._pending_receipts_omitted = 0
            return text
        except HarnessError:
            if timed_out.is_set():
                raise HarnessError('Harness 本轮超时，已停止后续输出和工具调用。') from None
            raise
        except Exception as error:
            if timed_out.is_set():
                raise HarnessError('Harness 本轮超时，已停止后续输出和工具调用。') from None
            if cancel_event.is_set() or self._cancel_requested.is_set():
                raise HarnessCancelled('已停止生成') from None
            # Upstream diagnostics can contain request configuration. Redact
            # credentials before exposing a bounded useful startup error.
            detail = str(error)
            for secret in (self._api_key, self._host.token if self._host else ''):
                if secret:
                    detail = detail.replace(secret, '[redacted]')
            raise HarnessError('Harness 运行失败：' + detail[-2400:]) from None
        finally:
            # SDK "idle" is an observed status, not its public whenIdle()
            # completion barrier. Retire the JS cancellation controller and
            # wait for driver quiescence before another prompt may be admitted.
            if admitted and self._host and self._sdk is not None:
                self._host.settle_requested.set()
                if not self._host.settled.wait(timeout=2):
                    self._requires_reset = True
                    self._stop_sdk()
            finished.set()
            if watcher.is_alive():
                watcher.join(timeout=4)
            if self._host:
                self._host.end()
                if admitted and not completed:
                    self._retain_receipts(self._host.completed_receipts)
            self._run_lock.release()

    def close(self):
        self.cancel()
        self._stop_sdk()
        if self._host:
            self._host.close()
            self._host = None
        if self._storage:
            self._storage.cleanup()
            self._storage = None
