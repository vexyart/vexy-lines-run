# Examples

## Launch the GUI

From the terminal:

```bash
vexy-lines-gui
```

From Python:

```python
from vexy_lines_run import launch
launch()
```

As a module:

```bash
python -m vexy_lines_run
```

## Typical workflow: style transfer on images

1. Launch the GUI
2. Switch to the **Images** tab
3. Click "Add Files" and select your photos
4. Click "Select Style" and pick a `.lines` file
5. Choose output format (SVG, PNG, or JPG)
6. Click "Export"
7. Watch the progress bar -- the UI stays responsive

## Style interpolation across a sequence

1. Load a sequence of images (e.g. video frames exported as JPGs)
2. Select a primary style (the starting look)
3. Select an end style (the finishing look)
4. Export -- the first image gets 100% primary, the last gets 100% end, everything in between blends smoothly

## Video processing

1. Install the video extra: `pip install "vexy-lines-run[video]"`
2. Switch to the **Video** tab
3. Load a video file
4. Select a style
5. Optionally set start/end frame range with the dual-handle slider
6. Toggle audio passthrough
7. Click "Export" -- each frame is decoded, styled, and re-encoded

## Probe video metadata

```python
from vexy_lines_run.video import probe

info = probe("clip.mp4")
print(f"Resolution: {info.width}x{info.height}")
print(f"FPS: {info.fps}")
print(f"Frames: {info.total_frames}")
print(f"Duration: {info.duration:.1f}s")
print(f"Audio: {'yes' if info.has_audio else 'no'}")
```

## Drag-and-drop

Install the `[dnd]` extra:

```bash
pip install "vexy-lines-run[dnd]"
```

Now drop files directly onto the input list in any tab. The app filters by file type based on the active tab.

## Use the range slider widget standalone

```python
import customtkinter as ctk
from vexy_lines_run.widgets import CTkRangeSlider

root = ctk.CTk()
root.geometry("400x100")

def on_range_change(low, high):
    print(f"Selected range: {low:.0f} - {high:.0f}")

slider = CTkRangeSlider(root, from_=0, to=300, command=on_range_change)
slider.pack(padx=20, pady=20, fill="x")

root.mainloop()
```
