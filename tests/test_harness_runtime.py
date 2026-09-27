"""Host boundary tests; optional integration uses the real pinned SDK locally."""
import importlib.util
import json
import os
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'FPGA_Agent'))
from harness_runtime import HarnessRuntime, HarnessError, HarnessCancelled, _HostTools
from tool_definitions import TOOLS


class HostToolsTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.cancel = threading.Event()
        self.host = _HostTools(TOOLS, 2)
        self.host.begin(lambda name, args, call: self.calls.append((name, args, call)) or '{}', self.cancel)

    def tearDown(self):
        self.host.close()

    def request(self, path, payload, token=None, **headers):
        if path == '/tool':
            if not self.host._steps:
                self.request('/step', {})
            payload = {'step_id': self.host._steps, **payload}
        if path in {'/tool', '/text'}:
            payload = {'run_id': self.host.run_id, **payload}
        req = Request(self.host.url + path, json.dumps(payload).encode(), headers={
            'Authorization': 'Bearer ' + (token if token is not None else self.host.token),
            'Content-Type': 'application/json', **headers,
        })
        try:
            with urlopen(req, timeout=3) as response:
                return json.load(response)
        except HTTPError as error:
            error.close()
            raise

    def test_only_authentic_local_requests_reach_dispatch(self):
        with self.assertRaises(HTTPError) as error:
            self.request('/tool', {}, token='wrong')
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError):
            self.request('/tool', {}, Origin='https://example.com')
        self.assertFalse(self.calls)

    def test_allowlist_and_idempotent_call_receipts(self):
        payload = {'name': 'list_modules', 'arguments': {}, 'call_id': 'c1'}
        self.assertEqual(self.request('/tool', payload), {'result': '{}'})
        self.assertEqual(self.request('/tool', payload), {'result': '{}'})
        self.assertEqual(len(self.calls), 1)
        with self.assertRaises(HTTPError):
            self.request('/tool', {**payload, 'name': 'bash'})
        with self.assertRaises(HTTPError):
            self.request('/tool', {**payload, 'arguments': {'scope': 'both'}})
        self.assertEqual(len(self.calls), 1)

    def test_cancel_and_budget_prevent_future_dispatch(self):
        self.request('/step', {})
        self.request('/step', {})
        with self.assertRaises(HTTPError):
            self.request('/step', {})
        self.cancel.set()
        with self.assertRaises(HTTPError):
            self.request('/tool', {'name': 'list_modules', 'arguments': {}, 'call_id': 'c2'})
        self.assertFalse(self.calls)

    def test_ready_requires_exact_inventory(self):
        with self.assertRaises(HTTPError):
            self.request('/ready', {'names': ['bash']})
        self.assertFalse(self.host.ready.is_set())
        self.request('/ready', {'names': sorted(t['function']['name'] for t in TOOLS)})
        self.assertTrue(self.host.ready.is_set())

    def test_settlement_requires_requested_current_run_identity(self):
        first_run = self.host.run_id
        with self.assertRaises(HTTPError):
            self.request('/settled', {'run_id': first_run})
        self.host.settle_requested.set()
        self.cancel.set()
        self.assertTrue(self.request('/control', {})['settle'])
        self.request('/settled', {'run_id': first_run})
        self.assertTrue(self.host.settled.is_set())
        self.host.end()
        self.host.begin(lambda *_: '{}', threading.Event())
        self.host.settle_requested.set()
        with self.assertRaises(HTTPError):
            self.request('/settled', {'run_id': first_run})
        self.assertFalse(self.host.settled.is_set())

    def test_provider_call_identity_is_scoped_to_run_and_stale_calls_reject(self):
        first_run = self.host.run_id
        payload = {'name': 'list_modules', 'arguments': {}, 'call_id': 'reused'}
        self.request('/tool', payload)
        self.host.end()
        self.host.begin(lambda *args: self.calls.append(args) or '{}', self.cancel)
        self.request('/tool', payload)
        self.assertEqual(len(self.calls), 2)
        self.assertNotEqual(self.calls[0][2], self.calls[1][2])
        with self.assertRaises(HTTPError):
            self.request('/tool', {**payload, 'run_id': first_run})
        self.assertEqual(len(self.calls), 2)

    def test_provider_call_identity_is_scoped_to_model_step(self):
        payload = {'name': 'list_modules', 'arguments': {}, 'call_id': 'reused'}
        self.request('/tool', payload)
        self.request('/tool', payload)
        self.request('/step', {})
        self.request('/tool', {**payload, 'arguments': {'scope': 'both'}})
        self.assertEqual(len(self.calls), 2)
        self.assertNotEqual(self.calls[0][2], self.calls[1][2])
        with self.assertRaises(HTTPError):
            self.request('/tool', {**payload, 'step_id': 1})
        self.assertEqual(len(self.calls), 2)

    def test_dispatch_exception_is_not_replayed(self):
        attempts = []
        def fail(*args):
            attempts.append(args)
            raise RuntimeError('effect may already be committed')
        self.host.begin(fail, self.cancel)
        payload = {'name': 'list_modules', 'arguments': {}, 'call_id': 'uncertain'}
        first = self.request('/tool', payload)
        self.assertEqual(self.request('/tool', payload), first)
        self.assertEqual(json.loads(first['result'])['status'], 'error')
        self.assertEqual(len(attempts), 1)


