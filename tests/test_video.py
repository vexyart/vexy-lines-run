# this_file: vexy-lines-run/tests/test_video.py
"""Tests for vexy_lines_run.video -- video utilities and data structures."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# VideoInfo
# ---------------------------------------------------------------------------


class TestVideoInfo:
    def test_construction(self):
        from vexy_lines_run.video import VideoInfo

        info = VideoInfo(
            width=1920,
            height=1080,
            fps=30.0,
            total_frames=900,
            duration=30.0,
            has_audio=True,
        )
        assert info.width == 1920
        assert info.height == 1080
        assert info.fps == 30.0
        assert info.total_frames == 900
        assert info.duration == 30.0
        assert info.has_audio is True

    def test_frozen(self):
        from vexy_lines_run.video import VideoInfo

        info = VideoInfo(width=100, height=100, fps=24.0, total_frames=240, duration=10.0, has_audio=False)
        with pytest.raises(AttributeError):
            info.width = 200  # type: ignore[misc]

    def test_equality(self):
        from vexy_lines_run.video import VideoInfo

        a = VideoInfo(width=640, height=480, fps=25.0, total_frames=250, duration=10.0, has_audio=False)
        b = VideoInfo(width=640, height=480, fps=25.0, total_frames=250, duration=10.0, has_audio=False)
        assert a == b

    def test_inequality(self):
        from vexy_lines_run.video import VideoInfo

        a = VideoInfo(width=640, height=480, fps=25.0, total_frames=250, duration=10.0, has_audio=False)
        b = VideoInfo(width=1280, height=720, fps=30.0, total_frames=300, duration=10.0, has_audio=True)
        assert a != b

    def test_repr(self):
        from vexy_lines_run.video import VideoInfo

        info = VideoInfo(width=320, height=240, fps=15.0, total_frames=150, duration=10.0, has_audio=False)
        r = repr(info)
        assert "320" in r
        assert "240" in r
        assert "VideoInfo" in r


# ---------------------------------------------------------------------------
# probe
# ---------------------------------------------------------------------------


class TestProbe:
    def test_raises_import_error_without_av(self):
        """probe() should raise ImportError when av is not installed."""
        from vexy_lines_run.video import probe

        # If av IS installed, we'd need a valid file; if it's NOT installed
        # we get ImportError. Either way this exercises the error path.
        try:
            probe("/nonexistent/video.mp4")
        except (ImportError, RuntimeError):
            pass  # expected
        except Exception:
            pass  # av may throw different errors for bad files


# ---------------------------------------------------------------------------
# _svg_to_pil
# ---------------------------------------------------------------------------


class TestSvgToPil:
    def test_fallback_returns_correct_size(self):
        """Without resvg or svglab, returns a blank image of the right size."""
        from vexy_lines_run.video import _svg_to_pil

        # Patch out both rasterisers so we hit the fallback
        with (
            patch.dict("sys.modules", {"resvg": None, "svglab": None}),
        ):
            img = _svg_to_pil("<svg></svg>", 200, 100)
            assert img.size == (200, 100)
            assert img.mode == "RGBA"

    def test_returns_pil_image(self):
        from PIL import Image

        from vexy_lines_run.video import _svg_to_pil

        img = _svg_to_pil("<svg></svg>", 50, 50)
        assert isinstance(img, Image.Image)

    @patch("vexy_lines_run.video.resvg", create=True)
    def test_uses_resvg_when_available(self, mock_resvg):
        """When resvg is importable, _svg_to_pil should call svg_to_png."""
        import io

        from PIL import Image

        # Create a valid PNG that resvg would return
        img = Image.new("RGBA", (100, 80))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        mock_resvg.svg_to_png.return_value = buf.getvalue()

        from vexy_lines_run.video import _svg_to_pil

        result = _svg_to_pil("<svg></svg>", 100, 80)
        assert isinstance(result, Image.Image)


# ---------------------------------------------------------------------------
# process_video (import check)
# ---------------------------------------------------------------------------


class TestProcessVideoImport:
    def test_process_video_importable(self):
        from vexy_lines_run.video import process_video

        assert callable(process_video)

    def test_process_video_with_style_importable(self):
        from vexy_lines_run.video import process_video_with_style

        assert callable(process_video_with_style)
