# this_file: vexy-lines-run/tests/test_settings.py
"""Tests for vexy_lines_run.settings (AI-rename LLM settings persistence)."""

from __future__ import annotations

from pathlib import Path

from vexy_lines_run import settings as s


def test_load_returns_empty_when_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(s, "settings_path", lambda: tmp_path / "settings.json")
    assert s.load_ai_settings() == {}


def test_save_then_load_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(s, "settings_path", lambda: tmp_path / "settings.json")
    s.save_ai_settings(
        {
            "llm_api_url": "http://host/v1",
            "llm_api_key": "key",
            "llm_model_vision": "vis",
            "llm_model": "txt",
        }
    )
    assert s.load_ai_settings() == {
        "llm_api_url": "http://host/v1",
        "llm_api_key": "key",
        "llm_model_vision": "vis",
        "llm_model": "txt",
    }


def test_save_drops_empty_and_unknown(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(s, "settings_path", lambda: tmp_path / "settings.json")
    s.save_ai_settings({"llm_api_url": "  ", "llm_model": "txt", "bogus": "x"})
    assert s.load_ai_settings() == {"llm_model": "txt"}


def test_load_handles_corrupt_file(tmp_path: Path, monkeypatch):
    p = tmp_path / "settings.json"
    p.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(s, "settings_path", lambda: p)
    assert s.load_ai_settings() == {}
