# vexy-lines-run

GUI desktop application for [Vexy Lines](https://vexy.art) style transfer.

Apply, preview, and export Vexy Lines fill styles across `.lines` files, raster images, and video -- all from a single desktop window.

## Installation

```bash
pip install vexy-lines-run
```

With all optional features (drag-and-drop, video processing, menus):

```bash
pip install vexy-lines-run[all]
```

Optional extras:

| Extra | What it adds |
|-------|-------------|
| `dnd` | Drag-and-drop file support (tkinterdnd2) |
| `video` | Video processing (PyAV, OpenCV, resvg, svglab) |
| `menus` | Native menu bar (CTkMenuBarPlus) |
| `all` | Everything above |

## Usage

```bash
vexy-lines-gui
```

Or from Python:

```python
from vexy_lines_run import launch
launch()
```

## Features

- **Three input modes** -- Lines, Images, and Video tabs for different workflows
- **Style picker** -- Browse and preview `.lines` style files with thumbnail extraction
- **End-style interpolation** -- Blend between two styles across a batch or video timeline
- **Export controls** -- SVG, PNG, JPG, MP4, and LINES output formats at 1x or 2x resolution
- **Drag-and-drop** -- Drop files directly onto the window (requires `tkinterdnd2`)
- **Video processing** -- Per-frame style transfer with audio passthrough (requires `[video]` extra)
- **Background processing** -- Exports run in a thread so the UI stays responsive

## Dependencies

- [vexy-lines-apy](../vexy-lines-apy) -- MCP client and style engine
- [vexy-lines-py](../vexy-lines-py) -- `.lines` file parser (transitive via vexy-lines-apy)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) -- Modern Tk UI toolkit
- [Pillow](https://python-pillow.org/) -- Image handling
- [loguru](https://github.com/Delgan/loguru) -- Logging

## License

MIT
