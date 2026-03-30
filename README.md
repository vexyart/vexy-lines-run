# vexy-lines-run

Desktop GUI for [Vexy Lines](https://vexy.art) style transfer — load images, `.lines` files, or video, pick a style, export.

Built with CustomTkinter. Runs on macOS, Windows, and Linux wherever Tk is available.

## Install

```bash
pip install vexy-lines-run
```

Optional extras:

| Extra | What it adds |
|-------|-------------|
| `dnd` | Drag-and-drop file support (`tkinterdnd2`) |
| `video` | Video processing (PyAV, OpenCV, resvg, svglab) |
| `menus` | Native menu bar (`CTkMenuBarPlus`) |
| `all` | Everything above |

```bash
pip install "vexy-lines-run[all]"
```

## Launch

```bash
vexy-lines-gui
```

Or:

```bash
python -m vexy_lines_run
```

From Python:

```python
from vexy_lines_run import launch
launch()
```

## Features

**Three input tabs**

- **Lines** — load `.lines` files; export embedded previews or apply a new style
- **Images** — load PNG, JPG, WEBP, and other rasters; style applied via the MCP API
- **Video** — load MP4, MOV, MKV, or similar; per-frame style transfer with audio passthrough

**Style picker**

Select a primary style from any `.lines` file. Optionally select an end style — the two are interpolated linearly across the input sequence. Both show inline thumbnail previews.

**Export formats**

| Format | Notes |
|--------|-------|
| SVG | Vector output from the style engine |
| PNG / JPG | Raster, with optional 2× upscale |
| MP4 | Re-encoded video with styled frames, optional audio |
| LINES | Copy `.lines` files directly (Lines tab only) |

**Drag-and-drop** onto any input list (requires `[dnd]`)

**Background processing** — export runs on a daemon thread; the progress bar updates live and the UI stays responsive

## Architecture

```
app.py          App(CTk)         — window, three tabs, style pickers, export bar
processing.py   process_export() — background thread dispatcher for lines/images/video
video.py        probe()          — PyAV-based video metadata and per-frame processing
widgets.py      CTkRangeSlider   — dual-handle range slider for video frame selection
```

Style transfer calls into `vexy-lines-apy` (`MCPClient`, `apply_style`, `interpolate_style`). Video uses PyAV for mux/demux and OpenCV for frame extraction.

## Full documentation

[Read the docs](https://vexyart.github.io/vexy-lines/vexy-lines-run/) for the complete GUI guide, API reference, and more examples.

## License

MIT
