# this_file: vexy-lines-run/src/vexy_lines_run/__main__.py
"""Entry point for ``python -m vexy_lines_run``."""

from __future__ import annotations

from vexy_lines_run.app import launch


def main() -> None:
    """Launch the Vexy Lines Run application."""
    launch()


if __name__ == "__main__":
    main()
