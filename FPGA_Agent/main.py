#!/usr/bin/env python3
"""FPGA Agent — AI-powered FPGA signal processing design assistant.

Launches the standard DClocking MainWindow with an additional Agent chat panel
docked on the right side.  No existing code is modified.

Usage:
    python FPGA_Agent/main.py          # from DClocking directory
    python -m FPGA_Agent.main          # from DClocking directory
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


def create_window(settings=None):
    # ---- Ensure our own package is importable (for absolute imports) ----
    agent_dir = str(Path(__file__).resolve().parent)
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)

    # ---- Ensure the DClocking python control directory is on sys.path ----
    project_root = Path(__file__).resolve().parent.parent
    python_control = project_root / "python control"
    if str(python_control) not in sys.path:
        sys.path.insert(0, str(python_control))

    # ---- Import existing MainWindow ----
    from qt_ui_mainwindow import MainWindow

    window = MainWindow(settings=settings)

    # ---- Load public config and OS-backed API credential ----
    agent_dir = Path(__file__).resolve().parent
    config_path = agent_dir / "config.json"
    from secret_store import load_agent_configuration

    try:
        config, api_key, credential_warning = load_agent_configuration(config_path)
    except (OSError, ValueError) as exc:
        config = {"llm": {}, "agent": {}}
        api_key = ""
        credential_warning = str(exc)

    # ---- Build Agent components ----
    from canvas_bridge import CanvasBridge
    from llm_client import LLMClient
    from tool_executor import ToolExecutor
    from tool_gateway import ToolGateway
    from code_generator import CodeGenerator
    from runtime_agent_core import RuntimeAgentCore
    from agent_chat_widget import AgentChatWidget

    # Canvas bridge
    bridge = CanvasBridge(window)

    # Code generator
    code_gen = CodeGenerator()

    # Tool executor
    executor = ToolExecutor(bridge, None, code_gen)
    gateway = ToolGateway(executor, bridge, parent=window)

    # LLM client
    llm_cfg = config.get("llm", {})
    llm = LLMClient(
        endpoint=llm_cfg.get("endpoint", "https://api.openai.com/v1"),
        api_key=api_key,
        model=llm_cfg.get("model", "gpt-4o"),
        temperature=llm_cfg.get("temperature", 0.1),
        max_tokens=llm_cfg.get("max_tokens", 4096),
    )

    # Agent core
    agent = RuntimeAgentCore(llm, gateway, None, bridge, config, parent=window)

    # Chat widget
    chat = AgentChatWidget(window)
    window.register_agent_dock(chat)

    # ---- Wire signals ----
    chat.user_message_submitted.connect(agent.send_message)
    chat.cancel_requested.connect(agent.stop_generation)
    gateway.approval_requested.connect(chat.show_tool_approval)
    gateway.approval_finished.connect(chat.expire_tool_approval)
    chat.approval_resolved.connect(gateway.resolve_approval)
    agent.runtime_status_changed.connect(chat.set_runtime_status)
    chat.set_runtime_status(agent.engine, agent.runtime_description())

    def apply_saved_settings(payload):
        from copy import deepcopy

        updated = payload.get("config", {})
        updated_llm = updated.get("llm", {})
        current = llm.configuration_snapshot()
        candidate = deepcopy(config)
        candidate.update(updated)
        try:
            # Validate the entire provider tuple before retiring the old
            # session. A busy/close failure must not partially replace its key.
            prepared = LLMClient(
                endpoint=updated_llm.get("endpoint", current["endpoint"]),
                model=updated_llm.get("model", current["model"]),
                api_key=payload.get("api_key", ""),
            ).configuration_snapshot()
            agent.reconfigure(candidate)
            llm.configure(endpoint=prepared["endpoint"], model=prepared["model"],
                          api_key=prepared["api_key"])
        except (ValueError, RuntimeError, OSError):
            chat.add_system_message("运行中的设置未修改：请先停止任务并检查运行时，再重新保存设置。")
            return
        config.clear()
        config.update(candidate)
        chat.add_system_message("Agent 设置已生效；已开始新的模型会话，画布配置保持不变。")
        if payload.get("api_key"):
            chat.add_system_message("LLM 设置已安全保存并立即生效。")
        else:
            chat.add_system_message("Endpoint 已切换；请为该服务配置 API Key。")

    chat.settings_saved.connect(apply_saved_settings)

    agent.response_ready.connect(chat.finish_assistant_message)
    agent.response_delta.connect(chat.append_assistant_delta)
    agent.thinking_started.connect(lambda: chat.set_thinking(True))
    agent.thinking_stopped.connect(lambda: chat.set_thinking(False))
    agent.thinking_stopped.connect(chat.dismiss_tool_approvals)
    agent.error_occurred.connect(
        lambda err: chat.add_system_message(f"Error: {err}")
    )
    agent.generation_cancelled.connect(
        lambda: chat.add_system_message("已停止生成；尚未执行的操作已取消，已完成的操作不会撤销。")
    )
    agent.tool_event.connect(chat.update_tool_call)

    app = QApplication.instance()
    if app is not None:
        # Wake queued gateway waits before joining the worker. Never process
        # pending mutations in a nested event loop while closing the app.
        app.aboutToQuit.connect(gateway.shutdown)
        app.aboutToQuit.connect(agent.shutdown)

    # ---- Welcome message ----
    chat.add_assistant_message(
        "## FPGA Agent Ready\n\n"
        "I can help you build FPGA signal processing pipelines. "
        "Just describe what you want in natural language.\n\n"
        "**Examples:**\n"
        "- \"帮我搭建一个 PDH 锁定系统\"\n"
        "- \"Create a sine wave generator at 10 MHz\"\n"
        "- \"Set up a PID feedback loop with a lowpass filter\"\n\n"
        "Use the **Settings** button to configure your LLM API endpoint and key."
    )

    # Check API key
    if credential_warning:
        chat.add_system_message(credential_warning)
    if not api_key:
        chat.add_system_message(
            "API key not configured. Click Settings to enter your API key."
        )

    window._agent_components = {
        "bridge": bridge,
        "code_generator": code_gen,
        "executor": executor,
        "gateway": gateway,
        "llm": llm,
        "agent": agent,
        "chat": chat,
    }
    return window


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = create_window()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
