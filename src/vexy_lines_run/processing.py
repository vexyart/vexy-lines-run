# this_file: src/vexy_lines_run/processing.py
"""Compatibility shim that re-exports shared export pipeline internals."""

from __future__ import annotations

from vexy_lines_api.export.callbacks import (
    report_complete as _report_complete,
)
from vexy_lines_api.export.callbacks import (
    report_error as _report_error,
)
from vexy_lines_api.export.callbacks import (
    report_preview as _report_preview,
)
from vexy_lines_api.export.callbacks import (
    report_progress as _report_progress,
)
from vexy_lines_api.export.images import _process_images
from vexy_lines_api.export.lines import _process_lines
from vexy_lines_api.export.pipeline import (
    _estimate_svg_dimensions,
    _parse_size_multiplier,
    _save_image_bytes,
    _save_svg_as_image,
    process_export,
)
from vexy_lines_api.export.video import _process_video, _process_video_to_frames, _process_video_to_mp4

__all__ = ["process_export"]
