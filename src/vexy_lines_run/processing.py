# this_file: src/vexy_lines_run/processing.py
"""Export processing pipeline for the Vexy Lines Run.

Dispatches export jobs for three input modes (lines, images, video) and
calls into the MCP style engine from ``vexy_lines_api``.

All heavy work runs on a background thread started by
:meth:`~vexy_lines_run.app.App._on_export`.  Three callbacks communicate
results back to the GUI thread:

- ``on_progress(current, total, message)`` — integer progress counters
- ``on_complete(message)`` — called once on success
- ``on_error(message)`` — called once on failure

Callbacks are always invoked via ``root.after(0, ...)`` in the App layer, so
they are safe to call from the worker thread without extra locking.
"""

from __future__ import annotations

import contextlib
import io
import re
import shutil
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import cv2  # type: ignore[import-untyped]
from loguru import logger
from PIL import Image

from vexy_lines import parse as parse_lines
from vexy_lines_api import (
    MCPClient,
    apply_style,
    extract_style,
    interpolate_style,
    styles_compatible,
)
from vexy_lines_api.video import (
    _svg_to_pil,
    probe,
    process_video_with_style,
)

if TYPE_CHECKING:
    pass

__all__ = ["process_export"]

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def process_export(
    mode: str,
    input_paths: list[str],
    style_path: str | None,
    end_style_path: str | None,
    output_path: str,
    fmt: str,
    size: str,
    *,
    audio: bool = True,
    frame_range: tuple[int, int] | None = None,
    relative_style: bool = False,
    abort_event: threading.Event | None = None,
    on_progress: Callable[[int, int, str], None] | None = None,
    on_complete: Callable[[str], None] | None = None,
    on_error: Callable[[str], None] | None = None,
) -> None:
    """Dispatch an export job."""
    try:
        if mode == "lines":
            _process_lines(
                input_paths=input_paths,
                style_path=style_path,
                end_style_path=end_style_path,
                output_path=output_path,
                fmt=fmt,
                size=size,
                relative_style=relative_style,
                abort_event=abort_event,
                on_progress=on_progress,
            )
        elif mode == "images":
            _process_images(
                input_paths=input_paths,
                style_path=style_path,
                end_style_path=end_style_path,
                output_path=output_path,
                fmt=fmt,
                size=size,
                relative_style=relative_style,
                abort_event=abort_event,
                on_progress=on_progress,
            )
        elif mode == "video":
            _process_video(
                input_path=input_paths[0] if input_paths else "",
                style_path=style_path,
                end_style_path=end_style_path,
                output_path=output_path,
                fmt=fmt,
                size=size,
                audio=audio,
                frame_range=frame_range,
                relative_style=relative_style,
                abort_event=abort_event,
                on_progress=on_progress,
            )
        else:
            _report_error(on_error, f"Unknown mode: {mode}")
            return

        _report_complete(on_complete, f"Export complete ({fmt})")
    except Exception as exc:
        if str(exc) == "Export aborted by user":
            _report_error(on_error, str(exc))
        else:
            logger.opt(exception=True).error("Export failed")
            _report_error(on_error, str(exc))


# ---------------------------------------------------------------------------
# Mode dispatchers
# ---------------------------------------------------------------------------


def _process_lines(
    *,
    input_paths: list[str],
    style_path: str | None,
    end_style_path: str | None,
    output_path: str,
    fmt: str,
    size: str,
    relative_style: bool = False,
    abort_event: threading.Event | None = None,
    on_progress: Callable[[int, int, str], None] | None,
) -> None:
    """Process .lines file exports."""
    total = len(input_paths)
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    multiplier = _parse_size_multiplier(size)

    style = _load_style(style_path) if style_path else None
    end_style = _load_style(end_style_path) if end_style_path else None

    if style is not None:
        with MCPClient() as client:
            for idx, path in enumerate(input_paths):
                if abort_event and abort_event.is_set():
                    raise Exception("Export aborted by user")

                _report_progress(on_progress, idx, total, f"Processing {Path(path).name}")

                if fmt == "LINES":
                    shutil.copy2(path, out_dir / Path(path).name)
                    continue

                try:
                    doc = parse_lines(path)
                except Exception:
                    logger.opt(exception=True).warning("Could not parse {}", path)
                    continue

                img_bytes: bytes | None = doc.source_image_data or doc.preview_image_data
                if img_bytes is None:
                    logger.warning("No image data in {}", path)
                    continue

                current_style = style
                if end_style is not None and styles_compatible(style, end_style) and total > 1:
                    current_style = interpolate_style(style, end_style, idx / (total - 1))

                stem = Path(path).stem
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    tmp.write(img_bytes)
                    tmp_path = Path(tmp.name)
                try:
                    res: str | bytes = apply_style(client, current_style, str(tmp_path), relative=relative_style)
                    final_bytes = res if isinstance(res, bytes) else res.encode()
                    if fmt in ("PNG", "JPG"):
                        _save_image_bytes(final_bytes, out_dir / f"{stem}.{fmt.lower()}", fmt, multiplier)
                    elif fmt == "SVG":
                        (out_dir / f"{stem}.svg").write_bytes(final_bytes)
                finally:
                    tmp_path.unlink(missing_ok=True)
    else:
        for idx, path in enumerate(input_paths):
            if abort_event and abort_event.is_set():
                raise Exception("Export aborted by user")
            _report_progress(on_progress, idx, total, f"Exporting {Path(path).name}")
            if fmt == "LINES":
                shutil.copy2(path, out_dir / Path(path).name)
            else:
                with contextlib.suppress(Exception):
                    doc = parse_lines(path)
                    img_bytes = doc.preview_image_data
                    if img_bytes:
                        _save_image_bytes(img_bytes, out_dir / f"{Path(path).stem}.{fmt.lower()}", fmt, multiplier)

    _report_progress(on_progress, total, total, "Done")


