# API Reference

## App

### `App(customtkinter.CTk)`

The main GUI window. Handles layout, file management, style selection, and export dispatch.

```python
from vexy_lines_run import App

app = App()
app.mainloop()
```

**Window defaults:** Title "Style with Vexy Lines", 900x700, minimum 960x480.

**Constructor:** Takes no arguments. Builds the entire widget tree, registers drop targets, and configures initial state.

**Key instance attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `format_var` | `tk.StringVar` | Current export format ("SVG", "PNG", "JPG", "MP4", "LINES") |
| `size_var` | `tk.StringVar` | Current size multiplier ("1x", "2x", "3x", "4x", or "—") |
| `audio_var` | `tk.BooleanVar` | Include audio in video exports |
| `inputs_tabview` | `CTkTabview` | The Lines/Images/Video tab container |
| `styles_tabview` | `CTkTabview` | The Style/End Style tab container |
| `convert_button` | `CTkButton` | The Export/Stop button |

**Internal state (not part of public API but useful to understand):**

| Attribute | Type | Description |
|-----------|------|-------------|
| `_style_paths` | `dict[str, str \| None]` | Maps `"start"`/`"end"` to loaded style file paths |
| `_image_paths` | `list[str]` | Loaded image file paths |
| `_lines_paths` | `list[str]` | Loaded .lines file paths |
| `_video_path` | `str` | Loaded video file path (empty if none) |
| `_video_total_frames` | `int` | Frame count of loaded video |
| `_video_has_audio` | `bool` | Whether loaded video has an audio stream |
| `_video_range` | `tuple[int, int]` | Selected frame range (1-indexed, inclusive) |
| `_output_path` | `str` | Last selected output directory or file path |

### `launch() -> None`

Creates an `App` and calls `mainloop()`. Sets CustomTkinter to dark appearance mode. The simplest way to start the GUI.

```python
from vexy_lines_run import launch
launch()
```

Equivalent to:

```python
import customtkinter
from vexy_lines_run import App

customtkinter.set_appearance_mode("dark")
app = App()
app.lift()
app.attributes("-topmost", True)
app.after(100, lambda: app.attributes("-topmost", False))
app.mainloop()
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
    audio=False,
    frame_range=None,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `str` | — | `"lines"`, `"images"`, or `"video"` |
| `input_paths` | `list[str]` | — | Paths to input files. For video mode, a single-element list with the video path. |
| `style_path` | `str \| None` | — | Path to primary `.lines` style file, or `None` |
| `end_style_path` | `str \| None` | — | Path to end `.lines` style file for interpolation, or `None` |
| `output_path` | `str` | — | Output directory (or `.mp4` filepath for video MP4 mode) |
| `fmt` | `str` | — | `"SVG"`, `"PNG"`, `"JPG"`, `"MP4"`, or `"LINES"` |
| `size` | `str` | — | `"1x"`, `"2x"`, `"3x"`, `"4x"`, or `"—"` |
| `audio` | `bool` | — | Include audio track in MP4 output (keyword-only) |
| `frame_range` | `tuple[int, int] \| None` | — | Start and end frame numbers (1-indexed, inclusive) for video mode. `None` means all frames. (keyword-only) |
| `on_progress` | `Callable[[int, int, str], None] \| None` | `None` | Called with `(current, total, message)` after each file/frame |
| `on_complete` | `Callable[[str], None] \| None` | `None` | Called with a summary message on success |
| `on_error` | `Callable[[str], None] \| None` | `None` | Called with an error message on failure |

Note: `audio` and `frame_range` are keyword-only parameters.

**Mode behavior:**

| Mode | Style required? | What happens |
|------|----------------|-------------|
| `"lines"` + LINES | No | File copy to output directory |
| `"lines"` + PNG/JPG | No | Extracts embedded preview image from each .lines file |
| `"lines"` + SVG | N/A | Returns error — SVG export from .lines requires Images mode with a style |
| `"images"` | Yes | Applies style to each image via MCP. Each image → new Vexy Lines document → apply fill tree → render → export SVG → optionally rasterise |
| `"video"` + MP4 | Yes | Full video re-encode with per-frame style transfer. Audio passthrough when `audio=True` and source has audio and full range selected. |
| `"video"` + PNG/JPG/SVG | Yes | Extracts frames, styles each one, saves as `frame_NNNNNN.ext` |

**Callbacks** are invoked on the calling thread. When `App` uses this function, it marshals them to the main Tk thread via `self.after(0, callback)`.

**Exceptions** are caught internally and passed to `on_error`. The function does not raise.

### Size multiplier parsing

The `size` string is parsed internally by `_parse_size_multiplier()`:

| Input | Multiplier | Effect |
|-------|-----------|--------|
| `"1x"` | 1.0 | Original resolution |
| `"2x"` | 2.0 | Double width and height (Lanczos resampling) |
| `"3x"` | 3.0 | Triple |
| `"4x"` | 4.0 | Quadruple |
| `"—"` | 1.0 | Same as 1x (used for SVG/LINES) |

Values below 1.0 are clamped to 1.0.

### Progress reporting

The `on_progress` callback receives three arguments:

- `current` (int): 0-indexed count of processed items
- `total` (int): total number of items to process
- `message` (str): human-readable status, e.g. `"Styling bear_03..."` or `"Frame 5/30"` or `"Done"`

The final call is always `(total, total, "Done")` on success.

### Error handling and recovery

All exceptions inside `process_export()` are caught and routed to `on_error`. The function never raises. Error messages include:

| Error | Cause |
|-------|-------|
| `"No input files selected."` | Empty `input_paths` list |
| `"A style file is required for Images mode."` | `style_path` is `None` in images mode |
| `"A style file is required for Video mode."` | `style_path` is `None` in video mode |
| `"Failed to read style: ..."` | Style .lines file can't be parsed |
| `"Start and end styles have incompatible structures."` | End style doesn't match start style's fill tree |
| `"MCP error: ...\n\nMake sure Vexy Lines is running."` | MCP connection refused or tool call failed |
| `"SVG export from .lines files requires the Vexy Lines app (MCP)."` | SVG format selected in lines mode |
| `"Unsupported format for Lines mode: ..."` | Invalid format for the mode |

---

## Video

Re-exported from `vexy_lines_api.video`. Video dependencies (OpenCV, svglab/resvg-py) must be installed.

### `VideoInfo`

Dataclass with video file metadata.

```python
from dataclasses import dataclass

