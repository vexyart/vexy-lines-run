# API Reference

## App

### `App(customtkinter.CTk)`

The main GUI window. Handles layout, file management, style selection, and export dispatch.

```python
from vexy_lines_run import App

app = App()
app.mainloop()
```

**Window defaults:** Title "Vexy Lines Run", 1024x768, minimum 960x480.

**Key instance attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `abort_event` | `threading.Event` | Set this to cancel a running export |
| `format_var` | `tk.StringVar` | Current export format ("SVG", "PNG", "JPG", "MP4", "LINES") |
| `size_var` | `tk.StringVar` | Current size multiplier ("1x", "2x", "3x", "4x", or "—") |
| `audio_var` | `tk.BooleanVar` | Include audio in video exports |
| `inputs_tabview` | `CTkTabview` | The Lines/Images/Video tab container |
| `styles_tabview` | `CTkTabview` | The Style/End Style tab container |
| `progress_bar` | `CTkProgressBar` | Export progress (hidden until export starts) |
| `convert_button` | `CTkButton` | The Export/Stop button |

### `launch() -> None`

Creates an `App` and calls `mainloop()`. The simplest way to start the GUI.

```python
from vexy_lines_run import launch
launch()
```

---

## Processing

### `process_export(...) -> None`

The export pipeline. Dispatches to mode-specific processors based on the `mode` parameter. Called by `App` on a background thread, but works fine called directly for scripting.

```python
from vexy_lines_run.processing import process_export

process_export(
    mode="images",
    input_paths=["photo.jpg"],
    style_path="style.lines",
    end_style_path=None,
    output_path="./output",
    fmt="SVG",
    size="1x",
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `str` | — | `"lines"`, `"images"`, or `"video"` |
| `input_paths` | `list[str]` | — | Paths to input files. For video mode, a single-element list. |
| `style_path` | `str \| None` | — | Path to primary `.lines` style file, or `None` |
| `end_style_path` | `str \| None` | — | Path to end `.lines` style file for interpolation, or `None` |
| `output_path` | `str` | — | Output directory (or `.mp4` filepath for video) |
| `fmt` | `str` | — | `"SVG"`, `"PNG"`, `"JPG"`, `"MP4"`, or `"LINES"` |
| `size` | `str` | — | `"1x"`, `"2x"`, `"3x"`, `"4x"`, or `"—"` |
| `audio` | `bool` | `True` | Include audio track in MP4 output |
| `frame_range` | `tuple[int, int] \| None` | `None` | Start and end frame indexes (0-based, inclusive). Video mode only. The GUI converts its 1-based controls before dispatch. |
| `relative_style` | `bool` | `False` | Use relative style scaling |
| `abort_event` | `threading.Event \| None` | `None` | Set to cancel mid-export |
| `on_progress` | `Callable[[int, int, str], None] \| None` | `None` | Called with `(current, total, message)` after each file |
| `on_complete` | `Callable[[str], None] \| None` | `None` | Called with a summary message on success |
| `on_error` | `Callable[[str], None] \| None` | `None` | Called with an error message on failure |

**Mode behavior:**

| Mode | Style required? | What happens |
|------|----------------|-------------|
| `"lines"` | No | With style: applies style to each file's source image via MCP. Without: opens in Vexy Lines, renders, exports. Format=LINES: file copy. |
| `"images"` | Yes | Applies style to each image via MCP. Falls back to original image on per-file failure. |
| `"video"` + MP4 | Yes | Full video re-encode with per-frame style transfer. Audio passthrough controlled by `audio`. |
| `"video"` + PNG/JPG | Yes | Extracts frames, styles each one, saves as `frame_NNNNNN.ext`. |

**Callbacks** are invoked on the calling thread. When `App` uses this function, it marshals them to the main Tk thread via `self.after(0, callback)`.

**Exceptions** are caught internally and passed to `on_error`. The function does not raise.

### Size multiplier parsing

The `size` string is parsed internally:

| Input | Multiplier | Effect |
|-------|-----------|--------|
| `"1x"` | 1 | Original resolution |
| `"2x"` | 2 | Double width and height (Lanczos resampling) |
| `"3x"` | 3 | Triple |
| `"4x"` | 4 | Quadruple |
| `"—"` | 1 | Same as 1x (used for SVG/LINES) |

---

## Video

Re-exported from `vexy_lines_api.video`. Video dependencies (PyAV, OpenCV, resvg-py, svglab) are included in the base install.

### `VideoInfo`

Dataclass returned by `probe()` and `process_video()`.

| Field | Type | Description |
|-------|------|-------------|
| `width` | `int` | Frame width in pixels |
| `height` | `int` | Frame height in pixels |
| `fps` | `float` | Frames per second |
| `total_frames` | `int` | Total frame count |
| `duration` | `float` | Duration in seconds |
| `has_audio` | `bool` | Whether an audio stream exists |

### `probe(path: str) -> VideoInfo`

Read video metadata without decoding any frames. Returns instantly even for large files.

```python
from vexy_lines_run.video import probe

