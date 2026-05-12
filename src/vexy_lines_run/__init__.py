# this_file: src/vexy_lines_run/__init__.py
"""vexy-lines-run: CustomTkinter desktop GUI for Vexy Lines style transfer.

Three input tabs:

- **Lines** — load ``.lines`` files; export embedded previews or apply a new
  style to each document.
- **Images** — load PNG, JPG, WEBP; apply a style via the MCP API and export
  SVG, PNG, or JPG.
- **Video** — load MP4/MOV/MKV; per-frame style transfer with audio
  passthrough. Optional frame range selection via a dual-handle range slider.

Style picker selects a primary style from any ``.lines`` file. Select an
optional end style to interpolate across the input sequence.

All exports run on a daemon thread so the UI stays responsive. A persistent
job folder stores every intermediate artifact — if the app quits mid-export,
re-running resumes from the last completed item.

Usage::

    from vexy_lines_run import launch

    launch()  # open the window; blocks until closed

Or from the command line::

    vexy-lines-run
"""

from __future__ import annotations

from vexy_lines_run.app import App, launch

__all__ = ["App", "launch"]
