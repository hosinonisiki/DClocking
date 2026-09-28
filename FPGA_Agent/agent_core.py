"""Agent core — orchestrates the LLM function-calling loop.

Manages conversation history, dispatches tool calls, and emits signals
for the chat UI to consume.
"""

from __future__ import annotations

import json
import threading
import time
import traceback
import uuid

from PySide6.QtCore import QObject, Signal, QThread


class _AgentIncomplete(Exception):
    """A bounded generation ended normally, but did not finish the task."""

    def __init__(self, notice: str, partial_text: str = ""):
        super().__init__(notice)
        self.partial_text = partial_text


class AgentCore(QObject):
    """Orchestrator that runs the LLM ↔ tool-calling loop."""

    # Signals emitted to the UI
    response_ready = Signal(str)          # final markdown text
    response_delta = Signal(str, str)     # run_id, streamed text
    tool_executed = Signal(str, str, str)  # tool_name, args_json, result_json
    # Stable identifiers let the UI update a card instead of adding duplicates.
    tool_event = Signal(str, str, str, str, str, str)
    thinking_started = Signal()
    thinking_stopped = Signal()
    generation_cancelled = Signal()
    response_incomplete = Signal(str)     # expected output limit, not a traceback
    error_occurred = Signal(str)

    def __init__(self, llm_client, tool_executor, module_registry,
                 canvas_bridge, config: dict, parent=None):
        super().__init__(parent)
        self._llm = llm_client
        self._tools = tool_executor
        self._registry = module_registry
        self._bridge = canvas_bridge
        self._config = config
        self._max_iterations = config.get("agent", {}).get("max_tool_iterations", 15)

        # Conversation history
        self._messages: list[dict] = []

        # Load system prompt
        self._system_prompt = self._load_system_prompt()

        # Worker thread
        self._worker = None
        self._active_turn = False
        self._messages_at_cancel_boundary = None
        self._pending_tool_args = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset_conversation(self):
        """Clear conversation history (keeps system prompt)."""
        if self.is_busy:
            return False
        self._messages = []
        return True

    @property
    def is_busy(self):
        # QThread may have ended while its queued finished/result signals have
        # not reached Qt yet. Those receipts must be finalized before reuse.
        return self._active_turn

    def send_message(self, user_text: str):
        """Process a user message — runs LLM loop in background thread."""
        from tool_definitions import TOOLS

        if self.is_busy:
            return False
        if not user_text.strip():
            return False

        # Build messages
        if not self._messages:
            self._messages.append({
                "role": "system",
                "content": self._system_prompt,
            })
        self._messages.append({"role": "user", "content": user_text})
        # On cancellation, keep the submitted user turn but discard any
        # incomplete assistant/tool protocol messages from that turn.
        self._messages_at_cancel_boundary = list(self._messages)

        self._active_turn = True
        self.thinking_started.emit()

        # Run in background thread
        self._worker = self._create_worker(
            llm=self._llm,
            tools_def=TOOLS,
            tool_executor=self._tools,
            messages=list(self._messages),
            max_iterations=self._max_iterations,
            bridge=self._bridge,
        )
        # QThread.finished is the state barrier for restoring the send button.
        # Custom signals emitted inside run() can arrive while isRunning() is
        # still true, which makes an immediate next message disappear.
        self._worker.finished.connect(self._on_worker_terminated)
        self._worker.tool_call_started.connect(self._on_tool_started)
        self._worker.tool_call_finished.connect(self._on_tool_finished)
        self._worker.tool_event.connect(self._on_tool_event)
        self._worker.text_delta.connect(self._on_text_delta)
        self._worker.start()
        return True

    def _create_worker(self, **kwargs):
        """Native implementation; the runtime facade overrides only this seam."""
        return _AgentWorker(**kwargs)

    def stop_generation(self):
        """Cancel the active LLM turn without terminating its QThread."""
        if self._worker is None or not self._worker.isRunning():
            return False
        return self._worker.cancel()

    def shutdown(self, timeout_ms: int | None = None) -> bool:
        """Cancel and join the worker before its QThread can be destroyed.

        LLM transport cancellation is immediate. An already-running tool call
        is treated as an atomic operation and is allowed to return safely.
        """
        if self._worker is None or not self._worker.isRunning():
            return True
        self._worker.cancel()
        if timeout_ms is None:
            return self._worker.wait()
        return self._worker.wait(timeout_ms)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_worker_terminated(self):
        """Publish a worker outcome only after QThread has fully stopped."""
        worker = self.sender()
        if worker is not self._worker:
            return
        self._active_turn = False
        outcome = worker.outcome
        if outcome == "completed":
            self._messages = worker.messages
            self._messages_at_cancel_boundary = None
            self.thinking_stopped.emit()
            if worker.final_text:
                self.response_ready.emit(worker.final_text)
            return
        if outcome == "cancelled":
            self._on_worker_cancelled(worker.messages)
            return
        if outcome == "incomplete":
            self._messages = worker.messages
            self._messages_at_cancel_boundary = None
            self.thinking_stopped.emit()
            if worker.final_text:
                self.response_ready.emit(worker.final_text)
            self.response_incomplete.emit(worker.incomplete_notice)
            return
        # A model/transport failure after a tool call must not erase the
        # completed side effects from the next turn's context.
        self._messages = worker.messages
        self._messages_at_cancel_boundary = None
        self.thinking_stopped.emit()
        self.error_occurred.emit(worker.error_text or "Agent worker failed")

    def _on_worker_cancelled(self, _messages: list[dict]):
        """Restore a clean history and notify the UI after cancellation."""
        boundary = self._messages_at_cancel_boundary
        if boundary is not None:
            partial_turn = _messages[len(boundary):]
            if any(message.get("role") == "tool" for message in partial_turn):
                # Completed atomic tool effects must remain in history so the
                # next turn agrees with the current canvas/hardware state.
                self._messages = _messages
            else:
                self._messages = boundary
        self._messages_at_cancel_boundary = None
        self.thinking_stopped.emit()
        self.generation_cancelled.emit()

    def _on_tool_started(self, tool_name: str, args: dict):
        """Called when a tool begins execution."""
        self._pending_tool_args[tool_name] = args
        self.tool_executed.emit(tool_name, json.dumps(args, ensure_ascii=False, indent=2),
                                "...")

    def _on_tool_finished(self, tool_name: str, result: str):
        """Called when a tool finishes."""
        args = self._pending_tool_args.pop(tool_name, {})
        self.tool_executed.emit(tool_name, json.dumps(args, ensure_ascii=False), result)

    def _on_tool_event(self, run_id, call_id, name, args, result, status):
        if self.sender() is self._worker:
            self.tool_event.emit(run_id, call_id, name, args, result, status)

    def _on_text_delta(self, run_id, text):
        if (self.sender() is self._worker and self.is_busy
                and not self._worker._cancel_event.is_set()):
            self.response_delta.emit(run_id, text)

    # ------------------------------------------------------------------
    # System prompt
    # ------------------------------------------------------------------

    def _load_system_prompt(self) -> str:
        """Load and populate the system prompt."""
        from pathlib import Path
        prompt_file = Path(__file__).resolve().parent / "prompts" / "system_prompt.txt"
        if prompt_file.exists():
            template = prompt_file.read_text(encoding="utf-8")
        else:
            template = _DEFAULT_SYSTEM_PROMPT

        # Build module context
        from module_registry import build_llm_context
        module_context = build_llm_context(include_patterns=True)

        return template.replace("{module_descriptions}", module_context) + """

## Host execution and safety boundary
Tools run through the application's validated gateway. A confirm argument is
not user approval. Never retry denied/cancelled writes without asking the user.
local_staged means only PC configuration changed; hardware_unverified does not
prove device readback or optical lock. Read-only data is cached unless explicitly
marked otherwise. Never claim a hardware effect or successful lock without
actual measurement evidence. Stopping generation cannot undo completed actions.
"""


