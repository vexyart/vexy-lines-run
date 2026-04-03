# Installation

## What you need

- **Python 3.11+** (3.12 recommended)
- **Tk/Tcl** — ships with most Python installs. On Linux, install `python3-tk` from your package manager.
- **[Vexy Lines](https://vexy.art)** desktop app — the style engine runs as an MCP server inside the app on `localhost:47384`. Without it, the GUI launches but can only extract previews from `.lines` files and copy `.lines` files. Anything involving style transfer requires the app running.

## Quick start

### macOS

Open Terminal, paste, press Enter:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh && "$HOME/.local/bin/uvx" --python 3.12 vexy-lines-run@latest
```

### Windows

Open Command Prompt, paste, press Enter:

```bat
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex; $env:Path = \"$HOME\.local\bin;$HOME\AppData\Roaming\uv;$env:Path\"; uvx --python 3.12 vexy-lines-run@latest"
```

These one-liners install [uv](https://docs.astral.sh/uv/) (a fast Python package manager) and run vexy-lines-run in an isolated environment. Nothing is permanently installed on your system — `uvx` manages it.

## Install with pip

```bash
pip install vexy-lines-run
```

With uv (faster):

```bash
uv add vexy-lines-run
```

## What's included

The base install includes all functionality — video processing, drag-and-drop, and native menus. No optional extras or feature flags needed.

## Runtime dependencies

These install automatically with the package:

| Package | Purpose |
|---------|---------|
| `vexy-lines-apy` | MCP client and style engine bindings |
| `vexy-lines-py` | `.lines` file parser (transitive, via vexy-lines-apy) |
| `customtkinter` | Modern Tk widgets with dark mode |
| `CTkMenuBarPlus` | Enhanced menu bar with cascading dropdown menus |
| `Pillow` | Image loading, thumbnails, format conversion |
| `loguru` | Debug logging (not shown to users) |
| `tkinterdnd2` | Drag-and-drop file support |
| `opencv-python-headless` | Video frame reading and writing |
| `svglab` or `resvg-py` | SVG-to-raster conversion for video/image export |

## System dependencies for video

Video processing also depends on system binaries (not Python packages):

| Binary | Required for | How to install |
|--------|-------------|----------------|
| `ffmpeg` | Audio merging in MP4 exports | `brew install ffmpeg` (macOS), `apt install ffmpeg` (Debian/Ubuntu), [ffmpeg.org](https://ffmpeg.org/download.html) (Windows) |
| `ffprobe` | Audio stream detection | Ships with ffmpeg |

Without ffmpeg, video export still works — you just won't get audio passthrough.

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

All three do the same thing: create an `App` instance in dark mode and call `mainloop()`.

## Verify

From Python:

```python
from vexy_lines_run import App
print("vexy-lines-run is ready")
```

## Platform notes

### macOS

Works out of the box. Tk ships with the Python.org and Homebrew installers.

### Windows

Works out of the box. Tk ships with the python.org installer.

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

Drag-and-drop depends on the Tcl/Tk DnD extension. On some minimal Linux installs, the underlying `tkdnd` library may be missing even if `tkinterdnd2` is installed. The app works without it — you just use the buttons and menus instead.

## Development install

```bash
git clone https://github.com/vexyart/vexy-lines.git
cd vexy-lines/vexy-lines-run
uv venv --python 3.12
uv pip install -e ".[dev]"
```

Run tests:

```bash
uvx hatch test
```

The test suite mocks the MCP client and macOS APIs, so tests run on any platform — no Vexy Lines app needed.
