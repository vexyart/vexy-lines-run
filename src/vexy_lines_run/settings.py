# this_file: src/vexy_lines_run/settings.py
"""Persisted GUI settings for the AI-rename LLM endpoint.

Stores the four LLM knobs — ``llm_api_url``, ``llm_api_key``,
``llm_model_vision`` and ``llm_model`` — in a small JSON file so they survive
restarts. Empty values are dropped, so anything left blank falls back to the
``VEXY_LINES_*`` environment defaults at run time.
"""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger

AI_SETTING_KEYS: tuple[str, ...] = (
    "llm_api_url",
    "llm_api_key",
    "llm_model_vision",
    "llm_model",
)


def settings_path() -> Path:
    """Return the path to the settings JSON file (``~/.config/vexy-lines-run``)."""
    return Path.home() / ".config" / "vexy-lines-run" / "settings.json"


def load_ai_settings() -> dict[str, str]:
    """Load saved AI-rename settings, returning only non-empty known keys."""
    path = settings_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("Could not read settings {}: {}", path, exc)
        return {}
    if not isinstance(data, dict):
        return {}
    return {key: str(data[key]) for key in AI_SETTING_KEYS if data.get(key)}


def save_ai_settings(values: dict[str, str]) -> Path:
    """Persist AI-rename settings, dropping unknown and empty values.

    Returns:
        The path the settings were written to.
    """
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = {key: str(values[key]).strip() for key in AI_SETTING_KEYS if str(values.get(key, "")).strip()}
    path.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
    logger.debug("Saved AI settings to {}", path)
    return path
