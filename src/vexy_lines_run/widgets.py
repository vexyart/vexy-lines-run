# this_file: src/vexy_lines_run/widgets.py
"""Custom widgets for the Vexy Lines GUI.

Provides ``CTkRangeSlider`` -- a dual-handle range slider built on
CustomTkinter, used for selecting video frame ranges.
"""

from __future__ import annotations

from typing import Any

import customtkinter as ctk
from loguru import logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_TRACK_HEIGHT = 6
_HANDLE_RADIUS = 8
_DEFAULT_FROM = 0
_DEFAULT_TO = 100


class CTkRangeSlider(ctk.CTkFrame):  # type: ignore[misc]
    """Dual-handle range slider for selecting a sub-range within [from_, to].

    The widget renders a horizontal track with two draggable handles. Values
    are clamped to the configured range and the ``command`` callback fires
    whenever either handle moves.

    Args:
        master: Parent widget.
        from_: Lower bound of the range.
        to: Upper bound of the range.
        command: Callback receiving ``(low, high)`` when values change.
        number_of_steps: If set, snap values to this many discrete steps.
        **kwargs: Extra keyword arguments forwarded to ``CTkFrame``.

    Example::

        slider = CTkRangeSlider(root, from_=0, to=1000, command=on_change)
        slider.set(100, 500)
        low, high = slider.get()
    """

    def __init__(
        self,
        master: Any = None,
        from_: int | float = _DEFAULT_FROM,
        to: int | float = _DEFAULT_TO,
        command: Any = None,
        number_of_steps: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)

        self._from = float(from_)
        self._to = float(to)
        self._command = command
        self._number_of_steps = number_of_steps

        self._low = self._from
        self._high = self._to

        self._dragging: str | None = None  # "low" | "high" | None

        # Canvas for rendering
        self._canvas = ctk.CTkCanvas(  # type: ignore[attr-defined]
            self,
            height=_HANDLE_RADIUS * 2 + 4,
            highlightthickness=0,
        )
        self._canvas.pack(fill="x", expand=True, padx=_HANDLE_RADIUS)

        self._canvas.bind("<Configure>", self._on_configure)
        self._canvas.bind("<Button-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self) -> tuple[float, float]:
        """Return the current ``(low, high)`` values."""
        return (self._low, self._high)

    def set(self, low: float, high: float) -> None:
        """Set both handle positions, clamped to [from_, to].

        Args:
            low: New lower value.
            high: New upper value.
        """
        self._low = self._clamp(min(low, high))
        self._high = self._clamp(max(low, high))
        self._draw()

    @property
    def from_(self) -> float:
        """Lower bound of the range."""
        return self._from

    @from_.setter
    def from_(self, value: float) -> None:
        self._from = float(value)
        self._low = max(self._low, self._from)
        self._draw()

    @property
    def to(self) -> float:
        """Upper bound of the range."""
        return self._to

    @to.setter
    def to(self, value: float) -> None:
        self._to = float(value)
        self._high = min(self._high, self._to)
        self._draw()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _clamp(self, value: float) -> float:
        """Clamp *value* to the configured range, with optional snapping."""
        value = max(self._from, min(self._to, value))
        if self._number_of_steps is not None and self._number_of_steps > 0:
            step = (self._to - self._from) / self._number_of_steps
            value = round((value - self._from) / step) * step + self._from
        return value

    def _value_to_x(self, value: float) -> float:
        """Convert a range value to a canvas x coordinate."""
        width = self._canvas.winfo_width()
        if width <= 0:
            return 0.0
        span = self._to - self._from
        if span == 0:
            return 0.0
        return (value - self._from) / span * width

    def _x_to_value(self, x: float) -> float:
        """Convert a canvas x coordinate to a range value."""
        width = self._canvas.winfo_width()
        if width <= 0:
            return self._from
        span = self._to - self._from
        return self._clamp(x / width * span + self._from)

    def _draw(self) -> None:
        """Redraw the track and handles on the canvas."""
        self._canvas.delete("all")
        w = self._canvas.winfo_width()
        cy = _HANDLE_RADIUS + 2  # vertical centre

        if w <= 0:
            return

        # Track background
        self._canvas.create_rectangle(
            0,
            cy - _TRACK_HEIGHT // 2,
            w,
            cy + _TRACK_HEIGHT // 2,
            fill="#3a3a3a",
            outline="",
        )

        # Active range
        x_low = self._value_to_x(self._low)
        x_high = self._value_to_x(self._high)
        self._canvas.create_rectangle(
            x_low,
            cy - _TRACK_HEIGHT // 2,
            x_high,
            cy + _TRACK_HEIGHT // 2,
            fill="#1f6aa5",
            outline="",
        )

        # Handles
        for x in (x_low, x_high):
            self._canvas.create_oval(
                x - _HANDLE_RADIUS,
                cy - _HANDLE_RADIUS,
                x + _HANDLE_RADIUS,
                cy + _HANDLE_RADIUS,
                fill="#dce4ee",
                outline="#1f6aa5",
                width=2,
            )

    def _on_configure(self, _event: Any) -> None:
        self._draw()

    def _on_press(self, event: Any) -> None:
        x_low = self._value_to_x(self._low)
        x_high = self._value_to_x(self._high)
        dist_low = abs(event.x - x_low)
        dist_high = abs(event.x - x_high)

        if dist_low <= dist_high:
            self._dragging = "low"
        else:
            self._dragging = "high"

        self._move_handle(event.x)

    def _on_drag(self, event: Any) -> None:
        if self._dragging:
            self._move_handle(event.x)

    def _on_release(self, _event: Any) -> None:
        self._dragging = None

    def _move_handle(self, x: float) -> None:
        """Move the currently-dragged handle to canvas position *x*."""
        value = self._x_to_value(x)

        if self._dragging == "low":
            self._low = min(value, self._high)
        elif self._dragging == "high":
            self._high = max(value, self._low)

        self._draw()

        if self._command is not None:
            try:
                self._command(self._low, self._high)
            except Exception:
                logger.opt(exception=True).warning("Range slider command callback failed")
