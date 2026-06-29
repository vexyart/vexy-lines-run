# Installation Troubleshooting

Platform-specific issues and fixes for `vexy-lines-run`.

---

## Windows

### tkinterdnd2 — drag-and-drop not working

`tkinterdnd2` ships a pre-built `tkdnd` Tcl extension inside the wheel.  On
Windows, the DLL must be on a path that Tcl can find.

**Symptom:** The app launches but dropping files onto the window does nothing,
or the title bar shows `tkdnd unavailable`.

**Fix 1 — reinstall with uv or pip:**

```bat
pip uninstall tkinterdnd2 -y
pip install tkinterdnd2
```

If you used a conda environment, make sure you installed `tkinterdnd2` from
PyPI, not from conda-forge (the conda package bundles a different Tcl layout).

**Fix 2 — run as a module rather than a script:**

Calling `python -m vexy_lines_run` instead of `vexy-lines-run` ensures that
the `tkinterdnd2` package root is on `sys.path` before `tkinter` initialises.

**Fix 3 — Tcl/Tk version mismatch:**

The bundled `tkdnd` DLL targets a specific Tcl version.  If your Python ships
with Tcl 8.6 but `tkinterdnd2` was built for Tcl 9, the extension cannot load.

Check your Tcl version:

```python
import tkinter
print(tkinter.TclVersion)
```

Then check the `tkinterdnd2` wheel name on PyPI — it encodes the Tcl target.
Install the matching version or upgrade Python to one that ships Tcl 9.

**Workaround:** The app works without drag-and-drop.  Use the **+** buttons or
the menu bar to add files.

---

### "No module named '_tkinter'" on Windows

This means Tk was not included in your Python installation.

**Fix:** Download and reinstall Python from [python.org](https://www.python.org/downloads/windows/).
During setup, make sure **tcl/tk and IDLE** is checked under Optional Features.

---

### The app window appears behind other windows

CustomTkinter calls `wm_attributes("-topmost", True)` briefly on startup to
bring the window to the front, then drops it back to normal z-order.  If the
window still appears behind, click the taskbar icon.

---

## macOS

### "Python framework" warning with CustomTkinter

On some macOS Python installs (especially `pyenv` or Homebrew Python), Tkinter
may fail with:

```
This program needs access to the screen. Please run with a Framework build
of python, and only when you are logged in on the main display of your Mac.
```

**Fix:** Use the python.org installer or the Homebrew cask
(`brew install --cask python`), which ships a proper macOS Framework build.

---

### Drag-and-drop works but paths contain spaces

tkinterdnd2 wraps paths with spaces in braces: `{/path/to/my file.png}`.
The app handles this automatically via the `_parse_drop_data` method.

---

## Linux

### Tk not available — "No module named '_tkinter'"

Most Linux distributions do not bundle Tk with the system Python.

```bash
# Debian / Ubuntu
sudo apt install python3-tk

# Fedora / RHEL
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

### Drag-and-drop not working

The underlying `tkdnd` Tcl extension may be missing on minimal installations
even when `tkinterdnd2` is installed.

```bash
# Debian / Ubuntu — install the system tkdnd package
sudo apt install tk-dnd

# Then reinstall tkinterdnd2 so it finds the system library
pip install --force-reinstall tkinterdnd2
```

If `tk-dnd` is unavailable for your distribution, the app still works using
the **+** buttons and menu bar — drag-and-drop is a convenience, not a
requirement.

### Running headless (no display server)

The GUI requires a display.  For CI or server environments, use Xvfb:

```bash
sudo apt install xvfb python3-tk
xvfb-run python -m vexy_lines_run
```

The test suite itself does not require a display — all GUI tests use mocks.
Only `tests/test_smoke_headless.py` tries to open a real Tk window and will
skip automatically if `$DISPLAY` is not set.

---

## Video processing

### ffmpeg not found

Audio passthrough requires `ffmpeg` on your PATH.  Without it, the audio
toggle is hidden and video exports are video-only.

```bash
# macOS
brew install ffmpeg

# Debian / Ubuntu
sudo apt install ffmpeg

# Windows — download from https://ffmpeg.org/download.html and add to PATH
```

### OpenCV fails to open a video file

Some container formats require additional codec support.  Try:

```bash
pip install opencv-python-headless --upgrade
```

If OpenCV still cannot open the file, convert it first with ffmpeg:

```bash
ffmpeg -i input.webm -c:v libx264 output.mp4
```

### "No module named 'cv2'"

OpenCV is pulled in transitively by `vexy-lines-apy`.  If it is missing from
your environment, install it explicitly:

```bash
pip install opencv-python-headless
# or, with the video extra:
pip install "vexy-lines-run[video]"
```

---

## General

### Import error: customtkinter not found

```bash
pip install customtkinter
```

### The app launches but style transfer does nothing

Style transfer requires the **Vexy Lines desktop app** running on your machine.
The GUI connects to it via a local MCP server on `localhost:47384`.

1. Launch the Vexy Lines app.
2. Wait a few seconds for its MCP server to start.
3. Try exporting again.

Check the log output (`--log-level DEBUG` is not a flag — use
`loguru` environment variable `LOGURU_LEVEL=DEBUG python -m vexy_lines_run`)
for connection errors.

### "MCP error: Connection refused"

Same as above — the Vexy Lines app is not running or has not finished starting.

### Reinstalling from scratch

```bash
pip uninstall vexy-lines-run vexy-lines-apy vexy-lines-py -y
pip install vexy-lines-run
```

With uv:

```bash
uv pip uninstall vexy-lines-run vexy-lines-apy vexy-lines-py
uv pip install vexy-lines-run
```