@dataclass
class VideoInfo:
    width: int          # Frame width in pixels
    height: int         # Frame height in pixels
    fps: float          # Frames per second
    total_frames: int   # Total frame count
    duration: float     # Duration in seconds
    has_audio: bool     # Whether an audio stream exists
```

### `probe(path: str | Path) -> VideoInfo`

Read video metadata without decoding any frames. Uses OpenCV's `VideoCapture` for dimensions/fps/frame count and ffprobe for audio detection. Returns instantly even for large files.

```python
from vexy_lines_run.video import probe

info = probe("clip.mp4")
print(f"{info.width}x{info.height} @ {info.fps}fps")
print(f"{info.total_frames} frames, {info.duration:.1f}s")
print(f"Audio: {'yes' if info.has_audio else 'no'}")
```

**Raises:**
- `RuntimeError` if the video file can't be opened
- `ImportError` if opencv-python-headless is not installed

**Audio detection:** Uses ffprobe (best-effort). If ffprobe is not on PATH, `has_audio` returns `False`.

### `process_video(...) -> VideoInfo`

Low-level video processing: decode frames, apply a single fill type per frame, re-encode. This is the standalone function that creates fills from scratch (fill_type + params), not from a `.lines` style file.

```python
from vexy_lines_run.video import process_video

def frame_callback(frame_index, total_frames):
    progress = frame_index / max(total_frames - 1, 1)
    return {"angle": progress * 180.0, "interval": 15.0}

