# WORK.md

## 2026-06-12

- Added "BUNDLE" to both export format menus. In lines mode it exports
  PDF + SVG + PNG and extracts the embedded source image as `<stem>-src.jpg`
  via `vexy_lines_api.bundle.export_bundle`. The pipeline rejects BUNDLE for
  image/video inputs and for style-transfer exports.

## Current Status

- The GUI package inherits `.lines` image-filter chain support through `vexy-lines-py` and `vexy-lines-apy`.
- Extracted non-GUI processing logic into `vexy-lines-apy` to centralize the export pipeline.
- `vexy-lines-run` is now functioning as a pure CustomTkinter GUI layer.
- All 141 unit tests are passing successfully.

## Recent Work

- **Filter Support**: Documented that matching style image-filter chains are preserved and interpolated by the backend style picker.
- **Bug Fix**: Fixed `TclError: image "pyimage1" doesn't exist` when dragging an image into the list after clearing it (Issue 603).
- **Test Fixes**: Updated `test_ui_properties.py` and `test_ui_verification.py` to match exact application strings.
- **Dependency Setup**: Organized package dependencies using `customtkinter`, `tkinterdnd2`, `Pillow`, and other necessary libraries for image/SVG/video processing.
- **Import Adjustments**: Configured `sys.path` correctly in `conftest.py` so tests can resolve module imports easily.

## Test Results

| Suite | Tests | Status |
|---|---|---|
| vexy-lines-run | 141 | PASS |
