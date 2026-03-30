# API Reference

## App

### `App(CTk)`

The main GUI application window. Subclass of `customtkinter.CTk`.

```python
from vexy_lines_run import App

app = App()
app.mainloop()
```

Creates the three-tab layout, style pickers, export controls, and progress bar. Export runs on a daemon thread via `processing.process_export()`.

### `launch() -> None`

Convenience function that creates an `App` instance and calls `mainloop()`.

```python
from vexy_lines_run import launch

launch()
```

---

## Processing

### `process_export(...) -> None`

Background thread dispatcher for all export modes. Called internally by `App` when the Export button is pressed.

Handles three input types:

- **Lines files** -- extracts previews or applies styles depending on configuration
- **Image files** -- applies style via MCP, exports as SVG/PNG/JPG
- **Video files** -- per-frame style transfer with PyAV decode/encode

Parameters are passed via the `App` instance's current state (selected files, style, format, DPI, etc.).

Progress callbacks (`on_progress`, `on_complete`, `on_error`) are invoked on the background thread. The `App` marshals them to the main thread via `self.after(0, callback)`.

---

## Video

Requires the `[video]` extra: PyAV, OpenCV, resvg-py, svglab.

### `VideoInfo`

Dataclass with video metadata.

| Field | Type | Description |
|-------|------|-------------|
| `width` | `int` | Frame width in pixels |
| `height` | `int` | Frame height in pixels |
| `fps` | `float` | Frames per second |
| `total_frames` | `int` | Total frame count |
| `duration` | `float` | Duration in seconds |
| `has_audio` | `bool` | Whether an audio stream exists |

### `probe(path) -> VideoInfo`

Read video metadata without decoding frames.

```python
from vexy_lines_run.video import probe

info = probe("clip.mp4")
print(f"{info.width}x{info.height} @ {info.fps}fps, {info.total_frames} frames")
```

### `process_video(...) -> VideoInfo`

Decode a video, process each frame through a callback, and re-encode to a new video.

```python
from vexy_lines_run.video import process_video

def frame_callback(frame_index, total_frames):
    return {"angle": 45, "interval": 2.0}

info = process_video(
    input_path="clip.mp4",
    output_path="result.mp4",
    frame_params=frame_callback,
    max_frames=100,
    host="127.0.0.1",
    port=47384,
    dpi=72,
)
```

---

## Widgets

### `CTkRangeSlider`

A dual-handle range slider built on CustomTkinter. Used in the Video tab for selecting start/end frame ranges.

```python
from vexy_lines_run.widgets import CTkRangeSlider

slider = CTkRangeSlider(
    parent,
    from_=0,
    to=100,
    command=lambda low, high: print(f"Range: {low}-{high}"),
)
slider.pack()
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `from_` | `float` | Minimum value |
| `to` | `float` | Maximum value |
| `command` | `callable` | Called with `(low, high)` on change |
