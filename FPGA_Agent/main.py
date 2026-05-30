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
import json
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


def main():
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

    # ---- Create application ----
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.setWindowTitle("FPGA Designer + Agent")

    # ---- Load config ----
    agent_dir = Path(__file__).resolve().parent
    config_path = agent_dir / "config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        config = {"llm": {}, "agent": {}}

    # ---- Build Agent components ----
    from canvas_bridge import CanvasBridge
    from llm_client import LLMClient
    from tool_definitions import TOOLS
    from tool_executor import ToolExecutor
    from code_generator import CodeGenerator
    from agent_core import AgentCore
    from agent_chat_widget import AgentChatWidget

    # Canvas bridge
    bridge = CanvasBridge(window)

    # Code generator
    code_gen = CodeGenerator()

    # Tool executor
    executor = ToolExecutor(bridge, None, code_gen)

    # LLM client
    llm_cfg = config.get("llm", {})
    llm = LLMClient(
        endpoint=llm_cfg.get("endpoint", "https://api.openai.com/v1"),
        api_key=llm_cfg.get("api_key", ""),
        model=llm_cfg.get("model", "gpt-4o"),
        temperature=llm_cfg.get("temperature", 0.1),
        max_tokens=llm_cfg.get("max_tokens", 4096),
    )

    # Agent core
    agent = AgentCore(llm, executor, None, bridge, config)

    # Chat widget
    chat = AgentChatWidget()
    window.addDockWidget(Qt.RightDockWidgetArea, chat)

    # ---- Wire signals ----
    chat.user_message_submitted.connect(agent.send_message)

    agent.response_ready.connect(chat.add_assistant_message)
    agent.thinking_started.connect(lambda: chat.set_thinking(True))
    agent.thinking_stopped.connect(lambda: chat.set_thinking(False))
    agent.error_occurred.connect(
        lambda err: chat.add_system_message(f"Error: {err}")
    )
    agent.tool_executed.connect(
        lambda name, args, result: chat.add_tool_call(name, args, result)
    )

    # ---- Show window ----
    window.show()

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
    if not llm_cfg.get("api_key"):
        chat.add_system_message(
            "API key not configured. Click Settings to enter your API key."
        )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
