# this_file: vexy-lines-run/tests/conftest.py
"""Pytest configuration for vexy-lines-run tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the src directory is on sys.path so that `import vexy_lines_run` works
# even when running tests outside of a proper editable install.
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

# Also add sibling packages (vexy-lines-py and vexy-lines-apy) so that
# vexy_lines and vexy_lines_api are importable when vexy_lines_run imports them.
_root = _src.parent.parent
for _sibling in ("vexy-lines-py", "vexy-lines-apy"):
    _sibling_src = _root / _sibling / "src"
    if _sibling_src.exists() and str(_sibling_src) not in sys.path:
        sys.path.insert(0, str(_sibling_src))
