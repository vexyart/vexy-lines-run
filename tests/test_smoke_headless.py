# this_file: vexy-lines-run/tests/test_smoke_headless.py
"""Headless GUI smoke test for vexy-lines-run.

This module attempts to instantiate the real Tk/CustomTkinter window.  It
requires a display server:

- **Linux CI**: run under ``xvfb-run`` (the CI workflow does this).
- **macOS / Windows**: a display is always available; the test runs normally.
- **Linux without Xvfb**: the test is skipped with an informative reason.

The test does not exercise style transfer or MCP — it only verifies that the
App window can be created and destroyed without errors.  This catches import
failures, missing Tk/CTk widgets, and early-init crashes that unit tests
(which mock the GUI layer) cannot catch.
"""

from __future__ import annotations

import os
import sys

import pytest


def _has_display() -> bool:
    """Return True if a display is available for Tk to connect to."""
    if sys.platform == "linux":
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    # macOS and Windows always have a display in normal runtime environments.
    return True


@pytest.mark.skipif(
    not _has_display(),
    reason="No display available — run this test with xvfb-run on Linux",
)
def test_app_window_creates_and_destroys() -> None:
    """Smoke test: instantiate App, schedule immediate destroy, run mainloop.

    The test passes if the window opens and closes without raising an
    exception.  The ``after(0, destroy)`` call schedules destruction for the
    very first idle tick, so the window is never visible on screen.
    """
    # Import here (not at module level) so that the skip decorator fires
    # before any Tk initialisation attempt.
    from vexy_lines_run.app import App  # noqa: PLC0415

    app = App()
    # Schedule immediate destruction on the first event-loop tick so that
    # mainloop() exits right away without user interaction.
    app.after(0, app.destroy)
    app.mainloop()
    # If we reach this line the window opened and closed cleanly.
