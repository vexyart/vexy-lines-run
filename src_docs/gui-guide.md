# GUI Guide

Three tabs on the left. Style picker on the right. Export controls at the bottom. That's the whole app.

![The app window showing the Lines tab with files loaded and a lettering preview](images/lines-mode.png)

## Layout

```
+--------------------------------------+-----------------+
|                                      |                 |
|  Tab: Lines | Images | Video         |  Style          |
|                                      |  End Style      |
|  [file list]       [preview]         |  [preview]      |
|                                      |                 |
+--------------------------------------+-----------------+
|  Export as [Format ▾]  [Size ▾]  Audio ○  ░░░  [Export ▶] |
+-----------------------------------------------------------+
```

The left panel takes roughly two-thirds of the window. The right panel holds your style. The bottom strip handles export.

The window title reads "Vexy Lines Run". Default size is 1024x768, minimum 960x480. Resize freely — previews, file lists, and path labels adapt automatically.

## Menu bar

Six menus sit at the top: **File**, **Lines**, **Image**, **Video**, **Style**, **Export**.

| Menu | Key items |
|------|-----------|
| **File** | Add Lines, Export, Stop, Quit (Cmd/Ctrl+Q) |
| **Lines** | Add, Remove Selected, Remove All |
| **Image** | Add, Remove Selected, Remove All |
| **Video** | Add, Reset Range, Remove |
| **Style** | Open Style, Open End Style, Reset Styles |
| **Export** | Export, Stop, Location, Format submenu, Size submenu, Audio toggle |

The menu bar is included in the base install — you can use menus or buttons interchangeably.

## Lines tab

Load `.lines` files — the native Vexy Lines document format.

![Lines tab: nine files listed on the left, a purple-and-teal "Vexy Lines" lettering preview on the right](images/lines-mode.png)

The left half is a scrollable file list. Click a filename to select it (highlights in blue). The right half shows a preview image extracted from the selected file's embedded data.

**Buttons along the bottom:**

| Button | What it does |
|--------|-------------|
| **Add Lines...** | Opens a file dialog filtered to `*.lines` |
| **−** | Removes the selected file from the list |
| **✕** | Clears the entire list |

**What happens on export:**

| Condition | Behavior |
|-----------|----------|
| Style selected | The style's fill structure is applied to each file's source image via MCP |
| No style selected | The file is opened in Vexy Lines via MCP, rendered, and exported directly |
| Format = LINES | Plain file copy — no MCP, no rendering |

When no files are loaded, the list area shows a "Drop lines here" placeholder.

## Images tab

Load raster images and turn them into vector art.

![Images tab: eight bear photos listed, a teddy bear preview in the center, and a halftone cat style loaded on the right](images/images-mode.png)

Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP — anything Pillow can open.

A style **must** be selected for image export. Without one, there's nothing to apply. Each image gets opened as a new document in Vexy Lines through the MCP API, the style's fill tree is replicated onto it, the document renders, and the result exports.

The screenshot above shows eight bear photos loaded with a halftone cat style (`kitty.lines`) ready to apply. The preview shows the currently selected photo; the style panel shows what the fill pattern looks like.

**Buttons:** Same as the Lines tab — Add Images, remove selected (−), clear all (✕).

If style application fails for a particular image (MCP timeout, connection error), the app logs a warning and continues to the next file rather than aborting the entire batch.

## Video tab

Process video frame-by-frame with style transfer.

![Video tab: first and last frames of a teddy bear video side by side, a range slider set to frames 1–5, and a halftone cat style loaded](images/video-mode.png)

Requires `vexy-lines-run` (video dependencies are included). Supported formats: MP4, MOV, MKV, AVI, WEBM.

Two preview panes sit side by side — the first and last frames of your selected range. Below them:

| Control | What it does |
|---------|-------------|
| **Start entry** | Type an exact start frame number (1-indexed) |
| **Range slider** | Drag the two handles to set start and end frames |
| **Frame count** | Shows how many frames are in the selected range (e.g. "5 frames") |
| **End entry** | Type an exact end frame number |
| **Open Video...** | File dialog for video files |
| **Path label** | Shows the loaded video's path (truncated to fit) |
| **✕** | Removes the loaded video |

The range slider and text entries stay in sync — change one, the other updates. Values are clamped to valid bounds (1 to total frames). The previews update when the range changes, extracting the actual frames via OpenCV.

**Audio passthrough** appears as a toggle switch only when all four conditions are met:

1. A video with an audio track is loaded
2. Format is MP4
3. The full frame range is selected (first frame to last)
4. You're on the Video tab

Why the full-range restriction? Re-encoding a frame subset with the original audio would produce mismatched timing. For partial ranges, the audio is silently dropped.

## Style picker

The right panel has two tabs: **Style** and **End Style**.

Click **Open Lines...** to choose a `.lines` file. A thumbnail preview extracted from the file appears immediately. The file path displays below, truncated from the left with "..." if it's too long for the panel width.

Click **✕** to clear the style and return to the "Drop lines here" placeholder.

### How styles work

