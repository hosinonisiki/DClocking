"""LLM API client — OpenAI-compatible chat completions with function calling.

Supports any OpenAI-compatible endpoint (OpenAI, Anthropic via proxy,
local Ollama/vLLM, etc.).
"""

from __future__ import annotations

import json
import threading
from typing import Any

import requests


class LLMError(Exception):
    """Raised when the LLM API returns an error."""


class LLMClient:
    """Thin wrapper around an OpenAI-compatible /chat/completions endpoint."""

    def __init__(self, endpoint: str, api_key: str, model: str = "gpt-4o",
                 temperature: float = 0.1, max_tokens: int = 4096,
                 timeout: float = 120.0):
        self.endpoint = endpoint.rstrip("/") + "/chat/completions"
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(self, messages: list[dict],
             tools: list[dict] | None = None) -> dict:
        """Send a chat completion request.

        Args:
            messages: List of {"role": "...", "content": "..."} dicts.
            tools: Optional list of function-calling tool definitions.

        Returns:
            The model's response message dict with "role", "content", and
            optionally "tool_calls".

        Raises:
            LLMError: On API error or network failure.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            resp = self._session.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise LLMError(f"Network error: {e}")

        if resp.status_code != 200:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text[:500]
            raise LLMError(f"API returned {resp.status_code}: {detail}")

        data = resp.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        return {
            "role": message.get("role", "assistant"),
            "content": message.get("content") or "",
            "tool_calls": message.get("tool_calls"),
            "finish_reason": choice.get("finish_reason", "stop"),
        }

    def test_connection(self) -> dict:
        """Send a minimal request to verify credentials and connectivity."""
        try:
            result = self.chat(
                messages=[{"role": "user", "content": "Hi"}],
                tools=None,
            )
            return {"ok": True, "model": self.model,
                    "response": result.get("content", "")[:100]}
        except LLMError as e:
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Async helpers (run in thread, return via callback)
    # ------------------------------------------------------------------

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

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

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
