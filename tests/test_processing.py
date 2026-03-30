# this_file: vexy-lines-run/tests/test_processing.py
"""Tests for vexy_lines_run.processing -- export pipeline helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# _parse_size_multiplier
# ---------------------------------------------------------------------------


class TestParseSizeMultiplier:
    def test_1x(self):
        from vexy_lines_run.processing import _parse_size_multiplier

        assert _parse_size_multiplier("1x") == 1

    def test_2x(self):
        from vexy_lines_run.processing import _parse_size_multiplier

        assert _parse_size_multiplier("2x") == 2

    def test_3x(self):
        from vexy_lines_run.processing import _parse_size_multiplier

        assert _parse_size_multiplier("3x") == 3

    def test_10x(self):
        from vexy_lines_run.processing import _parse_size_multiplier

        assert _parse_size_multiplier("10x") == 10

    def test_unknown_returns_1(self):
        from vexy_lines_run.processing import _parse_size_multiplier

        assert _parse_size_multiplier("foo") == 1

    def test_empty_returns_1(self):
        from vexy_lines_run.processing import _parse_size_multiplier

        assert _parse_size_multiplier("") == 1

    def test_no_x_suffix_returns_1(self):
        from vexy_lines_run.processing import _parse_size_multiplier

        assert _parse_size_multiplier("2") == 1


# ---------------------------------------------------------------------------
# _estimate_svg_dimensions
# ---------------------------------------------------------------------------


class TestEstimateSvgDimensions:
    def test_viewbox(self):
        from vexy_lines_run.processing import _estimate_svg_dimensions

        svg = '<svg viewBox="0 0 800 600"></svg>'
        assert _estimate_svg_dimensions(svg) == (800, 600)

    def test_viewbox_with_offset(self):
        from vexy_lines_run.processing import _estimate_svg_dimensions

        svg = '<svg viewBox="10 20 1024 768"></svg>'
        assert _estimate_svg_dimensions(svg) == (1024, 768)

    def test_width_height_attrs(self):
        from vexy_lines_run.processing import _estimate_svg_dimensions

        svg = '<svg width="640" height="480"></svg>'
        assert _estimate_svg_dimensions(svg) == (640, 480)

    def test_default_when_no_attrs(self):
        from vexy_lines_run.processing import _estimate_svg_dimensions

        svg = "<svg></svg>"
        assert _estimate_svg_dimensions(svg) == (800, 600)

    def test_viewbox_takes_precedence(self):
        from vexy_lines_run.processing import _estimate_svg_dimensions

        svg = '<svg viewBox="0 0 1920 1080" width="100" height="50"></svg>'
        assert _estimate_svg_dimensions(svg) == (1920, 1080)

    def test_viewbox_float_values(self):
        from vexy_lines_run.processing import _estimate_svg_dimensions

        svg = '<svg viewBox="0 0 100.5 200.7"></svg>'
        w, h = _estimate_svg_dimensions(svg)
        assert w == 100  # int(100.5)
        assert h == 200  # int(200.7)


# ---------------------------------------------------------------------------
# Callback helpers
# ---------------------------------------------------------------------------


class TestReportProgress:
    def test_calls_callback(self):
        from vexy_lines_run.processing import _report_progress

        cb = MagicMock()
        _report_progress(cb, 5, 10, "halfway")
        cb.assert_called_once_with(5, 10, "halfway")

    def test_none_callback_no_error(self):
        from vexy_lines_run.processing import _report_progress

        _report_progress(None, 5, 10, "halfway")  # should not raise

    def test_exception_in_callback_suppressed(self):
        from vexy_lines_run.processing import _report_progress

        cb = MagicMock(side_effect=RuntimeError("boom"))
        _report_progress(cb, 5, 10, "test")  # should not raise


class TestReportComplete:
    def test_calls_callback(self):
        from vexy_lines_run.processing import _report_complete

        cb = MagicMock()
        _report_complete(cb, "done")
        cb.assert_called_once_with("done")

    def test_none_callback_no_error(self):
        from vexy_lines_run.processing import _report_complete

        _report_complete(None, "done")

    def test_exception_in_callback_suppressed(self):
        from vexy_lines_run.processing import _report_complete

        cb = MagicMock(side_effect=RuntimeError("boom"))
        _report_complete(cb, "done")


class TestReportError:
    def test_calls_callback(self):
        from vexy_lines_run.processing import _report_error

        cb = MagicMock()
        _report_error(cb, "oops")
        cb.assert_called_once_with("oops")

    def test_none_callback_no_error(self):
        from vexy_lines_run.processing import _report_error

        _report_error(None, "oops")

    def test_exception_in_callback_suppressed(self):
        from vexy_lines_run.processing import _report_error

        cb = MagicMock(side_effect=RuntimeError("boom"))
        _report_error(cb, "oops")


# ---------------------------------------------------------------------------
# _save_image_bytes
# ---------------------------------------------------------------------------


class TestSaveImageBytes:
    def test_save_svg_writes_bytes(self, tmp_path):
        from vexy_lines_run.processing import _save_image_bytes

        dest = tmp_path / "out.svg"
        data = b"<svg>test</svg>"
        _save_image_bytes(data, dest, "SVG")
        assert dest.read_bytes() == data

    def test_save_png(self, tmp_path):
        from vexy_lines_run.processing import _save_image_bytes

        from PIL import Image

        # Create a small valid PNG in memory
        import io

        img = Image.new("RGB", (10, 10), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        dest = tmp_path / "out.png"
        _save_image_bytes(png_bytes, dest, "PNG")
        assert dest.exists()
        reopened = Image.open(dest)
        assert reopened.size == (10, 10)

    def test_save_png_with_multiplier(self, tmp_path):
        from vexy_lines_run.processing import _save_image_bytes

        from PIL import Image

        import io

        img = Image.new("RGB", (10, 10), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        dest = tmp_path / "out2x.png"
        _save_image_bytes(png_bytes, dest, "PNG", multiplier=2)
        assert dest.exists()
        reopened = Image.open(dest)
        assert reopened.size == (20, 20)

    def test_save_jpg(self, tmp_path):
        from vexy_lines_run.processing import _save_image_bytes

        from PIL import Image

        import io

        img = Image.new("RGB", (8, 8), color="green")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        dest = tmp_path / "out.jpg"
        _save_image_bytes(png_bytes, dest, "JPG")
        assert dest.exists()


# ---------------------------------------------------------------------------
# process_export dispatch
# ---------------------------------------------------------------------------


class TestProcessExportDispatch:
    def test_unknown_mode_calls_error(self):
        from vexy_lines_run.processing import process_export

        error_cb = MagicMock()
        complete_cb = MagicMock()
        process_export(
            mode="unknown",
            input_paths=[],
            style_path=None,
            end_style_path=None,
            output_path="/tmp/out",
            fmt="PNG",
            size="1x",
            audio=False,
            frame_range=None,
            on_progress=None,
            on_complete=complete_cb,
            on_error=error_cb,
        )
        error_cb.assert_called_once()
        assert "Unknown mode" in error_cb.call_args[0][0]
        complete_cb.assert_not_called()
