# Installation

## Requirements

- Python 3.11 or newer
- Tk/Tcl (ships with most Python installs; on Linux, install `python3-tk`)
- The [Vexy Lines](https://vexy.art) desktop app for style transfer via MCP

## Install from PyPI

```bash
pip install vexy-lines-run
```

Or with `uv`:

```bash
uv add vexy-lines-run
```

## Optional extras

| Extra | What it adds | Install |
|-------|-------------|---------|
| `dnd` | Drag-and-drop file support | `pip install "vexy-lines-run[dnd]"` |
| `video` | Video processing (PyAV, OpenCV, resvg, svglab) | `pip install "vexy-lines-run[video]"` |
| `menus` | Native menu bar | `pip install "vexy-lines-run[menus]"` |
| `all` | Everything above | `pip install "vexy-lines-run[all]"` |

## Runtime dependencies

| Package | Why |
|---------|-----|
| `vexy-lines-apy` | MCP client and style engine |
| `customtkinter` | Modern-looking Tk widgets |
| `Pillow` | Image loading and thumbnail generation |
| `loguru` | Structured debug logging |

## Launch

Three ways to start the GUI:

```bash
# Installed script
vexy-lines-gui

# Module entry point
python -m vexy_lines_run

# From Python
from vexy_lines_run import launch
launch()
```

## Verify the install

```bash
vexy-lines-gui --help
```

Or:

```python
from vexy_lines_run import App
print("vexy-lines-run is ready")
```

## Platform notes

**macOS**: Works out of the box. Drag-and-drop requires the `[dnd]` extra.

**Windows**: Works out of the box. Drag-and-drop requires the `[dnd]` extra.

**Linux**: Install `python3-tk` from your package manager if Tk is not bundled with your Python install. Drag-and-drop requires `[dnd]` plus `tkdnd` system library.

## Development install

```bash
git clone https://github.com/vexyart/vexy-lines.git
cd vexy-lines/vexy-lines-run
uv venv --python 3.12
uv pip install -e ".[all,dev]"
```

Run tests:

```bash
uvx hatch test
```
