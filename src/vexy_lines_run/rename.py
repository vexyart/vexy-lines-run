# this_file: src/vexy_lines_run/rename.py
"""GUI-side glue for AI-assisted renaming of .lines layers and fills.

Wraps :func:`vexy_lines_api.rename.rename_lines` with progress reporting and a
background-thread launcher so the Tk main loop stays responsive. The
synchronous :func:`run_ai_rename` holds all the logic and is unit-testable
without Tkinter; :func:`start_ai_rename_thread` runs it on a daemon thread.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from vexy_lines_api import RenamePlan, VLMConfig
    from vexy_lines_api.client import MCPClient

ProgressCb = Callable[[int, int, str], None]
CompleteCb = Callable[["RenamePlan", "Path | None"], None]
ErrorCb = Callable[[str], None]


def count_fills(lines_path: str | Path) -> int:
    """Count fills (with an object ID) in a .lines file for progress totals."""
    from vexy_lines import GroupInfo, LayerInfo, parse

    total = 0

    def walk(nodes: list[GroupInfo | LayerInfo]) -> None:
        nonlocal total
        for node in nodes:
            if isinstance(node, GroupInfo):
                walk(node.children)
            elif isinstance(node, LayerInfo):
                total += sum(1 for f in node.fills if f.object_id is not None)

    walk(parse(lines_path).groups)
    return total


def run_ai_rename(
    lines_path: str | Path,
    output_path: str | Path | None = None,
    *,
    dpi: int = 72,
    config: VLMConfig | None = None,
    client: MCPClient | None = None,
    on_progress: ProgressCb | None = None,
    on_complete: CompleteCb | None = None,
    on_error: ErrorCb | None = None,
    **plan_kwargs: object,
) -> RenamePlan | None:
    """Rename a .lines file, reporting progress through callbacks.

    Args:
        lines_path: Path to the ``.lines`` file.
        output_path: Destination ``.lines`` path. Defaults to
            ``<stem>-renamed.lines`` beside the input.
        dpi: Render DPI passed to the engine.
        config: VLM settings; environment defaults when ``None``.
        client: A connected MCP client. When ``None``, the engine creates one.
        on_progress: Called as ``(current, total, message)`` per fill described.
        on_complete: Called as ``(plan, output_path)`` on success.
        on_error: Called as ``(message)`` on failure.
        **plan_kwargs: Forwarded to the engine (e.g. ``render_png``, ``suggest``,
            ``describe``, ``save_artifacts``) — mainly for tests.

    Returns:
        The :class:`RenamePlan` on success, or ``None`` on error.
    """
    from vexy_lines_api.rename import describe_region, rename_lines
    from vexy_lines_api.rename.vlm import default_config

    src = Path(lines_path)
    config = config or default_config()

    try:
        total = count_fills(src)
        counter = {"n": 0}

        user_describe = plan_kwargs.pop("describe", None)

        def base_describe(png: bytes) -> str:
            if callable(user_describe):
                return str(user_describe(png))
            return describe_region(png, config=config)

        def describe_with_progress(png: bytes) -> str:
            counter["n"] += 1
            if on_progress is not None:
                on_progress(counter["n"], total, f"Describing fill {counter['n']}/{total}")
            return base_describe(png)

        if on_progress is not None:
            on_progress(0, total, "Rendering artwork…")

        out = Path(output_path) if output_path is not None else src.with_name(f"{src.stem}-renamed.lines")

        plan = rename_lines(
            src,
            out,
            client=client,
            config=config,
            dpi=dpi,
            describe=describe_with_progress,
            **plan_kwargs,  # type: ignore[arg-type]
        )
    except Exception as exc:
        logger.opt(exception=True).error("AI rename failed: {}", exc)
        if on_error is not None:
            on_error(str(exc))
        return None

    if on_complete is not None:
        on_complete(plan, out)
    return plan


def start_ai_rename_thread(
    lines_path: str | Path,
    output_path: str | Path | None = None,
    **kwargs: object,
) -> threading.Thread:
    """Run :func:`run_ai_rename` on a daemon thread and return it."""
    thread = threading.Thread(
        target=run_ai_rename,
        args=(lines_path, output_path),
        kwargs=kwargs,  # type: ignore[arg-type]
        daemon=True,
    )
    thread.start()
    return thread
