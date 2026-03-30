# Installation

## What you need

- **Python 3.11+** (3.12 recommended)
- **Tk/Tcl** — ships with most Python installs. On Linux, install `python3-tk` from your package manager.
- **[Vexy Lines](https://vexy.art)** desktop app — the style engine runs as an MCP server inside the app on `localhost:47384`. Without it, the GUI launches but can't export anything that requires style transfer.

## Install

```bash
pip install vexy-lines-run
```

With uv (faster):

```bash
uv add vexy-lines-run
```

## Optional extras

The base install handles `.lines` files and images. Extras unlock more:

| Extra | What it adds | Install |
|-------|-------------|---------|
| `dnd` | Drag-and-drop files onto the app | `pip install "vexy-lines-run[dnd]"` |
| `video` | Video processing — PyAV, OpenCV, resvg, svglab | `pip install "vexy-lines-run[video]"` |
| `menus` | Native menu bar (CTkMenuBarPlus) | `pip install "vexy-lines-run[menus]"` |
| `all` | Everything above | `pip install "vexy-lines-run[all]"` |

Without `[dnd]`, you use file dialogs instead of drag-and-drop. Without `[video]`, the Video tab still appears but can't load anything. Without `[menus]`, you use the in-panel buttons — nothing is lost, just a different workflow.

## Runtime dependencies

These install automatically with the base package:

| Package | Purpose |
|---------|---------|
| `vexy-lines-apy` | MCP client and style engine bindings |
| `customtkinter` | Modern Tk widgets with dark mode |
| `Pillow` | Image loading, thumbnails, format conversion |
| `loguru` | Debug logging (not shown to users) |

## Launch

Three ways:

```bash
# Installed console script
vexy-lines-run

# Module entry point
python -m vexy_lines_run
```

```python
# From Python
from vexy_lines_run import launch
launch()
```

All three do the same thing: create an `App` instance and call `mainloop()`.

## Verify

```bash
vexy-lines-run --help
```

Or from Python:

```python
from vexy_lines_run import App
print("vexy-lines-run is ready")
```

## Platform notes

### macOS

Works out of the box. Tk ships with the Python.org and Homebrew installers. Drag-and-drop requires the `[dnd]` extra.

### Windows

Works out of the box. Tk ships with the python.org installer. Drag-and-drop requires the `[dnd]` extra.

### Linux

Tk might not be bundled with your system Python. Install it:

```bash
# Debian/Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

Drag-and-drop requires `[dnd]` **plus** the `tkdnd` system library (`sudo apt install tkdnd` on Debian/Ubuntu).

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

The test suite mocks the MCP client and macOS APIs, so tests run on any platform — no Vexy Lines app needed.
