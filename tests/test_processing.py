# this_file: vexy-lines-run/tests/test_processing.py
"""Tests for vexy_lines_run.processing -- export pipeline helpers."""

from __future__ import annotations

import threading
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
        # Create a small valid PNG in memory
        import io

        from PIL import Image

        from vexy_lines_run.processing import _save_image_bytes

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
        import io

        from PIL import Image

        from vexy_lines_run.processing import _save_image_bytes

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
        import io

        from PIL import Image

        from vexy_lines_run.processing import _save_image_bytes

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


# ---------------------------------------------------------------------------
# _process_lines — no-style path (MCPClient-based export)
# ---------------------------------------------------------------------------


class TestProcessLinesNoStyle:
    """Tests for the no-style branch of _process_lines that uses MCPClient."""

    def _make_client_mock(self, mock_mcp_cls: MagicMock) -> MagicMock:
        mock_client = MagicMock()
        mock_mcp_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_mcp_cls.return_value.__exit__ = MagicMock(return_value=False)
        return mock_client

    @patch("vexy_lines_run.processing.MCPClient")
    def test_svg_export_uses_mcp_engine(self, mock_mcp_cls, tmp_path):
        from vexy_lines_run.processing import _process_lines

        mock_client = self._make_client_mock(mock_mcp_cls)

        inp = tmp_path / "input"
        inp.mkdir()
        test_file = inp / "test.lines"
        test_file.write_text("<doc/>")
        out = tmp_path / "output"

        _process_lines(
            input_paths=[str(test_file)],
            style_path=None,
            end_style_path=None,
            output_path=str(out),
            fmt="SVG",
            size="1x",
            on_progress=None,
        )

        mock_client.open_document.assert_called_once_with(str(test_file))
        mock_client.render.assert_called_once()
        mock_client.export_svg.assert_called_once()

    @patch("vexy_lines_run.processing.MCPClient")
    def test_png_export_uses_mcp_engine(self, mock_mcp_cls, tmp_path):
        from vexy_lines_run.processing import _process_lines

        mock_client = self._make_client_mock(mock_mcp_cls)

        inp = tmp_path / "input"
        inp.mkdir()
        test_file = inp / "art.lines"
        test_file.write_text("<doc/>")
        out = tmp_path / "output"
        out.mkdir()
        # export_png writes a file that _save_image_bytes may try to read;
        # make it a no-op by having the mock write nothing (dest won't exist).
        # We just verify the call was made.

        _process_lines(
            input_paths=[str(test_file)],
            style_path=None,
            end_style_path=None,
            output_path=str(out),
            fmt="PNG",
            size="1x",
            on_progress=None,
        )

        mock_client.open_document.assert_called_once_with(str(test_file))
        mock_client.render.assert_called_once()
        mock_client.export_png.assert_called_once()

    @patch("vexy_lines_run.processing.MCPClient")
    def test_jpg_export_uses_mcp_engine(self, mock_mcp_cls, tmp_path):
        from vexy_lines_run.processing import _process_lines

        mock_client = self._make_client_mock(mock_mcp_cls)

        inp = tmp_path / "input"
        inp.mkdir()
        test_file = inp / "art.lines"
        test_file.write_text("<doc/>")
        out = tmp_path / "output"
        out.mkdir()

        _process_lines(
            input_paths=[str(test_file)],
            style_path=None,
            end_style_path=None,
            output_path=str(out),
            fmt="JPG",
            size="1x",
            on_progress=None,
        )

        mock_client.open_document.assert_called_once_with(str(test_file))
        mock_client.render.assert_called_once()
        mock_client.export_jpeg.assert_called_once()

    @patch("vexy_lines_run.processing.shutil")
    @patch("vexy_lines_run.processing.MCPClient")
    def test_lines_format_copies_file(self, mock_mcp_cls, mock_shutil, tmp_path):
        from vexy_lines_run.processing import _process_lines

        mock_client = self._make_client_mock(mock_mcp_cls)

        inp = tmp_path / "input"
        inp.mkdir()
        test_file = inp / "art.lines"
        test_file.write_text("<doc/>")
        out = tmp_path / "output"

        _process_lines(
            input_paths=[str(test_file)],
            style_path=None,
            end_style_path=None,
            output_path=str(out),
            fmt="LINES",
            size="1x",
            on_progress=None,
        )

        mock_shutil.copy2.assert_called_once()
        mock_client.open_document.assert_not_called()
        mock_client.render.assert_not_called()

    @patch("vexy_lines_run.processing.MCPClient")
    def test_mcp_failure_logs_warning_and_continues(self, mock_mcp_cls, tmp_path):
        from vexy_lines_run.processing import _process_lines

        mock_client = self._make_client_mock(mock_mcp_cls)

        # First call raises, second call succeeds
        mock_client.open_document.side_effect = [RuntimeError("connection refused"), None]

        inp = tmp_path / "input"
        inp.mkdir()
        file1 = inp / "first.lines"
        file1.write_text("<doc/>")
        file2 = inp / "second.lines"
        file2.write_text("<doc/>")
        out = tmp_path / "output"

        # Should not raise — failures are caught and logged as warnings
        _process_lines(
            input_paths=[str(file1), str(file2)],
            style_path=None,
            end_style_path=None,
            output_path=str(out),
            fmt="SVG",
            size="1x",
            on_progress=None,
        )

        assert mock_client.open_document.call_count == 2

    @patch("vexy_lines_run.processing.MCPClient")
    def test_abort_event_stops_processing(self, mock_mcp_cls, tmp_path):
        from vexy_lines_run.processing import _process_lines

        self._make_client_mock(mock_mcp_cls)

        inp = tmp_path / "input"
        inp.mkdir()
        test_file = inp / "art.lines"
        test_file.write_text("<doc/>")
        out = tmp_path / "output"

        abort = threading.Event()
        abort.set()

        with pytest.raises(Exception, match="aborted"):
            _process_lines(
                input_paths=[str(test_file)],
                style_path=None,
                end_style_path=None,
                output_path=str(out),
                fmt="SVG",
                size="1x",
                abort_event=abort,
                on_progress=None,
            )
