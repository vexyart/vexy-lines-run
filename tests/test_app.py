# this_file: vexy-lines-run/tests/test_app.py
"""Tests for vexy_lines_run.app -- GUI helpers and constants.

GUI widget tests are limited (no display server in CI), so we focus on
helper functions, constants, and importability.
"""

from __future__ import annotations

import textwrap
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------


class TestImports:
    """Verify the public surface is importable without a display."""

    def test_import_app_module(self):
        import vexy_lines_run.app  # noqa: F401

    def test_import_launch(self):
        from vexy_lines_run.app import launch

        assert callable(launch)

    def test_import_app_class(self):
        from vexy_lines_run.app import App

        assert App is not None

    def test_top_level_reexport(self):
        from vexy_lines_run import App, launch

        assert App is not None
        assert callable(launch)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify module-level constants."""

    def test_image_extensions_are_lowercase(self):
        from vexy_lines_run.app import IMAGE_EXTENSIONS

        for ext in IMAGE_EXTENSIONS:
            assert ext.startswith("."), f"{ext} should start with a dot"
            assert ext == ext.lower(), f"{ext} should be lowercase"

    def test_video_extensions_are_lowercase(self):
        from vexy_lines_run.app import VIDEO_EXTENSIONS

        for ext in VIDEO_EXTENSIONS:
            assert ext.startswith(".")
            assert ext == ext.lower()

    def test_lines_extensions(self):
        from vexy_lines_run.app import LINES_EXTENSIONS

        assert ".lines" in LINES_EXTENSIONS

    def test_all_input_extensions_is_union(self):
        from vexy_lines_run.app import ALL_INPUT_EXTENSIONS, IMAGE_EXTENSIONS, LINES_EXTENSIONS, VIDEO_EXTENSIONS

        assert ALL_INPUT_EXTENSIONS == IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | LINES_EXTENSIONS

    def test_export_formats_lines(self):
        from vexy_lines_run.app import EXPORT_FORMATS_LINES

        assert "SVG" in EXPORT_FORMATS_LINES
        assert "LINES" in EXPORT_FORMATS_LINES

    def test_export_formats_video(self):
        from vexy_lines_run.app import EXPORT_FORMATS_VIDEO

        assert "MP4" in EXPORT_FORMATS_VIDEO

    def test_size_options(self):
        from vexy_lines_run.app import SIZE_OPTIONS

        assert "1x" in SIZE_OPTIONS
        assert "2x" in SIZE_OPTIONS


# ---------------------------------------------------------------------------
# truncate_middle
# ---------------------------------------------------------------------------


class TestTruncateMiddle:
    def test_short_string_unchanged(self):
        from vexy_lines_run.app import truncate_middle

        assert truncate_middle("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        from vexy_lines_run.app import truncate_middle

        assert truncate_middle("12345", 5) == "12345"

    def test_long_string_truncated(self):
        from vexy_lines_run.app import truncate_middle

        result = truncate_middle("abcdefghij", 7)
        assert "..." in result
        assert len(result) == 7

    def test_preserves_start_and_end(self):
        from vexy_lines_run.app import truncate_middle

        result = truncate_middle("START_MIDDLE_END", 10)
        assert result.startswith("STA")
        assert result.endswith("END")

    def test_default_max_width(self):
        from vexy_lines_run.app import truncate_middle

        short = "x" * 40
        assert truncate_middle(short) == short
        long = "y" * 50
        assert len(truncate_middle(long)) == 40

    def test_empty_string(self):
        from vexy_lines_run.app import truncate_middle

        assert truncate_middle("", 10) == ""


# ---------------------------------------------------------------------------
# truncate_start
# ---------------------------------------------------------------------------


class TestTruncateStart:
    def test_short_string_unchanged(self):
        from vexy_lines_run.app import truncate_start

        assert truncate_start("hello", 10) == "hello"

    def test_long_string_truncated_at_start(self):
        from vexy_lines_run.app import truncate_start

        result = truncate_start("abcdefghij", 7)
        assert result.startswith("...")
        assert len(result) == 7

    def test_preserves_end(self):
        from vexy_lines_run.app import truncate_start

        result = truncate_start("/very/long/path/to/file.txt", 15)
        assert result.endswith("file.txt")

    def test_empty_string(self):
        from vexy_lines_run.app import truncate_start

        assert truncate_start("", 10) == ""


# ---------------------------------------------------------------------------
# extract_preview_from_lines
# ---------------------------------------------------------------------------


class TestExtractPreviewFromLines:
    def test_returns_none_on_missing_file(self, tmp_path):
        from vexy_lines_run.app import extract_preview_from_lines

        result = extract_preview_from_lines(tmp_path / "nonexistent.lines")
        assert result is None

    @patch("vexy_lines_run.app.extract_preview_image")
    def test_delegates_to_parser(self, mock_extract):
        from vexy_lines_run.app import extract_preview_from_lines

        mock_extract.return_value = b"\x89PNG..."
        result = extract_preview_from_lines("/some/file.lines")
        assert result == b"\x89PNG..."
        mock_extract.assert_called_once_with("/some/file.lines")

    @patch("vexy_lines.parse", side_effect=Exception("parse error"))
    def test_returns_none_on_exception(self, mock_parse):
        from vexy_lines_run.app import extract_preview_from_lines

        result = extract_preview_from_lines("/bad/file.lines")
        assert result is None


# ---------------------------------------------------------------------------
# extract_frame
# ---------------------------------------------------------------------------


class TestExtractFrame:
    def test_returns_none_without_opencv(self):
        from vexy_lines_run.app import extract_frame

        # Will return None if cv2 is not installed, or file doesn't exist
        result = extract_frame("/nonexistent/video.mp4", 0)
        assert result is None

    @patch("vexy_lines_run.app.cv2", create=True)
    def test_returns_none_when_cap_fails(self, mock_cv2):
        from vexy_lines_run.app import extract_frame

        # Even with mocked cv2, the real import inside the function
        # may or may not work -- we test the graceful failure path
        result = extract_frame("/nonexistent/video.mp4")
        assert result is None


# ---------------------------------------------------------------------------
# _parse_drop_data (static method)
# ---------------------------------------------------------------------------


class TestParseDropData:
    def test_space_separated(self):
        from vexy_lines_run.app import App

        result = App._parse_drop_data("/path/a.png /path/b.png")
        assert result == ["/path/a.png", "/path/b.png"]

    def test_brace_enclosed(self):
        from vexy_lines_run.app import App

        result = App._parse_drop_data("{/path/with spaces/a.png} {/path/b.png}")
        assert result == ["/path/with spaces/a.png", "/path/b.png"]

    def test_single_path(self):
        from vexy_lines_run.app import App

        result = App._parse_drop_data("/single/path.lines")
        assert result == ["/single/path.lines"]

    def test_empty_string(self):
        from vexy_lines_run.app import App

        result = App._parse_drop_data("")
        assert result == []  # str.split() on empty string returns empty list
