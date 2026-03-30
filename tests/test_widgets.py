# this_file: tests/test_widgets.py
"""Tests for vexy_lines_run.widgets -- CTkRangeSlider."""

from __future__ import annotations

import pytest


class TestCTkRangeSliderImport:
    """Verify the widget class is importable without a display."""

    def test_import(self):
        from vexy_lines_run.widgets import CTkRangeSlider

        assert CTkRangeSlider is not None

    def test_has_docstring(self):
        from vexy_lines_run.widgets import CTkRangeSlider

        assert CTkRangeSlider.__doc__ is not None
        assert "range" in CTkRangeSlider.__doc__.lower()
