"""Agent core — orchestrates the LLM function-calling loop.

Manages conversation history, dispatches tool calls, and emits signals
for the chat UI to consume.
"""

from __future__ import annotations

import json
import time
import traceback

from PySide6.QtCore import QObject, Signal, QThread


class AgentCore(QObject):
    """Orchestrator that runs the LLM ↔ tool-calling loop."""

    # Signals emitted to the UI
    response_ready = Signal(str)          # final markdown text
    tool_executed = Signal(str, str, str)  # tool_name, args_json, result_json
    thinking_started = Signal()
    thinking_stopped = Signal()
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset_conversation(self):
        """Clear conversation history (keeps system prompt)."""
        self._messages = []

    def send_message(self, user_text: str):
        """Process a user message — runs LLM loop in background thread."""
        from tool_definitions import TOOLS

        # Build messages
        if not self._messages:
            self._messages.append({
                "role": "system",
                "content": self._system_prompt,
            })
        self._messages.append({"role": "user", "content": user_text})

        self.thinking_started.emit()

        # Run in background thread
        self._worker = _AgentWorker(
            llm=self._llm,
            tools_def=TOOLS,
            tool_executor=self._tools,
            messages=list(self._messages),
            max_iterations=self._max_iterations,
            bridge=self._bridge,
        )
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.tool_call_started.connect(self._on_tool_started)
        self._worker.tool_call_finished.connect(self._on_tool_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_worker_finished(self, final_text: str, messages: list[dict]):
        """Called when the LLM loop completes."""
        self._messages = messages
        self.thinking_stopped.emit()
        if final_text:
            self.response_ready.emit(final_text)

    def _on_tool_started(self, tool_name: str, args: dict):
        """Called when a tool begins execution."""
        self.tool_executed.emit(tool_name, json.dumps(args, ensure_ascii=False, indent=2),
                                "...")

    def _on_tool_finished(self, tool_name: str, result: str):
        """Called when a tool finishes."""
        # Update the last emitted signal (we re-emit with result)
        pass

    def _on_error(self, error_text: str):
        """Called on error."""
        self.thinking_stopped.emit()
        self.error_occurred.emit(error_text)

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

        return template.replace("{module_descriptions}", module_context)


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

    finished = Signal(str, list)        # final_text, messages
    tool_call_started = Signal(str, dict)  # tool_name, args
    tool_call_finished = Signal(str, str)  # tool_name, result_json
    error = Signal(str)

    def __init__(self, llm, tools_def, tool_executor, messages,
                 max_iterations, bridge, parent=None):
        super().__init__(parent)
        self._llm = llm
        self._tools_def = tools_def
        self._executor = tool_executor
        self._messages = messages
        self._max_iter = max_iterations
        self._bridge = bridge

    def run(self):
        try:
            final_text = self._loop()
            self.finished.emit(final_text, self._messages)
        except Exception as e:
            self.error.emit(f"Agent error: {e}\n{traceback.format_exc()}")

    def _loop(self) -> str:
        from llm_client import LLMError

        for iteration in range(self._max_iter):
            try:
                response = self._llm.chat(self._messages, self._tools_def)
            except LLMError as e:
                self._messages.append({
                    "role": "assistant",
                    "content": f"API error: {e}",
                })
                self.finished.emit(f"LLM API 错误: {e}", self._messages)
                return f"❌ LLM API 错误: {e}"

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
            for tc in tool_calls:
                fn = tc.get("function", {})
                tool_name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}

                self.tool_call_started.emit(tool_name, args)

                result_str = self._executor.dispatch(tool_name, args)

                self.tool_call_finished.emit(tool_name, result_str)

                self._messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": result_str,
                })

            # Auto-layout after modifications
            if self._bridge and tool_calls:
                try:
                    self._bridge.auto_layout()
                except Exception:
                    pass

        # Max iterations reached
        msg = (
            f"已达到最大工具调用次数 ({self._max_iter})。"
            f"我已完成了 {self._max_iter} 步操作，请检查画布结果。"
        )
        self._messages.append({"role": "assistant", "content": msg})
        return msg
