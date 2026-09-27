"""Real official SDK/runtime + local OpenAI-compatible provider; no paid API."""
import json
import os
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'FPGA_Agent'))
from harness_runtime import HarnessRuntime, HarnessCancelled, HarnessError
from tool_definitions import TOOLS


class LocalProvider:
    def __init__(self, responses):
        self.requests = []
        self.responses = list(responses)
        self.received = threading.Event()
        self.release = threading.Event()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                owner.requests.append((self.path, body, self.headers.get('Authorization')))
                owner.received.set()
                mode = owner.responses.pop(0) if owner.responses else 'done'
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.end_headers()
                if mode == 'wait':
                    owner.release.wait(10)
                    return
                if mode in {'tool', 'two_tools', 'info_tool'}:
                    delta = {'role': 'assistant', 'content': None, 'tool_calls': [{
                        # Some compatible providers reuse IDs in another turn.
                        'index': 0, 'id': 'call_reused', 'type': 'function',
                        'function': {'name': 'list_modules', 'arguments': '{"scope":"on_canvas"}'}}]}
                    reason = 'tool_calls'
                    if mode == 'info_tool':
                        delta['tool_calls'][0]['function'] = {
                            'name': 'get_module_info', 'arguments': '{"module_type":"PID控制器"}'}
                    if mode == 'two_tools':
                        delta['tool_calls'].append({'index': 1, 'id': 'second-call', 'type': 'function',
                            'function': {'name': 'list_modules', 'arguments': '{}'}})
                else:
                    delta, reason = {'role': 'assistant', 'content': 'LOCAL_OK'}, 'stop'
                for payload in ({'choices': [{'index': 0, 'delta': delta, 'finish_reason': None}]},
                                {'choices': [{'index': 0, 'delta': {}, 'finish_reason': reason}],
                                 'usage': {'prompt_tokens': 10, 'completion_tokens': 4, 'total_tokens': 14}}):
                    payload.update({'id': 'completion-test', 'object': 'chat.completion.chunk', 'model': 'deepseek-chat'})
                    self.wfile.write(('data: ' + json.dumps(payload) + '\n\n').encode())
                self.wfile.write(b'data: [DONE]\n\n')
                self.wfile.flush()

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.url = f'http://127.0.0.1:{self.server.server_port}/v1'
        self.thread = threading.Thread(target=self.server.serve_forever,
            kwargs={'poll_interval': 0.05}, daemon=True)
        self.thread.start()

    def close(self):
        self.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)


@unittest.skipUnless(os.environ.get('DCLOCKING_TEST_HARNESS_RUNTIME') == '1',
                     'set DCLOCKING_TEST_HARNESS_RUNTIME=1 for installed bundled runtime')
class HarnessRealRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.provider = LocalProvider(['tool', 'done', 'done'])
        self.runtime = HarnessRuntime(self.provider.url, 'local-test-key', 'deepseek-chat', timeout_seconds=45)
        self.calls = []

    def tearDown(self):
        self.runtime.close()
        self.provider.close()

    def run_turn(self, cancel=None):
        return self.runtime.run('List modules safely.', 'Use only the application tools.', TOOLS,
            lambda name, args, call: self.calls.append((name, args, call)) or '{"status":"success","nodes":[]}',
            cancel or threading.Event())

    def test_real_sdk_tools_history_and_openai_compatibility(self):
        self.provider.responses = ['tool', 'done', 'tool', 'done']
        self.assertEqual(self.run_turn(), 'LOCAL_OK')
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.run_turn(), 'LOCAL_OK')
        self.assertEqual(len(self.calls), 2)
        self.assertNotEqual(self.calls[0][2], self.calls[1][2])
        expected = sorted(tool['function']['name'] for tool in TOOLS)
        for path, request, auth in self.provider.requests:
            self.assertEqual(path, '/v1/chat/completions')
            self.assertEqual(auth, 'Bearer local-test-key')
            self.assertEqual(request.get('temperature'), 0.1)
            self.assertEqual(sorted(t['function']['name'] for t in request['tools']), expected)
            self.assertNotIn('dsh_session_log', request)
            self.assertNotIn('dsh_plugin_packages', request)
        self.assertTrue(any(m['role'] == 'tool' for m in self.provider.requests[-1][1]['messages']))

    def test_real_cancel_reaps_request_and_allows_next_turn(self):
        self.provider.responses = ['wait', 'done']
        cancelled = threading.Event()
        caught = []
        def run():
            try:
                self.run_turn(cancelled)
            except Exception as error:
                caught.append(error)
        thread = threading.Thread(target=run)
        thread.start()
        self.assertTrue(self.provider.received.wait(30))
        start = time.monotonic()
        cancelled.set()
        thread.join(timeout=6)
        self.assertFalse(thread.is_alive())
        self.assertLess(time.monotonic() - start, 6)
        self.assertIsInstance(caught[0], HarnessCancelled)
        self.provider.release.set()
        self.assertEqual(self.run_turn(), 'LOCAL_OK')
        self.assertFalse(self.calls)

    def test_provider_reused_call_id_in_different_model_rounds_executes_both(self):
        self.provider.responses = ['tool', 'info_tool', 'done']
        self.assertEqual(self.run_turn(), 'LOCAL_OK')
        self.assertEqual([call[0] for call in self.calls], ['list_modules', 'get_module_info'])
        self.assertNotEqual(self.calls[0][2], self.calls[1][2])

    def test_real_model_iteration_budget_stops_before_next_request(self):
        self.runtime.max_iterations = 1
        self.provider.responses = ['tool', 'tool', 'tool']
        with self.assertRaises(HarnessError):
            self.run_turn()
        self.assertEqual(len(self.provider.requests), 1)
        self.assertEqual(len(self.calls), 1)

    def test_cancel_after_first_atomic_tool_preserves_receipt_and_skips_sibling(self):
        self.provider.responses = ['two_tools', 'done']
        cancel = threading.Event()
        calls = []
        def dispatch(name, args, call_id):
            calls.append((name, args, call_id))
            cancel.set()
            return '{"status":"success","receipt":"already_completed_123"}'
        with self.assertRaises(HarnessCancelled):
            self.runtime.run('List twice.', 'Use only the application tools.', TOOLS, dispatch, cancel)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.run_turn(), 'LOCAL_OK')
        replayed = json.dumps(self.provider.requests[-1][1]['messages'])
        self.assertIn('already_completed_123', replayed)

    def test_real_stream_deltas_and_timeout(self):
        self.provider.responses = ['done', 'wait']
        deltas = []
        result = self.runtime.run('hello', 'Use only the application tools.', TOOLS,
            lambda *_: '{}', threading.Event(), on_text=deltas.append)
        self.assertEqual(''.join(deltas), result)
        self.runtime.timeout_seconds = 1
        with self.assertRaisesRegex(HarnessError, '超时'):
            self.run_turn()

    def test_timeout_cancels_pending_host_approval_wait(self):
        # This deadline covers a pending tool approval, not platform-dependent
        # SDK process startup. Warm the real runtime with its normal budget,
        # then give only the approval turn the deliberately short deadline.
        self.provider.responses = ['done']
        self.assertEqual(self.run_turn(), 'LOCAL_OK')
        self.assertFalse(self.calls)
        self.provider.requests.clear()
        self.provider.received.clear()
        self.provider.responses = ['tool']
        self.runtime.timeout_seconds = 1.5
        cancel, entered = threading.Event(), threading.Event()
        def pending_approval(*_args):
            entered.set()
            if not cancel.wait(4):
                raise AssertionError('Runtime did not wake pending approval')
            return '{"status":"cancelled","hardware_written":false}'
        start = time.monotonic()
        with self.assertRaisesRegex(HarnessError, '超时'):
            self.runtime.run('List modules.', 'Use only the application tools.', TOOLS,
                pending_approval, cancel)
        self.assertTrue(entered.is_set())
        self.assertTrue(cancel.is_set())
        self.assertLess(time.monotonic() - start, 3.5)
        self.assertEqual(len(self.provider.requests), 1)

    def test_cancel_pending_tool_then_immediately_send_again(self):
        for _ in range(3):
            self.provider.responses = ['tool', 'done']
            cancel, entered = threading.Event(), threading.Event()
            errors = []
            def pending(*_args):
                entered.set()
                cancel.wait(4)
                return '{"status":"cancelled","hardware_written":false}'
            def run():
                try:
                    self.runtime.run('Inspect modules.', 'Use only the application tools.', TOOLS, pending, cancel)
                except Exception as error:
                    errors.append(error)
            worker = threading.Thread(target=run)
            worker.start()
            self.assertTrue(entered.wait(5))
            cancel.set()
            worker.join(timeout=4)
            self.assertFalse(worker.is_alive())
            self.assertIsInstance(errors[0], HarnessCancelled)
            self.assertEqual(self.run_turn(), 'LOCAL_OK')

    def test_cancel_during_atomic_result_settlement_allows_twenty_next_turns(self):
        # Keep the HTTP tool request live while the runtime observes Stop.
        # This exercises actual AbortSignal cancellation, not just the host's
        # rejection of an already-set event before a model round is admitted.
        from deepseek_harness import DeepSeekHarness
        original_run = DeepSeekHarness.run
        sdk_returned = threading.Event()
        sdk_results = []

        def observed_run(sdk, *args, **kwargs):
            result = original_run(sdk, *args, **kwargs)
            sdk_results.append(result)
            sdk_returned.set()
            return result

        with patch.object(DeepSeekHarness, 'run', observed_run):
            for cycle in range(20):
                self.provider.responses = ['two_tools', 'done']
                cancel = threading.Event()
                calls = []
                sdk_returned.clear()

                def dispatch(name, args, call_id):
                    calls.append(call_id)
                    cancel.set()
                    # Signal the JS agent while fetch('/tool') is still alive,
                    # and hold the atomic host effect until its driver stops.
                    # This event barrier makes the regression deterministic.
                    if not sdk_returned.wait(3):
                        raise AssertionError('Canceled SDK driver did not settle')
                    return '{"status":"success","receipt":"atomic_completion"}'

                with self.assertRaises(HarnessCancelled):
                    self.runtime.run('List twice.', 'Use only the application tools.',
                        TOOLS, dispatch, cancel)
                self.assertEqual(len(calls), 1)
                self.assertEqual(sdk_results[-1].finish_reason, 'aborted', f'cycle {cycle}')
                self.assertEqual(self.run_turn(), 'LOCAL_OK')
