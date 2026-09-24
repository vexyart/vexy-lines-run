# Video Processing

How `vexy-lines-run` handles video input and output.

## Supported containers

| Extension | Container | Notes |
|-----------|-----------|-------|
| `.mp4` | MPEG-4 / H.264 | Primary format; best compatibility |
| `.mov` | QuickTime | Common on macOS |
| `.mkv` | Matroska | Open container; widely supported |
| `.avi` | AVI | Legacy; no audio passthrough |
| `.webm` | WebM | VP8/VP9; no audio passthrough |

OpenCV (`opencv-python-headless`) handles frame extraction for all containers.
Output is always re-encoded MP4 (H.264 via OpenCV's VideoWriter) or individual
PNG/JPG frames. The app does not remux the original container.

## Per-frame pipeline

Each styled frame goes through this sequence:

```
OpenCV VideoCapture
    ↓  read raw BGR frame (numpy ndarray, shape H×W×3)
cv2.imencode(".png")
    ↓  PNG bytes in memory  (~1–3 MB for 1080p, versus ~6 MB uncompressed)
PIL Image.open(BytesIO(...))
    ↓  PIL Image in RGB
MCP apply_style(png_bytes)  →  SVG string
    ↓  (round-trip to Vexy Lines desktop app on localhost:47384)
svg_to_pil(svg, width, height)
    ↓  PIL Image in RGBA  (rasterised by resvg-py or Pillow fallback)
PIL Image.convert("RGB") → numpy array
    ↓
cv2 VideoWriter.write(frame)   [MP4 output]
    — or —
PIL Image.save(path)           [PNG/JPG frame output]
```

### Memory behaviour

Frames are kept as in-memory PNG bytes while waiting for the MCP round-trip,
not as raw numpy arrays.  For a 1080p frame this is roughly 1–3 MB compressed
versus 6 MB uncompressed.  Only one frame is in the pipeline at a time; the
app does not buffer frames ahead.

For a 5-second clip at 30 fps (150 frames), peak RAM usage is dominated by the
single in-flight PNG plus the SVG string returned by the engine.  Long clips do
not accumulate in memory.

### Job folder (crash-safe exports)

Every export creates a persistent job folder alongside the output file.
Intermediate artifacts (`.lines` documents, `.svg` exports, individual PNG
frames) are written there.  If the export is interrupted, re-running it resumes
from the last completed frame rather than starting over.

The GUI never deletes job folders automatically.  To start fresh, delete the
`<output-stem>--job/` folder manually, or use the CLI with `--force`.

## Audio passthrough

The audio toggle (♪) appears only when **all** of these are true:

1. The loaded video has an audio stream (detected via `ffprobe`).
2. Export format is MP4.
3. The full frame range is selected (first frame to last).
4. You are on the Video tab.

When audio passthrough is on, the app:

1. Writes the styled video (video-only, no audio) to a temp file.
2. Runs `ffmpeg -i <styled.mp4> -i <original.mp4> -c:v copy -c:a aac <output.mp4>` to merge the audio track.
3. Deletes the temp file.

**Why the full-range restriction?**  If you export only frames 10–50 of a
60-frame clip, the audio and video would be out of sync.  For partial ranges
the audio toggle is hidden and audio is silently dropped.

**ffmpeg must be on your PATH.**  The app uses `shutil.which("ffmpeg")` to find
it.  Without ffmpeg, audio passthrough is disabled regardless of the toggle
state.

## SVG rasterisation

After the Vexy Lines engine returns an SVG string, it must be rasterised for
raster outputs (PNG, JPG, MP4 frames).  The app tries these in order:

1. **resvg-py** (`resvg.svg_to_png`): fast, correct, preferred.
2. **Pillow fallback**: returns a blank RGBA image of the correct size.  Used
   when `resvg` is not installed.  The resulting frame will be blank but the
   export will not fail.

Install `resvg-py` to get proper rasterisation:

```bash
pip install resvg-py
# or, with uv:
uv add resvg-py
```

## Video probe

`probe(path)` uses `cv2.VideoCapture` to read:

- `width`, `height`: frame dimensions in pixels.
- `fps`: frames per second (`CAP_PROP_FPS`).
- `total_frames`: frame count (`CAP_PROP_FRAME_COUNT`).
- `duration`: `total_frames / fps`.
- `has_audio`: detected separately via `ffprobe` (returns `False` if ffprobe is
  unavailable).

`probe` opens the file only to read properties and closes it immediately.  It
does not decode any frames.

## Frame range semantics

Frame numbers in the GUI are **1-indexed** (first frame = 1, last frame =
`total_frames`).  Internally, the export pipeline converts to **0-indexed**
ranges before passing them to the frame extractor.  The UI-to-internal
conversion is `(ui_start - 1, ui_end - 1)`.

## Optional `video` extra

The video dependencies (`opencv-python-headless`, `av`) are pulled in
transitively by `vexy-lines-apy` for most installs.  If your environment strips
transitive extras or you need to pin versions explicitly, install them directly:

```bash
pip install "vexy-lines-run[video]"
```
