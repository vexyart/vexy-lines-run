# vexy-lines-run

Desktop GUI for [Vexy Lines](https://vexy.art) style transfer — load images, `.lines` files, or video, pick a style, export.

Built with CustomTkinter. Runs on macOS, Windows, and Linux wherever Tk is available.

## Install

```bash
pip install vexy-lines-run
```

All dependencies (CustomTkinter, tkinterdnd2, PyAV, OpenCV, resvg, svglab, CTkMenuBarPlus) are installed automatically.

## Launch

```bash
vexy-lines-run
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
Matching image-filter chains on fills are preserved and interpolated as part of the style.

**AI Rename Layers & Fills**

*Lines ▸ AI Rename Layers & Fills…* renames a `.lines` document's generic
captions (`Layer`, `Blended`, `Linear`) to describe what each
[fill](https://help.vexy.art/lines/articles/fill-properties-1/) actually draws,
then names each [layer](https://help.vexy.art/lines/articles/layers-panel/) from
its fills — only the captions change. After a confirmation and a Save dialog,
each fill is rendered in Vexy Lines and described by a vision model on a
background thread (progress shows in the title bar); the renamed copy defaults to
`<stem>-renamed.lines`. Needs the `[ai]` extra (`pip install "vexy-lines-run[ai]"`),
the Vexy Lines app, and an OpenAI-compatible `/v1` LLM endpoint — set it in
**Lines ▸ AI Rename Settings…** or via `VEXY_LINES_LLM_API_URL`,
`VEXY_LINES_LLM_API_KEY`, `VEXY_LINES_LLM_MODEL_VISION`, and `VEXY_LINES_VLM_MODEL`.
See the [full guide](https://vexyart.github.io/vexy-lines/vexy-lines-apy/ai-rename/).

**Export formats**

| Format | Notes |
|--------|-------|
| SVG | Vector output from the style engine |
| PNG / JPG | Raster, with optional 2× upscale |
| MP4 | Re-encoded video with styled frames, optional audio |
| LINES | Copy `.lines` files directly (Lines tab only) |

**Drag-and-drop** onto any input list (via `tkinterdnd2`)

**Background processing** — export runs on a daemon thread; the progress bar updates live and the UI stays responsive

## Architecture

```
app.py          App(CTk)         — window, three tabs, style pickers, export bar
processing.py   process_export() — background thread dispatcher for lines/images/video
video.py        probe()          — PyAV-based video metadata and per-frame processing
widgets.py      CTkRangeSlider   — dual-handle range slider for video frame selection
```

Style transfer calls into `vexy-lines-apy` (`MCPClient`, `apply_style`, `interpolate_style`). Video uses PyAV for mux/demux and OpenCV for frame extraction.

## Job folders (crash-safe exports)

All exports create a persistent **job folder** alongside the output directory. Every intermediate artifact — `.lines` documents, `.svg` exports, rasterized frames — is saved there. If the app quits or the process is interrupted mid-export, re-running the export resumes from where it left off.

The GUI never deletes job folders automatically. Use the CLI with `--force` to start fresh or `--cleanup` to remove the folder after completion.

## Full documentation

[Read the docs](https://vexyart.github.io/vexy-lines/vexy-lines-run/) for the complete GUI guide, API reference, and more examples.

## License

MIT
