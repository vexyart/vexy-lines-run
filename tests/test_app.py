# this_file: vexy-lines-run/tests/test_app.py
"""Tests for vexy_lines_run.app -- GUI helpers and constants.

GUI widget tests are limited (no display server in CI), so we focus on
helper functions, constants, and importability.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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
        from vexy_lines_run.helpers import IMAGE_EXTENSIONS

        for ext in IMAGE_EXTENSIONS:
            assert ext.startswith("."), f"{ext} should start with a dot"
            assert ext == ext.lower(), f"{ext} should be lowercase"

    def test_video_extensions_are_lowercase(self):
        from vexy_lines_run.helpers import VIDEO_EXTENSIONS

        for ext in VIDEO_EXTENSIONS:
            assert ext.startswith(".")
            assert ext == ext.lower()

    def test_lines_extensions(self):
        from vexy_lines_run.helpers import LINES_EXTENSIONS

        assert ".lines" in LINES_EXTENSIONS

    def test_export_formats_lines(self):
        from vexy_lines_run.helpers import EXPORT_FORMATS_LINES

        assert "SVG" in EXPORT_FORMATS_LINES
        assert "LINES" in EXPORT_FORMATS_LINES

    def test_export_formats_video(self):
        from vexy_lines_run.helpers import EXPORT_FORMATS_VIDEO

        assert "MP4" in EXPORT_FORMATS_VIDEO


# ---------------------------------------------------------------------------
# truncate_start
# ---------------------------------------------------------------------------


class TestTruncateStart:
    def test_short_string_unchanged(self):
        from vexy_lines_run.helpers import truncate_start

        assert truncate_start("hello", 10) == "hello"

    def test_long_string_truncated_at_start(self):
        from vexy_lines_run.helpers import truncate_start

        result = truncate_start("abcdefghij", 7)
        assert result.startswith("...")
        assert len(result) == 7

    def test_preserves_end(self):
        from vexy_lines_run.helpers import truncate_start

        result = truncate_start("/very/long/path/to/file.txt", 15)
        assert result.endswith("file.txt")

    def test_empty_string(self):
        from vexy_lines_run.helpers import truncate_start

        assert truncate_start("", 10) == ""


# ---------------------------------------------------------------------------
# extract_preview_from_lines
# ---------------------------------------------------------------------------


class TestExtractPreviewFromLines:
    def test_returns_none_on_missing_file(self, tmp_path):
        from vexy_lines_run.helpers import extract_preview_from_lines

        result = extract_preview_from_lines(tmp_path / "nonexistent.lines")
        assert result is None

    def test_returns_none_on_nonexistent_path(self):
        from vexy_lines_run.helpers import extract_preview_from_lines

        result = extract_preview_from_lines("/nonexistent/does_not_exist.lines")
        assert result is None

    @patch("vexy_lines.parse", side_effect=Exception("parse error"))
    def test_returns_none_on_exception(self, _mock_parse):
        from vexy_lines_run.helpers import extract_preview_from_lines

        result = extract_preview_from_lines("/bad/file.lines")
        assert result is None


# ---------------------------------------------------------------------------
# extract_frame
# ---------------------------------------------------------------------------


class TestExtractFrame:
    def test_returns_none_without_opencv(self):
        from vexy_lines_run.helpers import extract_frame

        # Will return None if cv2 is not installed, or file doesn't exist
        result = extract_frame("/nonexistent/video.mp4", 0)
        assert result is None


class _FakeVar:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


class _FakeTabView:
    def __init__(self, value: str):
        self._value = value

    def get(self) -> str:
        return self._value


class _FakeThread:
    last_created = None

    def __init__(self, *, target, args, kwargs, daemon):
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.daemon = daemon
        self.started = False
        _FakeThread.last_created = self

    def start(self):
        self.started = True


class TestRunExport:
    def test_run_export_converts_ui_video_range_to_zero_based_export_request(self):
        from vexy_lines_run.app import App

        fake_app = SimpleNamespace(
            inputs_tabview=_FakeTabView("Video"),
            _style_paths={"start": "style.lines", "end": None},
            _output_path="styled.mp4",
            format_var=_FakeVar("MP4"),
            size_var=_FakeVar("1x"),
            audio_var=_FakeVar(True),
            _video_range=(5, 12),
            _style_mode="auto",
            abort_event=object(),
            after=MagicMock(),
            _on_export_progress=MagicMock(),
            _on_export_preview=MagicMock(),
            _on_export_complete=MagicMock(),
            _on_export_error=MagicMock(),
            _get_active_input_paths=lambda: ["input.mp4"],
        )

        _FakeThread.last_created = None
        with patch("vexy_lines_run.app.threading.Thread", _FakeThread):
            App._run_export(fake_app)

        assert _FakeThread.last_created is not None
        assert _FakeThread.last_created.started is True
        request = _FakeThread.last_created.args[0]
        assert request.mode == "video"
        assert request.frame_range == (4, 11)


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