info = process_video(
    input_path="clip.mp4",
    output_path="result.mp4",
    fill_type="linear",
    color="#000000",
    interval=20,
    thickness=15,
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
| `input_path` | `str \| Path` | — | Source video file |
| `output_path` | `str \| Path` | — | Destination video file |
| `fill_type` | `str` | `"linear"` | Fill algorithm name |
| `color` | `str` | `"#000000"` | Fill colour as hex string |
| `interval` | `float` | `20` | Spacing between strokes in pixels |
| `thickness` | `float` | `15` | Maximum stroke thickness |
| `thickness_min` | `float` | `0` | Minimum stroke thickness |
| `dpi` | `int` | `72` | Document DPI for the Vexy Lines engine |
| `frame_params` | `Callable[[int, int], dict] \| None` | `None` | Called with `(frame_index, total_frames)`, returns fill parameter overrides. When `None`, angle rotates from 0 to 180 degrees across the video. |
| `max_frames` | `int \| None` | `None` | Limit processing to first N frames |
| `on_progress` | `Callable[[int, int], None] \| None` | `None` | Called with `(frame_index, total_frames)` after each frame |
| `host` | `str` | `"127.0.0.1"` | MCP server host |
| `port` | `int` | `47384` | MCP server port |
| `timeout` | `float` | `60.0` | Render timeout per frame in seconds |

**Returns:** `VideoInfo` of the input video.

**Raises:**
- `ImportError` if required packages are missing
- `MCPError` if the MCP server is unreachable

### `process_video_with_style(...) -> VideoInfo`

Higher-level video processing using extracted `Style` objects. Supports style interpolation across a frame range. This is what the GUI's processing pipeline uses internally.

```python
from vexy_lines_run.video import process_video_with_style
from vexy_lines_apy.style import extract_style

style = extract_style("halftone.lines")
end_style = extract_style("scribble.lines")

info = process_video_with_style(
    input_path="clip.mp4",
    output_path="result.mp4",
    style=style,
    end_style=end_style,
    start_frame=0,
    end_frame=150,
    dpi=72,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_path` | `str \| Path` | — | Source video file |
| `output_path` | `str \| Path` | — | Destination video file |
| `style` | `Style` | — | Start style object (from `extract_style()`) |
| `end_style` | `Style \| None` | `None` | End style for interpolation |
| `dpi` | `int` | `72` | Document DPI |
| `max_frames` | `int \| None` | `None` | Limit frames from start_frame |
| `start_frame` | `int` | `0` | First frame to process (0-based, inclusive) |
| `end_frame` | `int \| None` | `None` | Last frame to process (0-based, exclusive). `None` = all frames. |
| `on_progress` | `Callable[[int, int], None] \| None` | `None` | Called with `(frame_index, total_frames)` |
| `host` | `str` | `"127.0.0.1"` | MCP server host |
| `port` | `int` | `47384` | MCP server port |
| `timeout` | `float` | `60.0` | Render timeout per frame |

**Returns:** `VideoInfo` of the input video.

**Note:** `start_frame` and `end_frame` are 0-based in this function, unlike the GUI which presents 1-indexed values to the user.

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

**Theming:** Follows CustomTkinter's dark/light appearance mode. All colors accept `(light_value, dark_value)` tuples for per-mode styling. The drawing engine auto-selects the best rendering backend for the platform (circle_shapes on macOS, font_shapes elsewhere).

---

## Utility functions

These are internal to `app.py` but useful to understand:

### `extract_preview_from_lines(filepath: str) -> Image.Image | None`

Extract the embedded preview image from a `.lines` file. Parses the XML, looks for the `PreviewDoc` element, decodes the base64 content. Returns a PIL Image or `None` if extraction fails (missing element, corrupt data, parse error).

### `extract_frame(video_path: str, frame_number: int) -> Image.Image | None`

Extract a single frame from a video file using OpenCV. Frame numbers are 1-indexed. Returns a PIL Image in RGB mode, or `None` if extraction fails or OpenCV is not installed.

### `fit_image_to_box(image: Image.Image, width: int, height: int) -> Image.Image`

Scale an image to fit within the given box while preserving aspect ratio. Uses Lanczos resampling. The result is pasted onto a dark canvas (`#1d1f22`) at position (0, 0), so the image sits in the top-left corner with dark padding on the right and/or bottom.

### `truncate_start(text: str, max_chars: int = 20) -> str`

Trim leading characters, keeping only the last `max_chars` characters. Prepends "…" if truncated.

### `truncate_middle(text: str, max_width: int) -> str`

Shorten text by replacing the middle with "⋮", keeping roughly equal amounts from the start and end.

### `create_placeholder_image(width: int, height: int, text: str) -> Image.Image`

Returns a plain dark-grey (`#1d1f22`) image. The `text` parameter is accepted but not rendered — the placeholder is a solid color block.
