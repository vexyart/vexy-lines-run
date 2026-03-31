# this_file: src/vexy_lines_run/helpers.py
"""Constants and helper re-exports for the Vexy Lines GUI."""

from __future__ import annotations

from vexy_lines_api.media import (
    extract_frame,
    extract_preview_from_lines,
    fit_image_to_box,
    truncate_start,
)

__all__ = [
    "EXPORT_FORMATS_IMAGES",
    "EXPORT_FORMATS_LINES",
    "EXPORT_FORMATS_VIDEO",
    "IMAGE_EXTENSIONS",
    "LINES_EXTENSIONS",
    "MIN_TRUNCATE_CHARS",
    "VIDEO_EXTENSIONS",
    "extract_frame",
    "extract_preview_from_lines",
    "fit_image_to_box",
    "truncate_start",
]

IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
VIDEO_EXTENSIONS: set[str] = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
LINES_EXTENSIONS: set[str] = {".lines"}

EXPORT_FORMATS_LINES: list[str] = ["SVG", "PNG", "JPG", "LINES"]
EXPORT_FORMATS_IMAGES: list[str] = ["SVG", "PNG", "JPG"]
EXPORT_FORMATS_VIDEO: list[str] = ["MP4", "PNG", "JPG"]

MIN_TRUNCATE_CHARS = 5