def _process_images(
    *,
    input_paths: list[str],
    style_path: str | None,
    end_style_path: str | None,
    output_path: str,
    fmt: str,
    size: str,
    relative_style: bool = False,
    abort_event: threading.Event | None = None,
    on_progress: Callable[[int, int, str], None] | None,
) -> None:
    """Process raster image exports."""
    total = len(input_paths)
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    multiplier = _parse_size_multiplier(size)

    style = _load_style(style_path) if style_path else None
    end_style = _load_style(end_style_path) if end_style_path else None

    if style is not None:
        with MCPClient() as client:
            for idx, path in enumerate(input_paths):
                if abort_event and abort_event.is_set():
                    raise Exception("Export aborted by user")

                _report_progress(on_progress, idx, total, f"Styling {Path(path).name}")

                stem = Path(path).stem
                try:
                    current_style = style
                    if end_style is not None and styles_compatible(style, end_style) and total > 1:
                        current_style = interpolate_style(style, end_style, idx / (total - 1))

                    res = apply_style(client, current_style, path, relative=relative_style)

                    if fmt == "SVG":
                        final_svg = res if isinstance(res, str) else res.decode()
                        (out_dir / f"{stem}.svg").write_text(final_svg, encoding="utf-8")
                    else:
                        svg_str = res if isinstance(res, str) else res.decode()
                        _save_svg_as_image(svg_str, out_dir / f"{stem}.{fmt.lower()}", fmt, multiplier)
                except Exception:
                    logger.opt(exception=True).warning("Style application failed for {}", path)
                    img_data = Path(path).read_bytes()
                    _save_image_bytes(img_data, out_dir / f"{stem}.{fmt.lower()}", fmt, multiplier)
    else:
        for idx, path in enumerate(input_paths):
            if abort_event and abort_event.is_set():
                raise Exception("Export aborted by user")
            _report_progress(on_progress, idx, total, f"Exporting {Path(path).name}")
            img_data = Path(path).read_bytes()
            _save_image_bytes(img_data, out_dir / f"{Path(path).stem}.{fmt.lower()}", fmt, multiplier)

    _report_progress(on_progress, total, total, "Done")


def _process_video(
    *,
    input_path: str,
    style_path: str | None,
    end_style_path: str | None,
    output_path: str,
    fmt: str,
    size: str,
    audio: bool,
    frame_range: tuple[int, int] | None,
    relative_style: bool = False,
    abort_event: threading.Event | None = None,
    on_progress: Callable[[int, int, str], None] | None,
) -> None:
    """Dispatch video processing."""
    if fmt == "MP4":
        _process_video_to_mp4(
            input_path=input_path,
            style_path=style_path,
            end_style_path=end_style_path,
            output_path=output_path,
            size=size,
            audio=audio,
            frame_range=frame_range,
            relative_style=relative_style,
            abort_event=abort_event,
            on_progress=on_progress,
        )
    else:
        _process_video_to_frames(
            input_path=input_path,
            style_path=style_path,
            end_style_path=end_style_path,
            output_path=output_path,
            fmt=fmt,
            size=size,
            frame_range=frame_range,
            relative_style=relative_style,
            abort_event=abort_event,
            on_progress=on_progress,
        )


def _process_video_to_mp4(
    *,
    input_path: str,
    style_path: str | None,
    end_style_path: str | None,
    output_path: str,
    size: str,
    audio: bool,
    frame_range: tuple[int, int] | None,
    relative_style: bool = False,
    abort_event: threading.Event | None = None,
    on_progress: Callable[[int, int, str], None] | None,
) -> None:
    """Full video-to-video processing."""
    info = probe(input_path)
    style = _load_style(style_path) if style_path else None
    end_style = _load_style(end_style_path) if end_style_path else None

    start = frame_range[0] if frame_range else 0
    end = frame_range[1] if frame_range else info.total_frames

    _report_progress(on_progress, 0, max(end - start, 1), "Processing video...")

    process_video_with_style(
        input_path=input_path,
        output_path=output_path,
        style=style,
        end_style=end_style,
        start_frame=start,
        end_frame=end,
        include_audio=audio,
        size_multiplier=_parse_size_multiplier(size),
        relative=relative_style,
        abort_event=abort_event,
    )