# ------------------------------------------------------------------
# Default system prompt (fallback if file is missing)
# ------------------------------------------------------------------

_DEFAULT_SYSTEM_PROMPT = """\
You are an FPGA signal processing design assistant. You control a visual
graph canvas by calling tools — you cannot interact directly with the user's
mouse or keyboard.

## Your capabilities
- Create signal processing modules (PID, filters, mixers, accumulators, etc.)
- Wire them together to build processing pipelines
- Set module parameters
- Generate code for new custom module types

## Available modules
{module_descriptions}

## Signal type compatibility
- "level" ports: connect to "level" or "differential" inputs
- "phase" ports: connect to "phase" inputs only
- "differential" ports: connect to "level" or "differential" inputs
- "bool" ports: connect to "bool" inputs only
- An input port accepts at most ONE connection
- In developer mode, any physical signal types (level/phase/differential) may
  connect to each other (relaxed validation)

## Module naming
Internal (short) names are used in tool calls:
- First instance: base name (e.g. ACCM, PIDC, TRIG, MIXR)
- Second instance: name + "2" (e.g. ACC2, PID2, TRI2, MIX2)
- View the exact name in create_module or list_modules responses

## Guidelines
1. Always call `get_module_info` before creating connections to verify port
   indices and signal types
2. When multiple modules are needed, create them all first, then connect them
3. Call `auto_layout` after creating several modules
4. If a module type does not exist, use `generate_module` to create it
5. For PDH locking, refer to the standard topology in the module descriptions
6. Explain what you're doing to the user in clear terms
7. If a tool call fails, read the error carefully, diagnose the issue, and
   try an alternative approach
"""


