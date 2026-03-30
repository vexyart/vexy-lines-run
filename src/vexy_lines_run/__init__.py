# this_file: src/vexy_lines_run/__init__.py
"""Vexy Lines desktop GUI — apply, preview, and export styles.

Three-tab CustomTkinter app supporting .lines files, raster images, and video.
Style transfer runs on a background thread; progress feeds back to the UI.

Usage::

    from vexy_lines_run import App, launch

    launch()  # open the GUI window
"""

from __future__ import annotations

from vexy_lines_run.app import App, launch

__all__ = ["App", "launch"]
