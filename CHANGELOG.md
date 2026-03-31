# CHANGELOG.md

## 2026-03-31 — Refactoring Cleanup & Test Fixes (Issue 613)

- **refactor**: Deleted stale `protocols.py` — was out of sync with live code (used `int` indices instead of `str` keys, referenced non-existent `_FileListState`), unused at runtime.
- **refactor**: Replaced raw `cv2` usage in `_get_video_frame_count` with `vexy_lines_api.video.probe()`, removing direct OpenCV dependency from the GUI layer.
- **refactor**: Removed dead code `_choose_output_path` from `app.py` (defined but never called).
- **refactor**: Trimmed `processing.py.__all__` from 14 entries to just `process_export`.
- **refactor**: Deduplicated DnD hint strings between `layout.py` and `handlers.py` into `self._lines_hint`, `self._images_hint`, `self._video_hint` instance attributes in `app.py.__init__`.
- **refactor**: Renamed misleading `MAX_STORED_STYLES` constant to `MIN_TRUNCATE_CHARS` in `helpers.py`.
- **fix**: Corrected two inverted color assertions in `test_ui_verification.py` (`test_export_button_red_during_export` and `test_export_button_red_hover_color` were checking green instead of red).
- **fix**: Replaced tautological `test_delegates_to_parser` with meaningful `test_returns_none_on_nonexistent_path`.
- **fix**: Removed vacuous `test_import_ui_verification_module` (`assert True`).
- **fix**: Replaced never-failing `test_raises_import_error_without_av` with meaningful assertion.
- **fix**: Replaced `file://` path dependencies in `pyproject.toml` with proper PyPI version references (`vexy-lines-py>=1.0.13`, `vexy-lines-apy>=1.0.20`).
- **test**: 129 tests passing.

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