A `.lines` file contains a tree of groups, layers, and fills — each fill is an algorithm (linear, halftone, scribble, spiral, etc.) with numeric parameters. When you apply a style, the app replicates that entire fill tree onto your input image through the MCP API. The Vexy Lines engine then renders each fill algorithm against the image's pixel data.

### End style and interpolation

Select a second `.lines` file to enable style interpolation across a batch:

| Position in sequence | Style blend |
|---------------------|-------------|
| First input | 100% primary style |
| Middle inputs | Proportional blend |
| Last input | 100% end style |

Both styles must be structurally compatible — same number of groups, layers, and fills, with matching fill types. If they don't match, `styles_compatible()` returns false and the interpolation won't apply.

This is useful for animated sequences: load 100 frames, set a "clean lines" start style and a "chaotic scribble" end style, and watch the artwork gradually transform.

### Style panel and the Lines tab

When the Lines tab is active, the style panel is disabled (grayed out). Lines files carry their own fill structure — selecting an external style would override it. Switch to Images or Video to enable the style picker.

## Export controls

The bottom strip of the window:

```
Export as [SVG ▾]  [— ▾]  ○ Audio   ░░░░░░░░░░   [Export ▶]
```

### Format

| Format | Available on | Notes |
|--------|-------------|-------|
| **SVG** | Lines, Images | Vector output — no size scaling needed |
| **PNG** | Lines, Images, Video | Raster, supports 1x–4x upscale |
| **JPG** | Lines, Images, Video | Raster, supports 1x–4x upscale |
| **MP4** | Video only | Re-encoded video with styled frames |
| **LINES** | Lines only | Direct file copy, no processing |

The format dropdown updates its options when you switch tabs. If your current format isn't available on the new tab, it resets to the first option.

### Size

Choose output scaling: **1x**, **2x**, **3x**, or **4x**. The multiplier applies to raster and video exports. For 2x, a 1000x800 source produces a 2000x1600 output using Lanczos resampling.

Disabled (shows "—") for SVG and LINES formats — vector output has no fixed resolution, and LINES is a file copy.

### Export button

Click **Export ▶** to start. A dialog appears:

- **MP4 format:** Save-file dialog — choose a filename and location
- **All other formats:** Folder dialog — files are named automatically based on the input filenames

The button turns red and reads **Stop ■ (3/10)** during export, showing a running file count. The progress bar fills proportionally. Click Stop to cancel — the current file finishes, then the export halts. The button briefly shows "Stopping..." while the worker thread winds down.

On completion, the button returns to green **Export ▶** and the progress bar disappears.

### Crash-safe exports (job folders)

Every export creates a persistent job folder alongside the output directory. Intermediate artifacts — `.lines` documents, `.svg` exports, rasterized frames — accumulate there as the export progresses. If the app quits mid-export, re-running the same export picks up from where it left off rather than starting over. The GUI never deletes job folders automatically; use the CLI `--cleanup` flag if you want them removed after a successful run.

### Error handling

If an export fails, a dialog pops up with the error message. Common causes:

- Vexy Lines app not running (MCP connection refused)
- Style file deleted or moved since it was selected
- Output directory not writable
- Video codec not available

User-initiated cancellation ("Export aborted by user") does not show an error dialog — it resets silently.

For batch exports (multiple images), a single file failure logs a warning and continues. The export doesn't abort over one bad apple.

## Drag-and-drop

Drag-and-drop is included in the base install. Drop files directly onto the app:

| Drop target | Accepts |
|-------------|---------|
| Lines file list or preview | `.lines` files |
| Images file list or preview | Image files (PNG, JPG, etc.) |
| Video preview areas or path label | Video files |
| Style preview or path label | `.lines` files (loads as style) |
| End Style preview or path label | `.lines` files (loads as end style) |

The app filters by extension based on the drop target. Drop a PNG on the Lines list and nothing happens — no error, just no action.

Paths with spaces or special characters work correctly. The app handles both brace-enclosed (`{/path/to/my file.png}`) and space-separated drop data from tkinterdnd2.

Duplicate files are silently ignored — drop the same image twice and it only appears once in the list.

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| **Cmd/Ctrl+O** | Open file dialog for the active tab |
| **Cmd/Ctrl+E** | Start export |
| **Escape** | Cancel a running export |
| **Cmd/Ctrl+Q** | Quit the app |

## Appearance

CustomTkinter follows your system's dark/light mode. The app uses a dark slate theme with deep purple accents. Selected files highlight in blue. The export button is green (#2E7D32) at rest and red (#D32F2F) during export.

Preview images maintain their aspect ratio — a tall narrow image scales to fit within the preview box without stretching. When no image is loaded, the area shows placeholder text ("Drop lines here" or similar).

Path labels truncate from the left: a path like `/Users/adam/Documents/projects/art/kitty.lines` becomes `...projects/art/kitty.lines` to fit the available width. Labels re-truncate when you resize the window.

## Tooltips

If the CTkToolTip package is installed, hovering over buttons and controls shows brief descriptions. Tooltips appear after 200ms with a slight offset from the cursor. This is optional — the app works without it.