info = probe("clip.mp4")
print(f"{info.width}x{info.height} @ {info.fps}fps")
print(f"{info.total_frames} frames, {info.duration:.1f}s")
print(f"Audio: {'yes' if info.has_audio else 'no'}")
```

### `process_video(...) -> VideoInfo`

Decode a video, process each frame through a callback, and re-encode to a new file.

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

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_path` | `str` | — | Source video file |
| `output_path` | `str` | — | Destination video file |
| `frame_params` | `Callable[[int, int], dict]` | — | Called with `(frame_index, total_frames)`, returns fill parameter overrides |
| `max_frames` | `int \| None` | `None` | Limit processing to N frames |
| `host` | `str` | `"127.0.0.1"` | MCP server host |
| `port` | `int` | `47384` | MCP server port |
| `dpi` | `int` | `72` | Document DPI for the Vexy Lines engine |

Returns a `VideoInfo` with the output video's metadata.

---

## Widgets

### `CTkRangeSlider`

A dual-handle range slider for CustomTkinter. Used in the Video tab to select frame ranges. Works as a standalone widget in any CustomTkinter app.

```python
import customtkinter as ctk
from vexy_lines_run.widgets import CTkRangeSlider

slider = CTkRangeSlider(
    parent,
    from_=0,
    to=100,
    number_of_steps=100,
    command=lambda low, high: print(f"{low}-{high}"),
)
slider.pack(fill="x", padx=10)
```

**Constructor parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `master` | widget | — | Parent widget |
| `width` | `int` | `200` | Widget width (horizontal) or `16` (vertical) |
| `height` | `int` | `16` | Widget height (horizontal) or `200` (vertical) |
| `corner_radius` | `int` | auto | Track corner radius |
| `button_corner_radius` | `int` | auto | Thumb corner radius |
| `border_width` | `int` | `0` | Track border width |
| `button_length` | `int` | auto | Thumb width in pixels |
| `fg_color` | `str \| tuple` | theme | Track background color |
| `border_color` | `str \| tuple` | theme | Track border color |
| `progress_color` | `str \| tuple` | theme | Color of the bar between thumbs |
| `button_color` | `str \| tuple` | theme | Thumb color (or tuple for individual thumbs) |
| `button_hover_color` | `str \| tuple` | theme | Thumb color on hover |
| `from_` | `float` | `0` | Minimum output value |
| `to` | `float` | `1` | Maximum output value |
| `number_of_steps` | `int \| None` | `None` | Quantize to this many steps (e.g. 100 for integer percentages) |
| `state` | `str` | `"normal"` | `"normal"` or `"disabled"` |
| `hover` | `bool` | `True` | Enable hover highlighting on thumbs |
| `command` | `callable \| None` | `None` | Called with `(low, high)` on every value change |
| `variables` | `tuple[tk.Variable, tk.Variable] \| None` | `None` | Bind to two Tk variables for two-way sync |
| `orientation` | `str` | `"horizontal"` | `"horizontal"` or `"vertical"` |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get()` | `tuple[float, float]` | Current `(low, high)` output values |
| `set(values)` | — | Set both values. Accepts `[low, high]` list. |
| `configure(**kwargs)` | — | Update any constructor parameter at runtime |
| `cget(name)` | `object` | Read a property value |
| `bind(seq, cmd)` | — | Bind an event handler (preserves internal bindings) |
| `unbind(seq)` | — | Remove an event handler |
| `focus()` | — | Give keyboard focus to the slider |

**Interaction behavior:**

- Click anywhere on the track to jump the nearest thumb to that position
- Drag a thumb to slide it
- Hovering over a thumb highlights it (if `hover=True`)
- The slider prevents the low thumb from exceeding the high thumb and vice versa
- With `number_of_steps` set, values snap to discrete positions

**Theming:** Follows CustomTkinter's dark/light appearance mode. All colors accept `(light_value, dark_value)` tuples for per-mode styling. The drawing engine auto-selects the best rendering backend for the platform.

---

## Utility functions

These are internal to `app.py` but useful to understand:

### `extract_preview_from_lines(filepath: str) -> bytes | None`

Extract the embedded preview or source image from a `.lines` file. Parses the XML, looks for `PreviewDoc` or `SourcePict` elements, decompresses zlib data if needed. Returns raw image bytes (typically PNG) or `None` if extraction fails.

### `extract_frame(video_path: str, frame_number: int) -> Image.Image | None`

Extract a single frame from a video file using OpenCV. Frame numbers are 1-indexed. Returns a PIL Image in RGB mode, or `None` if extraction fails.

### `fit_image_to_box(image: Image.Image, width: int, height: int) -> Image.Image`

Scale an image to fit within the given box while preserving aspect ratio. Converts RGBA to RGB with a white background. Uses Lanczos resampling.
