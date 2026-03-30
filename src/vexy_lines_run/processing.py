# this_file: src/vexy_lines_run/processing.py
"""Export processing pipeline for the Vexy Lines GUI.

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

import io
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Callable

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
    on_progress: Callable[[int, int, str], None] | None = None,
    on_complete: Callable[[str], None] | None = None,
    on_error: Callable[[str], None] | None = None,
) -> None:
    """Dispatch an export job.

    Called from a background thread by :class:`~vexy_lines_run.app.App`.

    Args:
        mode: One of ``"lines"``, ``"images"``, ``"video"``.
        input_paths: Paths to input files.
        style_path: Path to the style ``.lines`` file, or ``None``.
        end_style_path: Path to the end-style ``.lines`` file, or ``None``.
        output_path: Output file or directory path.
        fmt: Export format (``"SVG"``, ``"PNG"``, ``"JPG"``, ``"MP4"``,
            ``"LINES"``).
        size: Size multiplier string (``"1x"``, ``"2x"``).
        audio: Whether to include audio (video mode only).
        frame_range: Optional ``(start, end)`` frame indices for video.
        relative_style: Scale spatial fill parameters to match the target
            image/frame dimensions.  Default ``False`` (absolute mode).
        on_progress: Progress callback ``(fraction, message)``.
        on_complete: Success callback ``(message)``.
        on_error: Error callback ``(error_message)``.
    """
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
                on_progress=on_progress,
            )
        else:
            _report_error(on_error, f"Unknown mode: {mode}")
            return

        _report_complete(on_complete, f"Export complete ({fmt})")
    except Exception as exc:
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
    on_progress: Callable[[int, int, str], None] | None,
) -> None:
    """Process .lines file exports.

    Extracts embedded previews/source images from ``.lines`` files and saves
    them in the requested format.
    """
    from vexy_lines import parse as parse_lines

    total = len(input_paths)
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    multiplier = _parse_size_multiplier(size)

    for idx, path in enumerate(input_paths):
        _report_progress(on_progress, idx, total, f"Processing {Path(path).name}")

        if fmt == "LINES":
            # Copy the .lines file directly
            import shutil

            shutil.copy2(path, out_dir / Path(path).name)
            continue

        # Extract preview or source image bytes from the parsed document
        try:
            doc = parse_lines(path)
        except Exception:
            logger.opt(exception=True).warning("Could not parse {}", path)
            continue
        img_bytes: bytes | None = doc.source_image_data
        if img_bytes is None:
            img_bytes = doc.preview_image_data

        if img_bytes is None:
            logger.warning("No image data in {}", path)
            continue

        # Apply style if provided
        if style_path is not None:
            img_bytes = _apply_style_to_bytes(img_bytes, style_path, end_style_path, relative=relative_style)

        stem = Path(path).stem
        if fmt in ("PNG", "JPG"):
            _save_image_bytes(img_bytes, out_dir / f"{stem}.{fmt.lower()}", fmt, multiplier)
        elif fmt == "SVG":
            # SVG bytes written directly
            (out_dir / f"{stem}.svg").write_bytes(img_bytes if isinstance(img_bytes, bytes) else img_bytes.encode())

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
    on_progress: Callable[[int, int, str], None] | None,
) -> None:
    """Process raster image exports via the MCP style engine."""
    from vexy_lines_api import MCPClient, apply_style, interpolate_style, styles_compatible

    total = len(input_paths)
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    multiplier = _parse_size_multiplier(size)

    # Load styles once
    style = _load_style(style_path) if style_path else None
    end_style = _load_style(end_style_path) if end_style_path else None

    for idx, path in enumerate(input_paths):
        _report_progress(on_progress, idx, total, f"Styling {Path(path).name}")

        stem = Path(path).stem

        if style is not None:
            try:
                current_style = style
                if end_style is not None and styles_compatible(style, end_style) and total > 1:
                    t = idx / (total - 1)
                    current_style = interpolate_style(style, end_style, t)

                with MCPClient() as client:
                    svg_string = apply_style(
                        client, current_style, path,
                        relative=relative_style,
                    )

                if fmt == "SVG":
                    (out_dir / f"{stem}.svg").write_text(svg_string, encoding="utf-8")
                else:
                    _save_svg_as_image(svg_string, out_dir / f"{stem}.{fmt.lower()}", fmt, multiplier)
                continue
            except Exception:
                logger.opt(exception=True).warning("Style application failed for {}", path)

        # No style — just copy the image with optional resize
        img_data = Path(path).read_bytes()
        ext = fmt.lower()
        _save_image_bytes(img_data, out_dir / f"{stem}.{ext}", fmt, multiplier)

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
    on_progress: Callable[[int, int, str], None] | None,
) -> None:
    """Dispatch video processing to the appropriate handler."""
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
    on_progress: Callable[[int, int, str], None] | None,
) -> None:
    """Full video-to-video processing via the style engine."""
    from vexy_lines_api.video import probe, process_video_with_style

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
    on_progress: Callable[[int, int, str], None] | None,
) -> None:
    """Extract styled video frames as individual image files."""
    from vexy_lines_api import MCPClient, apply_style, interpolate_style, styles_compatible

    from vexy_lines_api.video import probe

    info = probe(input_path)
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    multiplier = _parse_size_multiplier(size)

    style = _load_style(style_path) if style_path else None
    end_style = _load_style(end_style_path) if end_style_path else None

    start = frame_range[0] if frame_range else 0
    end = min(frame_range[1] if frame_range else info.total_frames, info.total_frames)
    total = max(end - start, 1)

    try:
        import cv2  # type: ignore[import-untyped]
    except ImportError as exc:
        msg = "opencv-python is required for frame extraction"
        raise ImportError(msg) from exc

    cap = cv2.VideoCapture(input_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)

    for i in range(total):
        ret, frame = cap.read()
        if not ret:
            break

        _report_progress(on_progress, i, total, f"Frame {start + i}")

        # Encode frame to PNG bytes
        _, buf = cv2.imencode(".png", frame)
        frame_bytes: bytes = buf.tobytes()

        if style is not None:
            try:
                with MCPClient() as client:
                    t = i / total if total > 1 else 0.0
                    current_style = style
                    if end_style is not None and styles_compatible(style, end_style):
                        current_style = interpolate_style(style, end_style, t)
                    frame_bytes = apply_style(client, frame_bytes, current_style, relative=relative_style)
            except Exception:
                logger.opt(exception=True).debug("Style failed on frame {}", start + i)

        ext = fmt.lower()
        _save_image_bytes(frame_bytes, out_dir / f"frame_{start + i:06d}.{ext}", fmt, multiplier)

    cap.release()
    _report_progress(on_progress, total, total, "Done")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_size_multiplier(size: str) -> int:
    """Parse a size string like ``"1x"`` or ``"2x"`` into an integer multiplier.

    Args:
        size: Size string.

    Returns:
        Integer multiplier (defaults to 1 for unrecognised input).
    """
    m = re.match(r"(\d+)x", size)
    if m:
        return int(m.group(1))
    return 1


def _estimate_svg_dimensions(svg_string: str) -> tuple[int, int]:
    """Extract width and height from an SVG string's ``viewBox`` or attributes.

    Args:
        svg_string: Raw SVG markup.

    Returns:
        ``(width, height)`` tuple; defaults to ``(800, 600)`` if parsing fails.
    """
    # Try viewBox first
    vb = re.search(r'viewBox=["\'][\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)', svg_string)
    if vb:
        return int(float(vb.group(1))), int(float(vb.group(2)))

    # Fall back to width/height attributes
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
    """Save raw image bytes (PNG/JPG/SVG) to *dest*, optionally scaling.

    Args:
        data: Raw image bytes.
        dest: Destination file path.
        fmt: Format hint (``"PNG"``, ``"JPG"``, ``"SVG"``).
        multiplier: Integer scale factor applied to raster output.
    """
    from PIL import Image

    if fmt == "SVG":
        dest.write_bytes(data)
        return

    img = Image.open(io.BytesIO(data))
    if multiplier > 1:
        new_size = (img.width * multiplier, img.height * multiplier)
        img = img.resize(new_size, Image.LANCZOS)

    pil_fmt = "JPEG" if fmt == "JPG" else fmt
    img.save(str(dest), format=pil_fmt)


def _save_svg_as_image(
    svg_data: str | bytes,
    dest: Path,
    fmt: str,
    multiplier: int = 1,
) -> None:
    """Rasterise SVG data and save as a raster image.

    Attempts to use ``resvg-py`` first, falling back to ``svglab`` if
    available.

    Args:
        svg_data: SVG string or bytes.
        dest: Output path.
        fmt: Target raster format (``"PNG"`` or ``"JPG"``).
        multiplier: Scale factor.
    """
    from vexy_lines_api.video import _svg_to_pil

    svg_str = svg_data if isinstance(svg_data, str) else svg_data.decode()
    w, h = _estimate_svg_dimensions(svg_str)
    img = _svg_to_pil(svg_str, w * multiplier, h * multiplier)
    pil_fmt = "JPEG" if fmt == "JPG" else fmt
    img.save(str(dest), format=pil_fmt)


def _load_style(path: str) -> Any:
    """Load a :class:`~vexy_lines_api.Style` from a ``.lines`` file.

    Args:
        path: Filesystem path to the ``.lines`` file.

    Returns:
        A ``Style`` object, or ``None`` on failure.
    """
    try:
        from vexy_lines_api import extract_style

        return extract_style(path)
    except Exception:
        logger.opt(exception=True).warning("Could not load style from {}", path)
        return None


def _apply_style_to_bytes(
    img_bytes: bytes,
    style_path: str,
    end_style_path: str | None,
    *,
    relative: bool = False,
) -> str | bytes:
    """Apply a style to raw image bytes via a temp file, returning SVG string.

    Writes the image bytes to a temp file, applies the style via MCP, and
    returns the SVG result.  Falls back to the original bytes on failure.

    Args:
        img_bytes: Source image data (JPEG or PNG).
        style_path: Path to the primary style ``.lines`` file.
        end_style_path: Optional path to the end-style ``.lines`` file.
        relative: Scale spatial fill parameters to match target dimensions.

    Returns:
        SVG string on success, or the original bytes on failure.
    """
    import tempfile

    try:
        from vexy_lines_api import MCPClient, apply_style, interpolate_style, styles_compatible

        style = _load_style(style_path)
        if style is None:
            return img_bytes

        current_style = style
        if end_style_path:
            end_style = _load_style(end_style_path)
            if end_style is not None and styles_compatible(style, end_style):
                current_style = interpolate_style(style, end_style, 0.5)

        # Write bytes to a temp file so apply_style can use the path
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = Path(tmp.name)

        try:
            with MCPClient() as client:
                return apply_style(client, current_style, str(tmp_path), relative=relative)
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception:
        logger.opt(exception=True).warning("Style application failed")
        return img_bytes


# ---------------------------------------------------------------------------
# Callback helpers
# ---------------------------------------------------------------------------


def _report_progress(
    callback: Callable[[int, int, str], None] | None,
    current: int,
    total: int,
    message: str,
) -> None:
    """Safely invoke the progress callback.

    Args:
        callback: The progress function, or ``None``.
        current: Current item index (0-based).
        total: Total number of items.
        message: Human-readable status string.
    """
    if callback is not None:
        try:
            callback(current, total, message)
        except Exception:
            logger.opt(exception=True).debug("Progress callback failed")


def _report_complete(callback: Callable[[str], None] | None, message: str) -> None:
    """Safely invoke the completion callback.

    Args:
        callback: The completion function, or ``None``.
        message: Human-readable success message.
    """
    if callback is not None:
        try:
            callback(message)
        except Exception:
            logger.opt(exception=True).debug("Complete callback failed")


def _report_error(callback: Callable[[str], None] | None, message: str) -> None:
    """Safely invoke the error callback.

    Args:
        callback: The error function, or ``None``.
        message: Human-readable error description.
    """
    if callback is not None:
        try:
            callback(message)
        except Exception:
            logger.opt(exception=True).debug("Error callback failed")
