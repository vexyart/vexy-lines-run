# Examples

## Launch

```bash
vexy-lines-gui
```

Or from Python:

```python
from vexy_lines_run import launch
launch()
```

Or as a module:

```bash
python -m vexy_lines_run
```

## Style transfer on a batch of photos

You have 20 portrait photos. You want them all rendered as halftone vector art.

![Images tab with bear photos and a halftone cat style loaded](images/images-mode.png)

1. Switch to the **Images** tab
2. Click **Add Images...** and select all 20 photos (PNG, JPG, WEBP — any raster format works)
3. Click **Open Lines...** in the Style panel and pick a `.lines` file with the halftone look you want
4. The style preview appears immediately — check it's the right one
5. Choose **SVG** for vector output, or **PNG**/**JPG** with a size multiplier (2x doubles the resolution)
6. Click **Export ▶** and choose an output folder
7. The progress bar fills as each photo is processed: "Stop ■ (7/20)"
8. Done. Twenty styled images in the output folder, named after the originals

If one photo fails (corrupt file, MCP timeout), the app logs a warning and moves on. The other 19 still export.

## Re-export .lines files with a different style

You have a collection of `.lines` documents and want to apply a completely different artistic style to all of them.

![Lines tab with nine .lines files loaded](images/lines-mode.png)

1. Switch to the **Lines** tab
2. Drag your `.lines` files onto the file list (or use **Add Lines...**)
3. In the Style panel, load the new style you want to apply
4. Pick your output format — SVG for vectors, PNG/JPG for rasters
5. Click **Export ▶**

Each file's embedded source image gets restyled with the new fill structure. The original `.lines` files are untouched.

**Without a style selected**, export works differently: the app opens each `.lines` file in Vexy Lines via MCP, renders it with its own fills, and exports the result. This is useful for batch-converting `.lines` files to SVG/PNG/JPG.

**With format set to LINES**, files are simply copied to the output folder. No MCP, no rendering — just a file copy.

## Style interpolation across a sequence

Load 60 frames from an animation. Set a "clean lines" primary style and a "chaotic scribble" end style. Frame 1 gets pure clean lines, frame 60 gets pure scribble, and everything in between blends proportionally.

1. Load your frames in the **Images** tab (JPGs named `frame_001.jpg` through `frame_060.jpg`)
2. Click **Open Lines...** and pick the clean lines style
3. Switch to the **End Style** tab and pick the scribble style
4. Export as PNG at 2x

The blend factor `t` for frame `i` of `N` total frames is `i / (N - 1)`. Both styles must be structurally compatible — same number of groups, layers, and fills with matching fill types.

## Video processing

Turn a 5-second bear clip into vector art, frame by frame.

![Video tab showing first and last frames of a bear video, with a range slider set to 5 frames](images/video-mode.png)

1. Install the video extra: `pip install "vexy-lines-run[video]"`
2. Switch to the **Video** tab
3. Click **Open Video...** and load `bear.mp4`
4. The first and last frames appear as previews. The range slider shows 1 to total frames.
5. Narrow the range with the slider handles or type exact frame numbers in the entry fields
6. Load a style in the Style panel
7. Choose output format:
   - **MP4** — re-encoded video with styled frames. Audio toggle appears if the source has audio and the full range is selected.
   - **PNG** or **JPG** — exports individual frame images named `frame_000001.png`, `frame_000002.png`, etc.
8. Click **Export ▶**

For MP4, you pick a save filename. For image frames, you pick a folder.

### Frame range tips

- The range is 1-indexed (first frame is 1, not 0)
- Slider handles and text entries stay in sync — change either one
- The "frames" label between them shows the count (e.g. "5 frames")
- Previews update when you change the range, showing the actual first and last frames
- Audio passthrough only works with full-range MP4 — partial ranges drop audio to avoid timing mismatch

## Drag-and-drop workflow

With the `[dnd]` extra installed, you can skip file dialogs entirely:

```bash
pip install "vexy-lines-run[dnd]"
```

- Drag `.lines` files onto the **Lines** tab list or preview area
- Drag photos onto the **Images** tab list or preview area
- Drag a video onto the **Video** tab preview areas or path label
- Drag a `.lines` file onto the **Style** panel to load it as primary style
- Drag a `.lines` file onto the **End Style** panel to load it as end style

The app filters by extension. Dropping a PNG on the Lines tab does nothing. Dropping a duplicate file is silently ignored.

## Probe video metadata from Python

```python
from vexy_lines_run.video import probe

info = probe("clip.mp4")
print(f"Resolution: {info.width}x{info.height}")
print(f"FPS:        {info.fps}")
print(f"Frames:     {info.total_frames}")
print(f"Duration:   {info.duration:.1f}s")
print(f"Audio:      {'yes' if info.has_audio else 'no'}")
```

`probe()` reads metadata without decoding frames — it returns instantly even for large files.

## Use the range slider widget standalone

The dual-handle range slider is a reusable CustomTkinter widget. Use it in your own apps:

```python
import customtkinter as ctk
from vexy_lines_run.widgets import CTkRangeSlider

root = ctk.CTk()
root.geometry("400x100")

def on_change(low, high):
    print(f"Range: {low:.0f} – {high:.0f}")

slider = CTkRangeSlider(
    root,
    from_=0,
    to=300,
    number_of_steps=300,  # integer steps
    command=on_change,
)
slider.pack(padx=20, pady=20, fill="x")

root.mainloop()
```

The slider supports horizontal and vertical orientations, variable binding (`tk.IntVar` / `tk.DoubleVar`), step quantization, hover highlighting, and full CustomTkinter theming (dark/light mode, custom colors).

## Run the processing pipeline from Python

For scripting or automation, call the processing module directly:

```python
import threading
from vexy_lines_run.processing import process_export

def on_progress(current, total, message):
    print(f"[{current}/{total}] {message}")

def on_complete(message):
    print(f"Done: {message}")

def on_error(message):
    print(f"Error: {message}")

process_export(
    mode="images",
    input_paths=["photo1.jpg", "photo2.jpg", "photo3.jpg"],
    style_path="halftone.lines",
    end_style_path=None,
    output_path="./output",
    fmt="SVG",
    size="1x",
    on_progress=on_progress,
    on_complete=on_complete,
    on_error=on_error,
)
```

This runs synchronously on the calling thread. To run in the background (like the GUI does), wrap it in a `threading.Thread`:

```python
abort = threading.Event()
thread = threading.Thread(
    target=process_export,
    kwargs={
        "mode": "images",
        "input_paths": ["photo1.jpg"],
        "style_path": "style.lines",
        "end_style_path": None,
        "output_path": "./output",
        "fmt": "PNG",
        "size": "2x",
        "abort_event": abort,
        "on_progress": on_progress,
        "on_complete": on_complete,
        "on_error": on_error,
    },
    daemon=True,
)
thread.start()

# To cancel:
abort.set()
```
