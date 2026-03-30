# this_file: src/vexy_lines_run/__init__.py
"""GUI desktop application for Vexy Lines style transfer.

Provides a CustomTkinter-based desktop application for applying, previewing,
and exporting Vexy Lines styles across images, .lines files, and video.

Usage::

    from vexy_lines_run import App, launch

    launch()  # opens the GUI
"""

from __future__ import annotations

from vexy_lines_run.app import App, launch

__all__ = ["App", "launch"]