class RuntimeUnitTests(unittest.TestCase):
    def test_recovery_receipts_are_bounded_and_truncation_is_explicit(self):
        runtime = HarnessRuntime('https://api.deepseek.com/v1', 'local-test-key', 'deepseek-chat')
        try:
            for batch in range(20):
                runtime._retain_receipts([{'call_id': f'{batch}:{item}',
                    'tool': 'set_parameter', 'arguments': {'params': {'freq': item}},
                    'result': '已完成' * 2000} for item in range(20)])
            context = runtime._recovery_receipts()
            self.assertLessEqual(len(json.dumps(context, ensure_ascii=False).encode()), 65536)
            self.assertLessEqual(len(runtime._pending_receipts), 64)
            self.assertEqual(context[0]['status'], 'warning')
            self.assertEqual(context[0]['omitted_receipts'], 400 - len(runtime._pending_receipts))
            self.assertIn('不要自动重放', context[0]['summary'])
            self.assertEqual(context[-1]['call_id'], '19:19')

            runtime._retain_receipts([{'call_id': 'large', 'arguments': {'value': 'x' * 80000}}])
            context = runtime._recovery_receipts()
            self.assertLessEqual(len(json.dumps(context, ensure_ascii=False).encode()), 65536)
            self.assertEqual(context[0]['omitted_receipts'], 401 - len(runtime._pending_receipts))
        finally:
            runtime.close()

    def test_cancel_before_sdk_spawn_reaps_late_process(self):
        entered, cancel = threading.Event(), threading.Event()
        instances, errors = [], []
        class SlowSDK:
            def __init__(self, **_kwargs):
                self.alive = False
                instances.append(self)
            def start(self):
                entered.set()
                time.sleep(2.2)  # SDK resolves/extracts executable before Popen.
                self.alive = True
            def close(self):
                self.alive = False
        runtime = HarnessRuntime('https://api.deepseek.com/v1', 'local-test-key', 'deepseek-chat')
        def run():
            try:
                runtime.run('hello', 'safe', TOOLS, lambda *_: '{}', cancel)
            except Exception as error:
                errors.append(error)
        try:
            with patch.dict(sys.modules, {'deepseek_harness': SimpleNamespace(DeepSeekHarness=SlowSDK)}), \
                    patch('harness_runtime.importlib.metadata.version', return_value='0.1.5rc1'):
                worker = threading.Thread(target=run)
                worker.start()
                self.assertTrue(entered.wait(2))
                cancel.set()
                worker.join(timeout=4)
                self.assertFalse(worker.is_alive())
                self.assertIsInstance(errors[0], HarnessCancelled)
                self.assertFalse(instances[0].alive)
        finally:
            runtime.close()

    def test_missing_key_and_sdk_are_explicit_not_silent_fallback(self):
        runtime = HarnessRuntime('https://api.deepseek.com/v1', '', 'deepseek-chat')
        try:
            with self.assertRaisesRegex(HarnessError, '密钥'):
                runtime.run('hello', 'safe', TOOLS, lambda *_: '{}', threading.Event())
            self.assertIsNone(runtime._sdk)
        finally:
            runtime.close()
        runtime = HarnessRuntime('https://api.deepseek.com/v1', 'not-a-real-key', 'deepseek-chat')
        try:
            with patch('harness_runtime.importlib.metadata.version', return_value='0.0.0'):
                with self.assertRaisesRegex(HarnessError, '固定版本'):
                    runtime.run('hello', 'safe', TOOLS, lambda *_: '{}', threading.Event())
            self.assertIsNone(runtime._sdk)
        finally:
            runtime.close()
    def test_invalid_endpoint_and_prerun_cancel(self):
        with self.assertRaises(ValueError):
            HarnessRuntime(endpoint='http://example.com/v1', api_key='unused', model='x')
        runtime = HarnessRuntime(endpoint='https://api.deepseek.com/v1', api_key='unused', model='deepseek-chat')
        event = threading.Event(); event.set()
        try:
            with self.assertRaises(HarnessCancelled):
                runtime.run('hello', 'safe', TOOLS, lambda *_: '{}', event)
            self.assertIsNone(runtime._sdk)
        finally:
            runtime.close()

    def test_profile_disables_shell_and_uploads(self):
        text = (Path(__file__).resolve().parents[1] / 'FPGA_Agent/harness_profile.yml').read_text()
        for row in ('persistent-bash', 'persistent-pwsh', 'terminal-bash', 'terminal-pwsh',
                    'session-log-deepseek', 'plugin-package-inventory-deepseek', 'llm-deepseek'):
            self.assertIn(f'- id: {row}\n  disabled: true', text)
