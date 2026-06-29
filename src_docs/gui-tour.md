# GUI Tour

A quick walkthrough of the three input tabs and the shared controls.

## Window layout at a glance

```
+--------------------------------------+-----------------+
|  Tab: Lines | Images | Video         |  Style          |
|                                      |  End Style      |
|  [input list / controls]  [preview]  |  [preview]      |
+--------------------------------------+-----------------+
|  Export as [Format ▾]  [Size ▾]  ♪ ○       [Export ▶]  |
+-----------------------------------------------------------+
```

The left panel (roughly two-thirds) holds the active tab.  The right panel
holds the style picker.  The bottom strip is always visible regardless of
which tab is active.

---

## Tab 1 — Lines

**Purpose:** batch-export `.lines` documents as SVG, PNG, JPG, or plain copies.

What you see:

- **Left half** — scrollable file list.  Click a name to select it (blue highlight).
- **Right half** — preview image extracted from the selected file's embedded data.
- **Buttons below the list** — **+** add files, **−** remove selected, **✕** clear all.

What to try:

1. Click **+** (or drag `.lines` files onto the list).
2. Select a file — the preview updates immediately.
3. Choose **LINES** in the format dropdown and click **Export ▶** to copy files
   without touching the MCP API.
4. Choose **PNG** or **JPG** to extract the embedded preview image from each file.

When the Lines tab is active the Style panel on the right is hidden — `.lines`
files carry their own fill structure and do not accept an external style.

---

## Tab 2 — Images

**Purpose:** apply a Vexy Lines fill style to raster images and export SVG or PNG/JPG.

What you see:

- **Left half** — scrollable image list with thumbnails.
- **Right half** — larger preview of the selected image.
- **Buttons below the list** — same **+** / **−** / **✕** as the Lines tab.

What to try:

1. Load a `.lines` style in the **Style** panel on the right.
2. Click **+** (or drag PNG/JPG/WEBP files onto the list).
3. Select an image — the preview updates.
4. Click **Export ▶** — each image is opened in Vexy Lines via MCP, the style's
   fill tree is replicated onto it, the engine renders, and the SVG or raster is
   saved.

A style **must** be loaded for image export.  If you export without one, the
app reports "A style file is required."

---

## Tab 3 — Video

**Purpose:** per-frame style transfer on video clips, with optional audio passthrough.

What you see:

- **Two preview panes** side by side — first and last frames of the selected range.
- **Range slider** with two draggable handles below the previews.
- **Start / End entry fields** — type exact frame numbers (1-indexed).
- **Frame count label** — shows how many frames are in the selected range.
- **Buttons** — **+** add a video, **✕** remove it, path label shows the file.

What to try:

1. Click **+** to load a video (MP4, MOV, MKV, AVI, WEBM).
2. Drag the range slider handles to pick a short segment for a test run (5–10 frames).
3. Load a style.
4. Choose **MP4** in the format dropdown and click **Export ▶**.

The range slider and text entries stay in sync.  Previews update whenever the
range changes — they show the actual first and last frames extracted via OpenCV.

---

## Style picker (right panel)

Two sub-tabs: **Style** and **End Style**.

- Click **+** to pick a `.lines` file.  A thumbnail appears immediately.
- Click **✕** to clear.
- Loading an **End Style** enables interpolation: the first input gets 100% start
  style, the last gets 100% end style, and the items in between get a proportional
  blend.

---

## Export controls (bottom strip)

| Control | Options | Notes |
|---------|---------|-------|
| **Format** | SVG, PNG, JPG, MP4, LINES | Not every format works on every tab |
| **Size** | 1×, 2×, 3×, 4× | Disabled for SVG and LINES |
| **♪ toggle** | on / off | Audio passthrough — visible only when conditions are met |
| **Export ▶** | — | Starts export on a background thread; shows progress |

During export the button label changes to a percentage and status message.
Click **Stop ■** to abort.

---

## Next steps

- [Full GUI Guide](gui-guide.md) — every control, every error message, every edge case.
- [Video Processing](video-processing.md) — the frame pipeline in detail.
- [Installation Troubleshooting](installation-troubleshooting.md) — platform gotchas.
