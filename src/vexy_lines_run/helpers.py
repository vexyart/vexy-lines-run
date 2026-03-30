# this_file: src/vexy_lines_run/helpers.py
"""Constants, extension sets, and pure helper functions for the Vexy Lines GUI."""

from __future__ import annotations

import base64
import contextlib
import xml.etree.ElementTree as ET
import zlib

import cv2
from PIL import Image

IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
VIDEO_EXTENSIONS: set[str] = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
LINES_EXTENSIONS: set[str] = {".lines"}

EXPORT_FORMATS_LINES: list[str] = ["SVG", "PNG", "JPG", "LINES"]
EXPORT_FORMATS_IMAGES: list[str] = ["SVG", "PNG", "JPG"]
EXPORT_FORMATS_VIDEO: list[str] = ["MP4", "PNG", "JPG"]

MAX_STORED_STYLES = 5


def truncate_start(text: str, max_chars: int = 60) -> str:
    """Trim leading characters, keeping only the last *max_chars*."""
    if len(text) <= max_chars:
        return text
    return f"...{text[-(max_chars - 3) :]}"


def extract_preview_from_lines(filepath: str) -> bytes | None:
    """Extract the embedded preview or source image from a .lines file."""
    try:
        from vexy_lines import parse  # noqa: PLC0415

        doc = parse(filepath)
        return doc.preview_image_data or doc.source_image_data
    except Exception:
        with contextlib.suppress(Exception):
            tree = ET.parse(str(filepath))  # noqa: S314
            root = tree.getroot()
            pd = root.find("PreviewDoc")
            if pd is not None and pd.text:
                return base64.b64decode(pd.text.strip())
            # Fallback to SourcePict if PreviewDoc is missing
            sp = root.find("SourcePict")
            if sp is not None:
                img_data = sp.find("ImageData")
                if img_data is not None and img_data.text:
                    raw = base64.b64decode(img_data.text.strip())
                    return zlib.decompress(raw[4:])

    return None


def extract_frame(video_path: str, frame_number: int = 1) -> Image.Image | None:
    """Extract a single frame from video via OpenCV."""
    try:
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    except Exception:
        return None


def fit_image_to_box(image: Image.Image, width: int, height: int) -> Image.Image:
    """Scale image to fit inside box while preserving aspect ratio (scales up and down)."""
    img_w, img_h = image.size
    # Calculate scale to fit while preserving aspect ratio
    ratio = min(width / img_w, height / img_h)
    new_w = max(1, int(img_w * ratio))
    new_h = max(1, int(img_h * ratio))

    fitted = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    if fitted.mode == "RGBA":
        white = Image.new("RGBA", fitted.size, (255, 255, 255, 255))
        fitted = Image.alpha_composite(white, fitted)
    return fitted.convert("RGB")
