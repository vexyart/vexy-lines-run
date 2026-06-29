# this_file: vexy-lines-run/src/vexy_lines_run/video.py
"""Re-exports video utilities from :mod:`vexy_lines_api.video`.

All video processing logic lives in ``vexy-lines-apy``.  This module
re-exports the public API so that ``vexy_lines_run.video`` remains a stable
import path.

Per-frame pipeline (implemented in ``vexy_lines_api.video``)::

    OpenCV VideoCapture
        → raw BGR frame (numpy ndarray)
        → cv2.imencode(".png") → PNG bytes in memory
        → PIL Image.open(BytesIO(...))  [no disk I/O for source frames]
        → MCP apply_style(png_bytes) → SVG string
        → svg_to_pil(svg, w, h)  [resvg-py or Pillow fallback]
        → PIL Image → cv2 encode → VideoWriter frame

Memory note: frames are held as PNG bytes (not raw numpy arrays) while
waiting for the MCP round-trip.  A 1080p frame at PNG is roughly 1–3 MB
versus 6 MB uncompressed; for high-frame-count exports this matters.  The
:func:`probe` helper uses ``cv2.VideoCapture`` only to read metadata and is
cheap even on large files.
"""

from __future__ import annotations

from vexy_lines_api.video import (
    VideoInfo,
    probe,
    process_video,
    process_video_with_style,
    svg_to_pil,
)

__all__ = [
    "VideoInfo",
    "probe",
    "process_video",
    "process_video_with_style",
    "svg_to_pil",
]
