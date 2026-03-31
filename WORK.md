# WORK.md

## Current Status

- Extracted non-GUI processing logic into `vexy-lines-apy` to centralize the export pipeline.
- `vexy-lines-run` is now functioning as a pure CustomTkinter GUI layer.
- All 70 unit tests are passing successfully.

## Recent Work

- **Bug Fix**: Fixed `TclError: image "pyimage1" doesn't exist` when dragging an image into the list after clearing it (Issue 603).
- **Test Fixes**: Updated `test_ui_properties.py` and `test_ui_verification.py` to match exact application strings.
- **Dependency Setup**: Organized package dependencies using `customtkinter`, `tkinterdnd2`, `Pillow`, and other necessary libraries for image/SVG/video processing.
- **Import Adjustments**: Configured `sys.path` correctly in `conftest.py` so tests can resolve module imports easily.

## Test Results

| Suite | Tests | Status |
|---|---|---|
| vexy-lines-run | 131 | PASS |