def _process_video_to_frames(
    *,
    input_path: str,
    style_path: str | None,
    end_style_path: str | None,
    output_path: str,
    fmt: str,
    size: str,
    frame_range: tuple[int, int] | None,
    relative_style: bool = False,
    abort_event: threading.Event | None = None,
    on_progress: Callable[[int, int, str], None] | None,
) -> None:
    """Extract styled video frames."""
    info = probe(input_path)
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    multiplier = _parse_size_multiplier(size)

    style = _load_style(style_path) if style_path else None
    end_style = _load_style(end_style_path) if end_style_path else None

    start = frame_range[0] if frame_range else 0
    end = min(frame_range[1] if frame_range else info.total_frames, info.total_frames)
    total = max(end - start, 1)

    cap = cv2.VideoCapture(input_path)
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start)

        with MCPClient() as client:
            for i in range(total):
                if abort_event and abort_event.is_set():
                    raise Exception("Export aborted by user")

                ret, frame = cap.read()
                if not ret:
                    break

                _report_progress(on_progress, i, total, f"Frame {start + i}")

                # Encode frame to PNG bytes
                _, buf = cv2.imencode(".png", frame)
                frame_bytes: bytes = buf.tobytes()

                if style is not None:
                    try:
                        t = i / total if total > 1 else 0.0
                        current_style = style
                        if end_style is not None and styles_compatible(style, end_style):
                            current_style = interpolate_style(style, end_style, t)

                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            tmp.write(frame_bytes)
                            tmp_path = Path(tmp.name)
                        try:
                            res = apply_style(client, current_style, str(tmp_path), relative=relative_style)
                            frame_bytes = res if isinstance(res, bytes) else res.encode()
                        finally:
                            tmp_path.unlink(missing_ok=True)
                    except Exception:
                        logger.opt(exception=True).debug("Style failed on frame {}", start + i)

                ext = fmt.lower()
                _save_image_bytes(frame_bytes, out_dir / f"frame_{start + i:06d}.{ext}", fmt, multiplier)
    finally:
        cap.release()
    _report_progress(on_progress, total, total, "Done")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_size_multiplier(size: str) -> int:
    """Parse size string."""
    m = re.match(r"(\d+)x", size)
    if m:
        return int(m.group(1))
    return 1


def _estimate_svg_dimensions(svg_string: str) -> tuple[int, int]:
    """Extract SVG dimensions."""
    vb = re.search(r'viewBox=["\'][\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)', svg_string)
    if vb:
        return int(float(vb.group(1))), int(float(vb.group(2)))
    w_match = re.search(r'width=["\'](\d+)', svg_string)
    h_match = re.search(r'height=["\'](\d+)', svg_string)
    w = int(w_match.group(1)) if w_match else 800
    h = int(h_match.group(1)) if h_match else 600
    return w, h


def _save_image_bytes(
    data: bytes,
    dest: Path,
    fmt: str,
    multiplier: int = 1,
) -> None:
    """Save raw image bytes."""
    if fmt == "SVG":
        dest.write_bytes(data)
        return
    img = Image.open(io.BytesIO(data))
    if multiplier > 1:
        new_size = (img.width * multiplier, img.height * multiplier)
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    pil_fmt = "JPEG" if fmt == "JPG" else fmt
    img.save(str(dest), format=pil_fmt)


def _save_svg_as_image(
    svg_data: str | bytes,
    dest: Path,
    fmt: str,
    multiplier: int = 1,
) -> None:
    """Rasterise SVG."""
    svg_str = svg_data if isinstance(svg_data, str) else svg_data.decode()
    w, h = _estimate_svg_dimensions(svg_str)
    img = _svg_to_pil(svg_str, w * multiplier, h * multiplier)
    pil_fmt = "JPEG" if fmt == "JPG" else fmt
    img.save(str(dest), format=pil_fmt)


def _load_style(path: str) -> Any:
    """Load Style."""
    try:
        return extract_style(path)
    except Exception:
        logger.opt(exception=True).warning("Could not load style from {}", path)
        return None


# ---------------------------------------------------------------------------
# Callback helpers
# ---------------------------------------------------------------------------


def _report_progress(
    callback: Callable[[int, int, str], None] | None,
    current: int,
    total: int,
    message: str,
) -> None:
    """Report progress."""
    if callback is not None:
        with contextlib.suppress(Exception):
            callback(current, total, message)


def _report_complete(callback: Callable[[str], None] | None, message: str) -> None:
    """Report completion."""
    if callback is not None:
        with contextlib.suppress(Exception):
            callback(message)


def _report_error(callback: Callable[[str], None] | None, message: str) -> None:
    """Report error."""
    if callback is not None:
        with contextlib.suppress(Exception):
            callback(message)