# ------------------------------------------------------------------
# Background worker thread
# ------------------------------------------------------------------

class _AgentWorker(QThread):
    """Runs the LLM function-calling loop in a background thread."""

    tool_call_started = Signal(str, dict)  # tool_name, args
    tool_call_finished = Signal(str, str)  # tool_name, result_json
    tool_event = Signal(str, str, str, str, str, str)
    text_delta = Signal(str, str)

    def __init__(self, llm, tools_def, tool_executor, messages,
                 max_iterations, bridge, parent=None):
        super().__init__(parent)
        self._llm = llm
        self._tools_def = tools_def
        self._executor = tool_executor
        self._messages = messages
        self._max_iter = max_iterations
        self._bridge = bridge
        self._cancel_event = threading.Event()
        self._request_id = object()
        self.run_id = uuid.uuid4().hex
        self.outcome = None
        self.final_text = ""
        self.error_text = ""
        self.incomplete_notice = ""

    @property
    def messages(self) -> list[dict]:
        return self._messages

    def cancel(self) -> bool:
        """Request cooperative cancellation and abort active network I/O."""
        if self._cancel_event.is_set():
            return False
        self._cancel_event.set()
        self.requestInterruption()
        cancel_request = getattr(self._llm, "cancel_request", None)
        if callable(cancel_request):
            try:
                cancel_request(self._request_id)
            except Exception:
                pass
        return True

    def run(self):
        try:
            self.final_text = self._loop()
            self._raise_if_cancelled()
            self.outcome = "completed"
        except _AgentCancelled:
            self._complete_cancelled_tool_protocol()
            self.outcome = "cancelled"
        except _AgentIncomplete as incomplete:
            if self._cancel_event.is_set() or self.isInterruptionRequested():
                self._complete_cancelled_tool_protocol()
                self.outcome = "cancelled"
            else:
                self._complete_cancelled_tool_protocol(
                    reason="Generation hit its output limit; do not repeat completed operations."
                )
                self.outcome = "incomplete"
                self.final_text = incomplete.partial_text
                self.incomplete_notice = str(incomplete)
                # Preserve both the receipts and explicit incomplete status,
                # without publishing hidden reasoning as an assistant answer.
                self._messages.append({"role": "assistant", "content":
                    (self.final_text + "\n\n" if self.final_text else "")
                    + "[" + self.incomplete_notice + "]"})
        except Exception as e:
            if self._cancel_event.is_set() or self.isInterruptionRequested():
                self._complete_cancelled_tool_protocol()
                self.outcome = "cancelled"
            else:
                self._complete_cancelled_tool_protocol(
                    reason="Execution stopped after an error; do not repeat completed operations."
                )
                self.outcome = "error"
                self.error_text = (
                    f"Agent error: {e}\n{traceback.format_exc()}"
                )
                snapshot = getattr(self._llm, "configuration_snapshot", None)
                if callable(snapshot):
                    key = snapshot().get("api_key", "")
                    if key:
                        self.error_text = self.error_text.replace(key, "[redacted]")

    def _loop(self) -> str:
        from llm_client import LLMError

        for iteration in range(self._max_iter):
            self._raise_if_cancelled()
            try:
                response = self._llm.chat(
                    self._messages,
                    self._tools_def,
                    cancel_event=self._cancel_event,
                    request_id=self._request_id,
                )
            except LLMError as e:
                self._raise_if_cancelled()
                self._messages.append({
                    "role": "assistant",
                    "content": f"API error: {e}",
                })
                return f"❌ LLM API 错误: {e}"

            self._raise_if_cancelled()

            # Extract assistant message
            content = response.get("content") or ""
            tool_calls = response.get("tool_calls")

            # Add assistant message to history
            assistant_msg = {"role": "assistant"}
            if content:
                assistant_msg["content"] = content
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            self._messages.append(assistant_msg)

            # If no tool calls, we're done
            if not tool_calls:
                return content

            # Execute each tool call
            for tool_index, tc in enumerate(tool_calls):
                self._raise_if_cancelled()
                fn = tc.get("function", {})
                tool_name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments", "{}"))
                except (json.JSONDecodeError, TypeError):
                    # Invalid JSON must not become {}, which could turn a
                    # malformed call into a valid default-valued operation.
                    args = None

                # Provider IDs need only correlate inside one assistant tool
                # batch. Keep them in model history, but namespace host/UI
                # receipts so later rounds cannot overwrite earlier results.
                host_call_id = f"native:{iteration}:{tool_index}:{tc.get('id', '')}"
                result_str = self._dispatch_tool(tool_name, args, host_call_id)

                self._messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": result_str,
                })
                self._raise_if_cancelled()

            # Layout is an explicit tool, subject to the same GUI-thread and
            # cancellation boundary. Read-only calls must not move the canvas.

        # Max iterations reached
        msg = (
            f"已达到最大模型执行轮数 ({self._max_iter})，本轮已停止。"
            "请以工具结果和画布实际状态为准；未完成的操作不会继续执行。"
        )
        self._messages.append({"role": "assistant", "content": msg})
        return msg

    def _dispatch_tool(self, name, args, call_id):
        self._raise_if_cancelled()
        args_json = json.dumps(args, ensure_ascii=False)
        self.tool_call_started.emit(name, args if isinstance(args, dict) else {})
        self.tool_event.emit(self.run_id, call_id, name, args_json, "", "running")
        if not isinstance(args, dict):
            result = json.dumps({"status": "failed", "error": "Tool arguments must be a JSON object"})
        elif getattr(self._executor, "supports_run_context", False):
            result = self._executor.dispatch(
                name, args, cancel_event=getattr(self, "_execution_cancel_event", self._cancel_event),
                run_id=self.run_id, call_id=call_id,
            )
        else:
            # Compatibility for headless native clients/test doubles. The UI
            # entrypoint always supplies ToolGateway, never a raw executor.
            result = self._executor.dispatch(name, args)
        self.tool_call_finished.emit(name, result)
        try:
            parsed = json.loads(result)
            status = parsed.get("status", "failed" if parsed.get("error") else "completed")
        except (ValueError, AttributeError):
            status = "failed"
        self.tool_event.emit(self.run_id, call_id, name, args_json, result, status)
        return result

    def _raise_if_cancelled(self):
        if self._cancel_event.is_set() or self.isInterruptionRequested():
            raise _AgentCancelled()

    def _complete_cancelled_tool_protocol(self, reason=None):
        """Close any partial tool-call protocol without executing more tools."""
        assistant_index = None
        tool_calls = []
        for index in range(len(self._messages) - 1, -1, -1):
            message = self._messages[index]
            if message.get("role") == "user":
                break
            if message.get("role") == "assistant" and message.get("tool_calls"):
                assistant_index = index
                tool_calls = message["tool_calls"]
                break
        if assistant_index is None:
            return

        completed_ids = {
            message.get("tool_call_id")
            for message in self._messages[assistant_index + 1:]
            if message.get("role") == "tool"
        }
        for tool_call in tool_calls:
            tool_call_id = tool_call.get("id", "")
            if tool_call_id not in completed_ids:
                self._messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps({
                        "error": reason or "Cancelled before execution"
                    }),
                })
        self._messages.append({
            "role": "assistant",
            "content": reason or "Generation stopped by user.",
        })


class _AgentCancelled(Exception):
    """Internal control-flow exception for a user-requested cancellation."""
