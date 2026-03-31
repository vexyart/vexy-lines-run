# CHANGELOG.md

## 2026-03-31 — Export Pipeline Centralization

- **fix**: When the vexy-lines-run GUI is in "Lines" mode, the Styles tabview is now completely hidden.
- **refactor**: Relocated core export orchestration logic (`process_export`, `_process_lines`, `_process_images`, `_process_video`) and generic media helpers out of `vexy-lines-run` and into `vexy-lines-apy` to share backend logic with the CLI.
- **refactor**: Updated the GUI application to utilize the new centralized `process_export` pipeline, securing `vexy-lines-run` as a pure CustomTkinter layer.
- **fix**: Adjusted UI tests (`test_ui_properties.py`, `test_ui_verification.py`) to align with text string changes, ensuring all 70 tests pass.

## 2026-03-30 — CustomTkinter Image Clearing Bug (Issue 603)

- **fix**: Resolved `TclError: image "pyimage1" doesn't exist` that occurred when dragging an image into the list after clearing it. Modified the clear function to wipe the underlying `tkinter.Label` widget so it doesn't hold onto garbage-collected `PhotoImage` references.
- **remove**: Removed `test_ui_issue_501.py` to fix a `RecursionError` caused by problematic Tkinter mocking.

## 2026-03-30 — Post-Decomposition Setup

- **fix**: Resolved `ModuleNotFoundError` across the test suite, bringing passing tests from 0 to 70.
- **add**: Added a `tests/conftest.py` with a `sys.path` fix for the source layout.
- **fix**: Fixed patch targets in `test_app.py` for `extract_preview_image` and assertions for `_parse_drop_data("")`.
- **add**: Created `py.typed` PEP 561 marker file to declare the package as typed.
- **fix**: Added `vexy_lines_api` and `vexy_lines` to ruff `isort` configuration as known first-party modules.