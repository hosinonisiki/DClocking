"""Shared application budgets for one model completion.

These are conservative application defaults, not advertised provider limits.
An explicit budget is never silently replaced by a model-specific default.
"""

DEFAULT_OUTPUT_TOKENS = 4096
REASONING_OUTPUT_TOKENS = 32768
MAX_OUTPUT_TOKENS = 131072
_REASONING_MODELS = frozenset({
    "deepseek-v4-pro", "deepseek-v4-flash", "deepseek-flash", "deepseek-reasoner",
})

# Public call sites use this sentinel to distinguish "keep the existing policy"
# from an explicit None, which switches back to automatic model defaults.
OUTPUT_BUDGET_UNSET = object()


def resolve_max_tokens(model: str, value: int | None = None) -> int:
    """Resolve automatic output budget or validate an explicit integer budget."""
    if value is None:
        model_name = str(model or "").strip().casefold()
        return (REASONING_OUTPUT_TOKENS if model_name in _REASONING_MODELS
                else DEFAULT_OUTPUT_TOKENS)
    if type(value) is not int or not 1 <= value <= MAX_OUTPUT_TOKENS:
        raise ValueError(
            f"单次输出额度必须是 1–{MAX_OUTPUT_TOKENS} 的整数，或留为自动（null）"
        )
    return value
