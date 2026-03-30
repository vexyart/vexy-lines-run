
[Vexy Lines for Mac & Windows](https://vexy.art/lines/) | [Download](https://www.vexy.art/lines/#buy) | [Buy](https://www.vexy.art/lines/#buy) | **Batch GUI** | [CLI/MCP](https://vexy.dev/vexy-lines-cli/) | [API](https://vexy.dev/vexy-lines-apy/) | [.lines format](https://vexy.dev/vexy-lines-py/)

[![Vexy Lines](https://i.vexy.art/vl/websiteart/vexy-lines-hero-poster.png)](https://www.vexy.art/lines/)

# vexy-lines-run

Desktop GUI for [Vexy Lines](https://vexy.art) style transfer.

Load images, `.lines` files, or video. Pick a style. Export. Built with CustomTkinter -- runs on macOS, Windows, and Linux wherever Tk is available.

## What it does

A three-tab desktop app that applies Vexy Lines artistic styles to any input:

- **Lines tab** -- load `.lines` files, export previews or apply a new style
- **Images tab** -- load PNG, JPG, WEBP rasters, style them via the MCP API
- **Video tab** -- load MP4, MOV, MKV, process frame-by-frame with style transfer and audio passthrough

Select a primary style from any `.lines` file. Optionally select an end style -- the two interpolate linearly across the input sequence for smooth transitions.

Export runs on a background thread. The progress bar updates live. The UI stays responsive.

## Quick start


## On macOS

Open Terminal app from /Applications/Utilities/ then paste this line and press Enter: 

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH="$HOME/.local/bin:$PATH" && uvx --python 3.12 vexy-lines-run
```

## On Windows

Open Command Prompt from Start menu, then paste this line and press Enter: 

```bat
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex; $env:Path = \"$HOME\.local\bin;$HOME\AppData\Roaming\uv;$env:Path\"; uvx --python 3.12 vexy-lines-run"
```

## From Python

```python
from vexy_lines_run import launch
launch()
```

## Next steps

- [Installation](installation.md) -- install options and optional extras
- [GUI Guide](gui-guide.md) -- walkthrough of every UI section
- [API Reference](api-reference.md) -- Python API for the app and processing modules
- [Examples](examples.md) -- usage patterns and workflows
