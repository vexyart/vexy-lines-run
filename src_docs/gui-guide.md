# GUI Guide

The Vexy Lines GUI is a CustomTkinter desktop app with three sections: input selection, style pickers, and export controls.

## Layout

```
+-------------------------------------------+
|  Tab: Lines | Images | Video              |  <- input file selection
+-------------------------------------------+
|  Style picker  |  End Style (optional)    |  <- .lines style files
+-------------------------------------------+
|  Format  Size  Audio  [Export]  ░░░░░░░   |  <- export controls + progress
+-------------------------------------------+
```

## Input tabs

### Lines tab

Load one or more `.lines` files. Each file appears in a scrollable list showing its filename. Use the "Add Files" button or drag-and-drop (requires `[dnd]` extra).

When you export from this tab:

- If a style is selected, the style's fill structure is applied to each file's source image
- If no style is selected, the embedded preview image is extracted directly

### Images tab

Load raster images: PNG, JPG, JPEG, WEBP, BMP, TIFF, and others supported by Pillow.

A style must be selected. Each image is opened as a new document in Vexy Lines via MCP, the style's fill tree is replicated, the document is rendered, and the result is exported.

### Video tab

Load video files: MP4, MOV, MKV, AVI, and others supported by PyAV.

Requires the `[video]` extra. Style transfer runs per-frame: each frame is decoded, styled via MCP, and re-encoded. Audio is passed through when available.

The dual-handle range slider lets you select a frame range (start/end) instead of processing the entire video.

## Style pickers

### Primary style

Click "Select Style" to choose a `.lines` file. The picker shows an inline thumbnail preview extracted from the file's embedded preview image.

The primary style defines the fill structure applied to every input.

### End style (optional)

Click "Select End Style" for a second `.lines` file. When set, the two styles are interpolated linearly across the input sequence:

- First input gets 100% primary style
- Last input gets 100% end style
- Inputs in between are blended proportionally

Both styles must have compatible structures (same groups, layers, fills, fill types). The app checks compatibility and warns if they don't match.

## Export controls

### Format selector

| Format | Notes |
|--------|-------|
| SVG | Vector output from the style engine |
| PNG | Raster with optional 2x upscale |
| JPG | Raster with optional 2x upscale |
| MP4 | Re-encoded video (Video tab only) |
| LINES | Copy `.lines` files directly (Lines tab only) |

### Size options

For raster and video exports, choose the output resolution. The "2x" option doubles the dimensions for higher-quality output.

### Audio passthrough

For video exports, toggle whether to copy the audio track from the input video to the output.

### Export button

Starts the export. Processing runs on a daemon thread -- the UI stays responsive. The progress bar shows completion percentage. Cancel at any time.

### Progress feedback

Three callbacks drive the UI:

- `on_progress(current, total)` -- updates the progress bar
- `on_complete(results)` -- shows a completion dialog with file counts
- `on_error(message)` -- shows an error dialog

All callbacks are marshalled to the Tk main thread via `self.after(0, ...)`.

## Drag-and-drop

With the `[dnd]` extra installed, drop files directly onto any input list. The app accepts `.lines` files (Lines tab), image files (Images tab), and video files (Video tab) based on the active tab.

## Dark/light mode

CustomTkinter follows the system appearance by default. The app uses the `slate` dark theme and `deep purple` accent colour.

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| Cmd/Ctrl+O | Open file dialog for the active tab |
| Cmd/Ctrl+E | Start export |
| Escape | Cancel running export |
