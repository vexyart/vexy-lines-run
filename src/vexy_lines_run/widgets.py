# this_file: src/vexy_lines_run/widgets.py
"""CTkRangeSlider - Range slider widget for customtkinter.

Original author: Akash Bora (Version 0.3).
Bundled into vexy-lines-run to avoid an external dependency.
Faithful port from ``vexy_lines_utils.gui.widgets``.
"""

from __future__ import annotations

import math
import sys
import tkinter as tk
from typing import TYPE_CHECKING

from customtkinter.windows.widgets.core_rendering import CTkCanvas
from customtkinter.windows.widgets.core_widget_classes import CTkBaseClass
from customtkinter.windows.widgets.theme import ThemeManager

if TYPE_CHECKING:
    from collections.abc import Callable


class CustomDrawEngine:
    """Custom DrawEngine for the range slider, handling all canvas drawing."""

    preferred_drawing_method: str = "circle_shapes" if sys.platform == "darwin" else "font_shapes"

    def __init__(self, canvas: CTkCanvas) -> None:
        self._canvas = canvas

    def __calc_optimal_corner_radius(self, user_corner_radius: float) -> float | int:
        if self.preferred_drawing_method == "polygon_shapes":
            return user_corner_radius if sys.platform == "darwin" else round(user_corner_radius)
        if self.preferred_drawing_method == "font_shapes":
            return round(user_corner_radius)
        if self.preferred_drawing_method == "circle_shapes":
            user_corner_radius = 0.5 * round(user_corner_radius / 0.5)
            if user_corner_radius == 0:
                return 0
            return user_corner_radius + 0.5 if user_corner_radius % 1 == 0 else user_corner_radius
        return user_corner_radius

    # -- polygon_shapes rounded rect -----------------------------------------

    def __draw_rounded_rect_with_border_polygon_shapes(
        self, width, height, corner_radius, border_width, inner_corner_radius
    ):
        requires_recoloring = False
        if border_width > 0:
            if not self._canvas.find_withtag("border_parts"):
                self._canvas.create_polygon((0, 0, 0, 0), tags=("border_line_1", "border_parts"))
                requires_recoloring = True
            self._canvas.coords(
                "border_line_1",
                corner_radius,
                corner_radius,
                width - corner_radius,
                corner_radius,
                width - corner_radius,
                height - corner_radius,
                corner_radius,
                height - corner_radius,
            )
            self._canvas.itemconfig("border_line_1", joinstyle=tk.ROUND, width=corner_radius * 2)
        else:
            self._canvas.delete("border_parts")
        if not self._canvas.find_withtag("inner_parts"):
            self._canvas.create_polygon((0, 0, 0, 0), tags=("inner_line_1", "inner_parts"), joinstyle=tk.ROUND)
            requires_recoloring = True
        bottom_right_shift = -1 if corner_radius <= border_width else 0
        self._canvas.coords(
            "inner_line_1",
            border_width + inner_corner_radius,
            border_width + inner_corner_radius,
            width - (border_width + inner_corner_radius) + bottom_right_shift,
            border_width + inner_corner_radius,
            width - (border_width + inner_corner_radius) + bottom_right_shift,
            height - (border_width + inner_corner_radius) + bottom_right_shift,
            border_width + inner_corner_radius,
            height - (border_width + inner_corner_radius) + bottom_right_shift,
        )
        self._canvas.itemconfig("inner_line_1", width=inner_corner_radius * 2)
        if requires_recoloring:
            self._canvas.tag_lower("inner_parts")
            self._canvas.tag_lower("border_parts")
        return requires_recoloring

    # -- font_shapes rounded rect --------------------------------------------

    def __draw_rounded_rect_with_border_font_shapes(
        self, width, height, corner_radius, border_width, inner_corner_radius, exclude_parts
    ):
        requires_recoloring = False
        if border_width > 0:
            if corner_radius > 0:
                for tag_num, cond, x, y in [
                    (1, True, corner_radius, corner_radius),
                    (2, width > 2 * corner_radius, width - corner_radius, corner_radius),
                    (
                        3,
                        height > 2 * corner_radius and width > 2 * corner_radius,
                        width - corner_radius,
                        height - corner_radius,
                    ),
                    (4, height > 2 * corner_radius, corner_radius, height - corner_radius),
                ]:
                    tag_a = f"border_oval_{tag_num}_a"
                    tag_b = f"border_oval_{tag_num}_b"
                    excl = f"border_oval_{tag_num}"
                    if not self._canvas.find_withtag(tag_a) and cond and excl not in exclude_parts:
                        self._canvas.create_aa_circle(
                            0, 0, 0, tags=(tag_a, "border_corner_part", "border_parts"), anchor=tk.CENTER
                        )
                        self._canvas.create_aa_circle(
                            0, 0, 0, tags=(tag_b, "border_corner_part", "border_parts"), anchor=tk.CENTER, angle=180
                        )
                        requires_recoloring = True
                    elif self._canvas.find_withtag(tag_a) and (not cond or excl in exclude_parts):
                        self._canvas.delete(tag_a, tag_b)
                    self._canvas.coords(tag_a, x, y, corner_radius)
                    self._canvas.coords(tag_b, x, y, corner_radius)
            else:
                self._canvas.delete("border_corner_part")
            if not self._canvas.find_withtag("border_rectangle_1"):
                self._canvas.create_rectangle(
                    0, 0, 0, 0, tags=("border_rectangle_1", "border_rectangle_part", "border_parts"), width=0
                )
                self._canvas.create_rectangle(
                    0, 0, 0, 0, tags=("border_rectangle_2", "border_rectangle_part", "border_parts"), width=0
                )
                requires_recoloring = True
            self._canvas.coords("border_rectangle_1", (0, corner_radius, width, height - corner_radius))
            self._canvas.coords("border_rectangle_2", (corner_radius, 0, width - corner_radius, height))
        else:
            self._canvas.delete("border_parts")

        if inner_corner_radius > 0:
            for tag_num, cond, x, y in [
                (1, True, border_width + inner_corner_radius, border_width + inner_corner_radius),
                (
                    2,
                    width - (2 * border_width) > 2 * inner_corner_radius,
                    width - border_width - inner_corner_radius,
                    border_width + inner_corner_radius,
                ),
                (
                    3,
                    height - (2 * border_width) > 2 * inner_corner_radius
                    and width - (2 * border_width) > 2 * inner_corner_radius,
                    width - border_width - inner_corner_radius,
                    height - border_width - inner_corner_radius,
                ),
                (
                    4,
                    height - (2 * border_width) > 2 * inner_corner_radius,
                    border_width + inner_corner_radius,
                    height - border_width - inner_corner_radius,
                ),
            ]:
                tag_a = f"inner_oval_{tag_num}_a"
                tag_b = f"inner_oval_{tag_num}_b"
                excl = f"inner_oval_{tag_num}"
                if not self._canvas.find_withtag(tag_a) and cond and excl not in exclude_parts:
                    self._canvas.create_aa_circle(
                        0, 0, 0, tags=(tag_a, "inner_corner_part", "inner_parts"), anchor=tk.CENTER
                    )
                    self._canvas.create_aa_circle(
                        0, 0, 0, tags=(tag_b, "inner_corner_part", "inner_parts"), anchor=tk.CENTER, angle=180
                    )
                    requires_recoloring = True
                elif self._canvas.find_withtag(tag_a) and (not cond or excl in exclude_parts):
                    self._canvas.delete(tag_a, tag_b)
                self._canvas.coords(tag_a, x, y, inner_corner_radius)
                self._canvas.coords(tag_b, x, y, inner_corner_radius)
        else:
            self._canvas.delete("inner_corner_part")

        if not self._canvas.find_withtag("inner_rectangle_1"):
            self._canvas.create_rectangle(
                0, 0, 0, 0, tags=("inner_rectangle_1", "inner_rectangle_part", "inner_parts"), width=0
            )
            requires_recoloring = True
        if not self._canvas.find_withtag("inner_rectangle_2") and inner_corner_radius * 2 < height - (border_width * 2):
            self._canvas.create_rectangle(
                0, 0, 0, 0, tags=("inner_rectangle_2", "inner_rectangle_part", "inner_parts"), width=0
            )
            requires_recoloring = True
        elif self._canvas.find_withtag("inner_rectangle_2") and not inner_corner_radius * 2 < height - (
            border_width * 2
        ):
            self._canvas.delete("inner_rectangle_2")
        self._canvas.coords(
            "inner_rectangle_1",
            border_width + inner_corner_radius,
            border_width,
            width - border_width - inner_corner_radius,
            height - border_width,
        )
        self._canvas.coords(
            "inner_rectangle_2",
            border_width,
            border_width + inner_corner_radius,
            width - border_width,
            height - inner_corner_radius - border_width,
        )
        if requires_recoloring:
            self._canvas.tag_lower("inner_parts")
            self._canvas.tag_lower("border_parts")
        return requires_recoloring

    # -- circle_shapes rounded rect ------------------------------------------

    def __draw_rounded_rect_with_border_circle_shapes(
        self, width, height, corner_radius, border_width, inner_corner_radius
    ):
        requires_recoloring = False
        if border_width > 0:
            if corner_radius > 0:
                if not self._canvas.find_withtag("border_oval_1"):
                    for i in range(1, 5):
                        self._canvas.create_oval(0, 0, 0, 0, tags=(f"border_oval_{i}", "border_parts"), width=0)
                    requires_recoloring = True
                cr2 = 2 * corner_radius
                self._canvas.coords("border_oval_1", 0, 0, cr2, cr2)
                self._canvas.coords("border_oval_2", width - cr2, 0, width, cr2)
                self._canvas.coords("border_oval_3", width - cr2, height - cr2, width, height)
                self._canvas.coords("border_oval_4", 0, height - cr2, cr2, height)
            if not self._canvas.find_withtag("border_rectangle_1"):
                self._canvas.create_rectangle(0, 0, 0, 0, tags=("border_rectangle_1", "border_parts"), width=0)
                self._canvas.create_rectangle(0, 0, 0, 0, tags=("border_rectangle_2", "border_parts"), width=0)
                requires_recoloring = True
            self._canvas.coords("border_rectangle_1", corner_radius, 0, width - corner_radius, height)
            self._canvas.coords("border_rectangle_2", 0, corner_radius, width, height - corner_radius)
        else:
            self._canvas.delete("border_parts")
        if not self._canvas.find_withtag("inner_rectangle_1"):
            self._canvas.create_rectangle(0, 0, 0, 0, tags=("inner_rectangle_1", "inner_parts"), width=0)
            requires_recoloring = True
        if inner_corner_radius > 0:
            if not self._canvas.find_withtag("inner_oval_1"):
                for i in range(1, 5):
                    self._canvas.create_oval(0, 0, 0, 0, tags=(f"inner_oval_{i}", "inner_parts"), width=0)
                requires_recoloring = True
            icr2 = 2 * inner_corner_radius
            bw = border_width
            self._canvas.coords("inner_oval_1", bw, bw, bw + icr2, bw + icr2)
            self._canvas.coords("inner_oval_2", width - bw - icr2, bw, width - bw, bw + icr2)
            self._canvas.coords("inner_oval_3", width - bw - icr2, height - bw - icr2, width - bw, height - bw)
            self._canvas.coords("inner_oval_4", bw, height - bw - icr2, bw + icr2, height - bw)
        else:
            self._canvas.delete("inner_oval_1", "inner_oval_2", "inner_oval_3", "inner_oval_4")
        self._canvas.coords(
            "inner_rectangle_1",
            border_width + inner_corner_radius,
            border_width,
            width - border_width - inner_corner_radius,
            height - border_width,
        )
        if requires_recoloring:
            self._canvas.tag_lower("inner_parts")
            self._canvas.tag_lower("border_parts")
        return requires_recoloring

    # -- polygon progress bar ------------------------------------------------

    def __draw_rounded_progress_bar_polygon(
        self, width, height, corner_radius, border_width, inner_corner_radius, pv1, pv2, orientation
    ):
        rc = self.__draw_rounded_rect_with_border_polygon_shapes(
            width, height, corner_radius, border_width, inner_corner_radius
        )
        if not self._canvas.find_withtag("progress_parts"):
            self._canvas.create_polygon((0, 0, 0, 0), tags=("progress_line_1", "progress_parts"), joinstyle=tk.ROUND)
            self._canvas.tag_raise("progress_parts", "inner_parts")
            rc = True
        iw = width - 2 * border_width - 2 * inner_corner_radius
        ih = height - 2 * border_width - 2 * inner_corner_radius
        bic = border_width + inner_corner_radius
        if orientation == "w":
            self._canvas.coords(
                "progress_line_1",
                bic + iw * pv1,
                bic,
                bic + iw * pv2,
                bic,
                bic + iw * pv2,
                height - bic,
                bic + iw * pv1,
                height - bic,
            )
        elif orientation == "s":
            self._canvas.coords(
                "progress_line_1",
                bic,
                bic + ih * (1 - pv2),
                width - bic,
                bic + ih * (1 - pv2),
                width - bic,
                bic + ih * (1 - pv1),
                bic,
                bic + ih * (1 - pv1),
            )
        self._canvas.itemconfig("progress_line_1", width=inner_corner_radius * 2)
        return rc

    # -- circle_shapes progress bar ------------------------------------------

    def __draw_rounded_progress_bar_circle(
        self, width, height, corner_radius, border_width, inner_corner_radius, pv1, pv2, orientation
    ):
        rc = self.__draw_rounded_rect_with_border_circle_shapes(
            width, height, corner_radius, border_width, inner_corner_radius
        )
        if not self._canvas.find_withtag("progress_rectangle_1"):
            self._canvas.create_rectangle(0, 0, 0, 0, tags=("progress_rectangle_1", "progress_parts"), width=0)
            rc = True
        iw = width - 2 * border_width - 2 * inner_corner_radius
        ih = height - 2 * border_width - 2 * inner_corner_radius
        bic = border_width + inner_corner_radius
        bw = border_width
        if orientation == "w":
            x1 = bic + iw * pv1
            x2 = bic + iw * pv2
            self._canvas.coords("progress_rectangle_1", x1, bw, x2, height - bw)
        elif orientation == "s":
            y1 = bic + ih * (1 - pv2)
            y2 = bic + ih * (1 - pv1)
            self._canvas.coords("progress_rectangle_1", bw, y1, width - bw, y2)
        if inner_corner_radius > 0:
            if not self._canvas.find_withtag("progress_oval_1"):
                for i in range(1, 5):
                    self._canvas.create_oval(0, 0, 0, 0, tags=(f"progress_oval_{i}", "progress_parts"), width=0)
                rc = True
            icr = inner_corner_radius
            if orientation == "w":
                self._canvas.coords("progress_oval_1", x1 - icr, bw, x1 + icr, bw + 2 * icr)
                self._canvas.coords("progress_oval_2", x2 - icr, bw, x2 + icr, bw + 2 * icr)
                self._canvas.coords("progress_oval_3", x2 - icr, height - bw - 2 * icr, x2 + icr, height - bw)
                self._canvas.coords("progress_oval_4", x1 - icr, height - bw - 2 * icr, x1 + icr, height - bw)
            elif orientation == "s":
                self._canvas.coords("progress_oval_1", bw, y1 - icr, bw + 2 * icr, y1 + icr)
                self._canvas.coords("progress_oval_2", width - bw - 2 * icr, y1 - icr, width - bw, y1 + icr)
                self._canvas.coords("progress_oval_3", width - bw - 2 * icr, y2 - icr, width - bw, y2 + icr)
                self._canvas.coords("progress_oval_4", bw, y2 - icr, bw + 2 * icr, y2 + icr)
        else:
            self._canvas.delete("progress_oval_1", "progress_oval_2", "progress_oval_3", "progress_oval_4")
        return rc

    # -- font_shapes progress bar (simplified) -------------------------------

    def __draw_rounded_progress_bar_font(
        self, width, height, corner_radius, border_width, inner_corner_radius, pv1, pv2, orientation
    ):
        rc2 = self.__draw_rounded_rect_with_border_font_shapes(
            width, height, corner_radius, border_width, inner_corner_radius, ()
        )
        rc = False
        icr = inner_corner_radius
        bw = border_width
        iw = width - 2 * bw - 2 * icr
        ih = height - 2 * bw - 2 * icr
        bic = bw + icr

        if icr > 0:
            if not self._canvas.find_withtag("progress_oval_1_a"):
                for i in range(1, 5):
                    self._canvas.create_aa_circle(
                        0,
                        0,
                        0,
                        tags=(f"progress_oval_{i}_a", "progress_corner_part", "progress_parts"),
                        anchor=tk.CENTER,
                    )
                    self._canvas.create_aa_circle(
                        0,
                        0,
                        0,
                        tags=(f"progress_oval_{i}_b", "progress_corner_part", "progress_parts"),
                        anchor=tk.CENTER,
                        angle=180,
                    )
                rc = True
        if not self._canvas.find_withtag("progress_rectangle_1"):
            self._canvas.create_rectangle(
                0, 0, 0, 0, tags=("progress_rectangle_1", "progress_rectangle_part", "progress_parts"), width=0
            )
            rc = True
        if not self._canvas.find_withtag("progress_rectangle_2") and icr * 2 < height - bw * 2:
            self._canvas.create_rectangle(
                0, 0, 0, 0, tags=("progress_rectangle_2", "progress_rectangle_part", "progress_parts"), width=0
            )
            rc = True

        if orientation == "w":
            x1 = bic + iw * pv1
            x2 = bic + iw * pv2
            if icr > 0:
                self._canvas.coords("progress_oval_1_a", x1, bic, icr)
                self._canvas.coords("progress_oval_1_b", x1, bic, icr)
                self._canvas.coords("progress_oval_2_a", x2, bic, icr)
                self._canvas.coords("progress_oval_2_b", x2, bic, icr)
                self._canvas.coords("progress_oval_3_a", x2, height - bw - icr, icr)
                self._canvas.coords("progress_oval_3_b", x2, height - bw - icr, icr)
                self._canvas.coords("progress_oval_4_a", x1, height - bw - icr, icr)
                self._canvas.coords("progress_oval_4_b", x1, height - bw - icr, icr)
            self._canvas.coords("progress_rectangle_1", x1, bw, x2, height - bw)
            self._canvas.coords(
                "progress_rectangle_2",
                bw + 2 * icr + (width - 2 * icr - 2 * bw) * pv1,
                bic,
                bw + 2 * icr + (width - 2 * icr - 2 * bw) * pv2,
                height - icr - bw,
            )
        elif orientation == "s":
            y1 = bic + ih * (1 - pv2)
            y2 = bic + ih * (1 - pv1)
            if icr > 0:
                self._canvas.coords("progress_oval_1_a", bic, y1, icr)
                self._canvas.coords("progress_oval_1_b", bic, y1, icr)
                self._canvas.coords("progress_oval_2_a", width - bw - icr, y1, icr)
                self._canvas.coords("progress_oval_2_b", width - bw - icr, y1, icr)
                self._canvas.coords("progress_oval_3_a", width - bw - icr, y2, icr)
                self._canvas.coords("progress_oval_3_b", width - bw - icr, y2, icr)
                self._canvas.coords("progress_oval_4_a", bic, y2, icr)
                self._canvas.coords("progress_oval_4_b", bic, y2, icr)
            self._canvas.coords("progress_rectangle_1", bic, bw + ih * (1 - pv2), width - bw - icr, bw + ih * (1 - pv1))
            self._canvas.coords("progress_rectangle_2", bw, bic + ih * (1 - pv2), width - bw, bic + ih * (1 - pv1))

        return rc or rc2

    # -- main slider draw entry point ----------------------------------------

    def draw_rounded_slider_with_border_and_2_button(
        self,
        width,
        height,
        corner_radius,
        border_width,
        button_length,
        button_corner_radius,
        slider_value,
        slider_2_value,
        orientation,
    ):
        width = math.floor(width / 2) * 2
        height = math.floor(height / 2) * 2
        if corner_radius > width / 2 or corner_radius > height / 2:
            corner_radius = min(width / 2, height / 2)
        if button_corner_radius > width / 2 or button_corner_radius > height / 2:
            button_corner_radius = min(width / 2, height / 2)
        button_length = round(button_length)
        border_width = round(border_width)
        button_corner_radius = round(button_corner_radius)
        corner_radius = self.__calc_optimal_corner_radius(corner_radius)
        inner_corner_radius = corner_radius - border_width if corner_radius >= border_width else 0

        if self.preferred_drawing_method == "polygon_shapes":
            return self.__draw_slider_polygon(
                width,
                height,
                corner_radius,
                border_width,
                inner_corner_radius,
                button_length,
                button_corner_radius,
                slider_value,
                slider_2_value,
                orientation,
            )
        if self.preferred_drawing_method == "font_shapes":
            return self.__draw_slider_font(
                width,
                height,
                corner_radius,
                border_width,
                inner_corner_radius,
                button_length,
                button_corner_radius,
                slider_value,
                slider_2_value,
                orientation,
            )
        if self.preferred_drawing_method == "circle_shapes":
            return self.__draw_slider_circle(
                width,
                height,
                corner_radius,
                border_width,
                inner_corner_radius,
                button_length,
                button_corner_radius,
                slider_value,
                slider_2_value,
                orientation,
            )
        return False

    # -- polygon slider buttons ----------------------------------------------

    def __draw_slider_polygon(self, width, height, cr, bw, icr, bl, bcr, sv, sv2, orient):
        rc = self.__draw_rounded_progress_bar_polygon(width, height, cr, bw, icr, sv, sv2, orient)
        if not self._canvas.find_withtag("slider_parts"):
            self._canvas.create_polygon(
                (0, 0, 0, 0), tags=("slider_line_1", "slider_parts", "slider_0_parts"), joinstyle=tk.ROUND
            )
            self._canvas.create_polygon(
                (0, 0, 0, 0), tags=("slider_2_line_1", "slider_parts", "slider_1_parts"), joinstyle=tk.ROUND
            )
            self._canvas.tag_raise("slider_parts")
            rc = True
        for val, tag in [(sv, "slider_line_1"), (sv2, "slider_2_line_1")]:
            if orient == "w":
                xp = cr + (bl / 2) + (width - 2 * cr - bl) * val
                self._canvas.coords(
                    tag, xp - bl / 2, bcr, xp + bl / 2, bcr, xp + bl / 2, height - bcr, xp - bl / 2, height - bcr
                )
            elif orient == "s":
                yp = cr + (bl / 2) + (height - 2 * cr - bl) * (1 - val)
                self._canvas.coords(
                    tag, bcr, yp - bl / 2, bcr, yp + bl / 2, width - bcr, yp + bl / 2, width - bcr, yp - bl / 2
                )
            self._canvas.itemconfig(tag, width=bcr * 2)
        return rc

    # -- circle_shapes slider buttons ----------------------------------------

    def __draw_slider_circle(self, width, height, cr, bw, icr, bl, bcr, sv, sv2, orient):
        rc = self.__draw_rounded_progress_bar_circle(width, height, cr, bw, icr, sv, sv2, orient)
        for part_tag, slider_prefix in [("slider_0_parts", "slider"), ("slider_1_parts", "slider_2")]:
            if not self._canvas.find_withtag(part_tag):
                for i in range(1, 5):
                    self._canvas.create_oval(
                        0,
                        0,
                        0,
                        0,
                        tags=(
                            f"{slider_prefix}_oval_{i}" if slider_prefix == "slider" else f"slider_oval_2_{i}",
                            "slider_parts",
                            part_tag,
                        ),
                        width=0,
                    )
                self._canvas.create_rectangle(
                    0,
                    0,
                    0,
                    0,
                    tags=(
                        f"{slider_prefix}_rectangle_1" if slider_prefix == "slider" else "slider_rectangle_2_1",
                        "slider_parts",
                        part_tag,
                    ),
                    width=0,
                )
                self._canvas.create_rectangle(
                    0,
                    0,
                    0,
                    0,
                    tags=(
                        f"{slider_prefix}_rectangle_2" if slider_prefix == "slider" else "slider_rectangle_2_2",
                        "slider_parts",
                        part_tag,
                    ),
                    width=0,
                )
                rc = True

        for val, prefix in [(sv, "slider"), (sv2, "slider_2")]:
            o1 = f"{prefix}_oval_1" if prefix == "slider" else "slider_oval_2_1"
            o2 = f"{prefix}_oval_2" if prefix == "slider" else "slider_oval_2_2"
            o3 = f"{prefix}_oval_3" if prefix == "slider" else "slider_oval_2_3"
            o4 = f"{prefix}_oval_4" if prefix == "slider" else "slider_oval_2_4"
            r1 = f"{prefix}_rectangle_1" if prefix == "slider" else "slider_rectangle_2_1"
            r2 = f"{prefix}_rectangle_2" if prefix == "slider" else "slider_rectangle_2_2"
            if orient == "w":
                xp = cr + (bl / 2) + (width - 2 * cr - bl) * val
                self._canvas.coords(o1, xp - bl / 2 - bcr, 0, xp - bl / 2 + bcr, 2 * bcr)
                self._canvas.coords(o2, xp + bl / 2 - bcr, 0, xp + bl / 2 + bcr, 2 * bcr)
                self._canvas.coords(o3, xp + bl / 2 - bcr, height - 2 * bcr, xp + bl / 2 + bcr, height)
                self._canvas.coords(o4, xp - bl / 2 - bcr, height - 2 * bcr, xp - bl / 2 + bcr, height)
                self._canvas.coords(r1, xp - bl / 2, 0, xp + bl / 2, height)
                self._canvas.coords(r2, xp - bl / 2 - bcr, bcr, xp + bl / 2 + bcr, height - bcr)
            elif orient == "s":
                yp = cr + (bl / 2) + (height - 2 * cr - bl) * (1 - val)
                self._canvas.coords(o1, 0, yp - bl / 2 - bcr, 2 * bcr, yp - bl / 2 + bcr)
                self._canvas.coords(o2, 0, yp + bl / 2 - bcr, 2 * bcr, yp + bl / 2 + bcr)
                self._canvas.coords(o3, width - 2 * bcr, yp + bl / 2 - bcr, width, yp + bl / 2 + bcr)
                self._canvas.coords(o4, width - 2 * bcr, yp - bl / 2 - bcr, width, yp - bl / 2 + bcr)
                self._canvas.coords(r1, 0, yp - bl / 2, width, yp + bl / 2)
                self._canvas.coords(r2, bcr, yp - bl / 2 - bcr, width - bcr, yp + bl / 2 + bcr)
        if rc:
            self._canvas.tag_raise("slider_parts")
        return rc

    # -- font_shapes slider buttons ------------------------------------------

    def __draw_slider_font(self, width, height, cr, bw, icr, bl, bcr, sv, sv2, orient):
        rc = self.__draw_rounded_progress_bar_font(width, height, cr, bw, icr, sv, sv2, orient)
        # Create slider buttons for both handles
        for part_tag, prefix, val in [("slider_0_parts", "slider", sv), ("slider_1_parts", "slider_2", sv2)]:
            o1a = f"{prefix}_oval_1_a" if prefix == "slider" else "slider_oval_2_1_a"
            if not self._canvas.find_withtag(o1a):
                for i in range(1, 5):
                    ta = f"{prefix}_oval_{i}_a" if prefix == "slider" else f"slider_oval_2_{i}_a"
                    tb = f"{prefix}_oval_{i}_b" if prefix == "slider" else f"slider_oval_2_{i}_b"
                    self._canvas.create_aa_circle(
                        0, 0, 0, tags=(ta, "slider_corner_part", "slider_parts", part_tag), anchor=tk.CENTER
                    )
                    self._canvas.create_aa_circle(
                        0, 0, 0, tags=(tb, "slider_corner_part", "slider_parts", part_tag), anchor=tk.CENTER, angle=180
                    )
                rc = True
            r1 = f"{prefix}_rectangle_1" if prefix == "slider" else "slider_rectangle_2_1"
            r2 = f"{prefix}_rectangle_2" if prefix == "slider" else "slider_rectangle_2_2"
            if not self._canvas.find_withtag(r1) and bl > 0:
                self._canvas.create_rectangle(
                    0, 0, 0, 0, tags=(r1, "slider_rectangle_part", "slider_parts", part_tag), width=0
                )
                rc = True
            if not self._canvas.find_withtag(r2) and height > 2 * bcr:
                self._canvas.create_rectangle(
                    0, 0, 0, 0, tags=(r2, "slider_rectangle_part", "slider_parts", part_tag), width=0
                )
                rc = True

            if orient == "w":
                xp = cr + (bl / 2) + (width - 2 * cr - bl) * val
                for i, (dx, dy) in enumerate(
                    [(-(bl / 2), bcr), (bl / 2, bcr), (bl / 2, height - bcr), (-(bl / 2), height - bcr)], 1
                ):
                    ta = f"{prefix}_oval_{i}_a" if prefix == "slider" else f"slider_oval_2_{i}_a"
                    tb = f"{prefix}_oval_{i}_b" if prefix == "slider" else f"slider_oval_2_{i}_b"
                    self._canvas.coords(ta, xp + dx, dy, bcr)
                    self._canvas.coords(tb, xp + dx, dy, bcr)
                self._canvas.coords(r1, xp - bl / 2, 0, xp + bl / 2, height)
                self._canvas.coords(r2, xp - bl / 2 - bcr, bcr, xp + bl / 2 + bcr, height - bcr)
            elif orient == "s":
                yp = cr + (bl / 2) + (height - 2 * cr - bl) * (1 - val)
                for i, (dx, dy) in enumerate(
                    [(bcr, -(bl / 2)), (bcr, bl / 2), (width - bcr, bl / 2), (width - bcr, -(bl / 2))], 1
                ):
                    ta = f"{prefix}_oval_{i}_a" if prefix == "slider" else f"slider_oval_2_{i}_a"
                    tb = f"{prefix}_oval_{i}_b" if prefix == "slider" else f"slider_oval_2_{i}_b"
                    self._canvas.coords(ta, dx, yp + dy, bcr)
                    self._canvas.coords(tb, dx, yp + dy, bcr)
                self._canvas.coords(r1, 0, yp - bl / 2, width, yp + bl / 2)
                self._canvas.coords(r2, bcr, yp - bl / 2 - bcr, width - bcr, yp + bl / 2 + bcr)

        if rc:
            self._canvas.tag_raise("slider_parts")
        return rc


# -- CTkRangeSlider widget ---------------------------------------------------


class CTkRangeSlider(CTkBaseClass):
    """Range slider with two thumbs, theming, and variable support."""

    def __init__(
        self,
        master: object,
        width: int | None = None,
        height: int | None = None,
        corner_radius: int | None = None,
        button_corner_radius: int | None = None,
        border_width: int | None = None,
        button_length: int | None = None,
        bg_color: str | tuple[str, str] = "transparent",
        fg_color: str | tuple[str, str] | None = None,
        border_color: str | tuple[str, str] = "transparent",
        progress_color: str | tuple[str, str] | None = None,
        button_color: str | tuple[str, str] | None = None,
        button_hover_color: str | tuple[str, str] | None = None,
        from_: int = 0,
        to: int = 1,
        state: str = "normal",
        number_of_steps: int | None = None,
        *,
        hover: bool = True,
        command: Callable[[float], None] | tuple[Callable[[float], None], Callable[[float], None]] | None = None,
        variables: tuple[tk.Variable, tk.Variable] | None = None,
        orientation: str = "horizontal",
        **kwargs: object,
    ) -> None:
        if width is None:
            width = 16 if orientation.lower() == "vertical" else 200
        if height is None:
            height = 200 if orientation.lower() == "vertical" else 16

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        self._border_color = self._check_color_type(border_color, transparency=True)
        self._fg_color = (
            ThemeManager.theme["CTkSlider"]["fg_color"] if fg_color is None else self._check_color_type(fg_color)
        )
        self._progress_color = (
            ThemeManager.theme["CTkSlider"]["progress_color"]
            if progress_color is None
            else self._check_color_type(progress_color, transparency=True)
        )

        if button_color is None:
            self._button_color_0 = ThemeManager.theme["CTkSlider"]["button_color"]
            self._button_color_1 = ThemeManager.theme["CTkSlider"]["button_color"]
        elif isinstance(button_color, tuple) and len(button_color) == 2 and isinstance(button_color[0], tuple):  # noqa: PLR2004  # noqa: PLR2004
            self._button_color_0 = (
                ThemeManager.theme["CTkSlider"]["button_color"]
                if button_color[0] is None
                else self._check_color_type(button_color[0])
            )
            self._button_color_1 = (
                ThemeManager.theme["CTkSlider"]["button_color"]
                if button_color[1] is None
                else self._check_color_type(button_color[1])
            )
        else:
            self._button_color_0 = self._check_color_type(button_color)
            self._button_color_1 = self._check_color_type(button_color)

        self._button_hover_color = (
            ThemeManager.theme["CTkSlider"]["button_hover_color"]
            if button_hover_color is None
            else self._check_color_type(button_hover_color)
        )

        self._corner_radius = (
            ThemeManager.theme["CTkSlider"]["corner_radius"] if corner_radius is None else corner_radius
        )
        self._button_corner_radius = (
            ThemeManager.theme["CTkSlider"]["button_corner_radius"]
            if button_corner_radius is None
            else button_corner_radius
        )
        self._border_width = ThemeManager.theme["CTkSlider"]["border_width"] if border_width is None else border_width
        self._button_length = (
            ThemeManager.theme["CTkSlider"]["button_length"] if button_length is None else button_length
        )
        self._values: tuple[float, float] = (0.0, 1.0)
        self._orientation = orientation
        self._hover_states: tuple[bool, bool] = (False, False)
        self._hover = hover
        self._from_ = from_
        self._to = to
        self._number_of_steps = number_of_steps
        self._output_values: tuple[float, float] = (
            self._from_ + (self._values[0] * (self._to - self._from_)),
            self._from_ + (self._values[1] * (self._to - self._from_)),
        )
        self._active_slider: bool = True
        self._corner_radius = max(self._corner_radius, self._button_corner_radius)
        self._command = command
        self._variables: tuple[tk.Variable, ...] | None = variables
        self._variable_callback_blocked = False
        self._variable_callback_name: list[str | None] = [None, None]
        self._state = state

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._canvas = CTkCanvas(
            master=self,
            highlightthickness=0,
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._canvas.grid(column=0, row=0, rowspan=1, columnspan=1, sticky="nswe")
        self._draw_engine = CustomDrawEngine(self._canvas)
        self._create_bindings()
        self._set_cursor()
        self._draw()

        if self._variables is not None:
            self._variable_callback_name[0] = self._variables[0].trace_add("write", self._variable_callback)
            self._variable_callback_name[1] = self._variables[1].trace_add("write", self._variable_callback)
            self._variable_callback_blocked = True
            self.set([self._variables[0].get(), self._variables[1].get()], from_variable_callback=True)
            self._variable_callback_blocked = False

    def _create_bindings(self, sequence: str | None = None) -> None:
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Motion>":
            self._canvas.bind("<Motion>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self._canvas.bind("<Button-1>", self._clicked)
        if sequence is None or sequence == "<B1-Motion>":
            self._canvas.bind("<B1-Motion>", self._clicked)

    def _set_scaling(self, *args: object, **kwargs: object) -> None:
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw()

    def _set_dimensions(self, width: int | None = None, height: int | None = None) -> None:
        super()._set_dimensions(width, height)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw()

    def _destroy(self) -> None:
        if self._variables is not None:
            self._variables[0].trace_remove("write", self._variable_callback_name[0])
            self._variables[1].trace_remove("write", self._variable_callback_name[1])
        super().destroy()

    def _set_cursor(self) -> None:
        if self._state == "normal" and self._cursor_manipulation_enabled:
            if sys.platform == "darwin":
                self.configure(cursor="pointinghand")
            elif sys.platform.startswith("win"):
                self.configure(cursor="hand2")
        elif self._state == "disabled" and self._cursor_manipulation_enabled:
            if sys.platform == "darwin" or sys.platform.startswith("win"):
                self.configure(cursor="arrow")

    def _draw(self, *, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)
        orientation = "s" if self._orientation.lower() == "vertical" else "w"
        requires_recoloring = self._draw_engine.draw_rounded_slider_with_border_and_2_button(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            self._apply_widget_scaling(self._border_width),
            self._apply_widget_scaling(self._button_length),
            self._apply_widget_scaling(self._button_corner_radius),
            self._values[0],
            self._values[1],
            orientation,
        )
        if no_color_updates is False or requires_recoloring:
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            if self._border_color == "transparent":
                self._canvas.itemconfig(
                    "border_parts",
                    fill=self._apply_appearance_mode(self._bg_color),
                    outline=self._apply_appearance_mode(self._bg_color),
                )
            else:
                self._canvas.itemconfig(
                    "border_parts",
                    fill=self._apply_appearance_mode(self._border_color),
                    outline=self._apply_appearance_mode(self._border_color),
                )
            self._canvas.itemconfig(
                "inner_parts",
                fill=self._apply_appearance_mode(self._fg_color),
                outline=self._apply_appearance_mode(self._fg_color),
            )
            if self._progress_color == "transparent":
                self._canvas.itemconfig(
                    "progress_parts",
                    fill=self._apply_appearance_mode(self._fg_color),
                    outline=self._apply_appearance_mode(self._fg_color),
                )
            else:
                self._canvas.itemconfig(
                    "progress_parts",
                    fill=self._apply_appearance_mode(self._progress_color),
                    outline=self._apply_appearance_mode(self._progress_color),
                )
            c0 = self._button_hover_color if self._hover_states[0] and self._hover else self._button_color_0
            c1 = self._button_hover_color if self._hover_states[1] and self._hover else self._button_color_1
            self._canvas.itemconfig(
                "slider_0_parts", fill=self._apply_appearance_mode(c0), outline=self._apply_appearance_mode(c0)
            )
            self._canvas.itemconfig(
                "slider_1_parts", fill=self._apply_appearance_mode(c1), outline=self._apply_appearance_mode(c1)
            )

    def _clicked(self, event: object = None) -> None:
        if self._state != "normal":
            return
        if self._orientation.lower() == "horizontal":
            click_pos = self._reverse_widget_scaling(event.x / self._current_width)
        else:
            click_pos = 1 - self._reverse_widget_scaling(event.y / self._current_height)
        if click_pos < self._values[0] or abs(click_pos - self._values[0]) < abs(click_pos - self._values[1]):
            if self._active_slider:
                self._values = (click_pos, self._values[1])
        elif not self._active_slider:
            self._values = (self._values[0], click_pos)
        self._values = tuple(max(min(x, 1.0), 0.0) for x in self._values)
        self._output_values = (
            self._round_to_step_size(self._from_ + (self._values[0] * (self._to - self._from_))),
            self._round_to_step_size(self._from_ + (self._values[1] * (self._to - self._from_))),
        )
        self._values = (
            (self._output_values[0] - self._from_) / (self._to - self._from_),
            (self._output_values[1] - self._from_) / (self._to - self._from_),
        )
        self._draw(no_color_updates=False)
        if self._variables is not None:
            self._variable_callback_blocked = True
            self._variables[0].set(
                round(self._output_values[0]) if isinstance(self._variables[0], tk.IntVar) else self._output_values[0]
            )
            self._variables[1].set(
                round(self._output_values[1]) if isinstance(self._variables[1], tk.IntVar) else self._output_values[1]
            )
            self._variable_callback_blocked = False
        if self._command is not None:
            if isinstance(self._command, tuple):
                if self._active_slider:
                    self._command[0](self._output_values[0])
                else:
                    self._command[1](self._output_values[1])
            else:
                self._command(self._output_values)

    def _on_enter(self, event: object = None) -> None:
        if self._state != "normal":
            return
        if self._orientation.lower() == "horizontal":
            pos = self._reverse_widget_scaling(event.x / self._current_width)
        else:
            pos = 1 - self._reverse_widget_scaling(event.y / self._current_height)
        if pos < self._values[0] or abs(pos - self._values[0]) <= abs(pos - self._values[1]):
            ht, nt, c = "slider_0_parts", "slider_1_parts", self._button_color_1
            self._hover_states = (True, False)
            self._active_slider = True
        else:
            ht, nt, c = "slider_1_parts", "slider_0_parts", self._button_color_0
            self._hover_states = (False, True)
            self._active_slider = False
        if self._hover:
            self._canvas.itemconfig(
                ht,
                fill=self._apply_appearance_mode(self._button_hover_color),
                outline=self._apply_appearance_mode(self._button_hover_color),
            )
        self._canvas.itemconfig(nt, fill=self._apply_appearance_mode(c), outline=self._apply_appearance_mode(c))

    def _on_leave(self, _event: object = None) -> None:
        self._hover_states = (False, False)
        self._canvas.itemconfig(
            "slider_0_parts",
            fill=self._apply_appearance_mode(self._button_color_0),
            outline=self._apply_appearance_mode(self._button_color_0),
        )
        self._canvas.itemconfig(
            "slider_1_parts",
            fill=self._apply_appearance_mode(self._button_color_1),
            outline=self._apply_appearance_mode(self._button_color_1),
        )

    def _round_to_step_size(self, values):
        if self._number_of_steps is not None:
            step_size = (self._to - self._from_) / self._number_of_steps
            if isinstance(values, list):
                return [self._to - (round((self._to - x) / step_size) * step_size) for x in values]
            return self._to - (round((self._to - values) / step_size) * step_size)
        return values

    def get(self) -> tuple[float, float]:
        return self._output_values

    def set(self, output_values: list[float], *, from_variable_callback: bool = False) -> None:
        if self._from_ < self._to:
            output_values = [max(min(x, self._to), self._from_) for x in output_values]
        else:
            output_values = [max(min(x, self._from_), self._to) for x in output_values]
        self._output_values = self._round_to_step_size(output_values)
        if (self._to - self._from_) != 0:
            self._values = (
                (self._output_values[0] - self._from_) / (self._to - self._from_),
                (self._output_values[1] - self._from_) / (self._to - self._from_),
            )
        else:
            self._values = (0.0, 1.0)
        self._draw(no_color_updates=False)
        if self._variables is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variables[0].set(
                round(self._output_values[0]) if isinstance(self._variables[0], tk.IntVar) else self._output_values[0]
            )
            self._variables[1].set(
                round(self._output_values[1]) if isinstance(self._variables[1], tk.IntVar) else self._output_values[1]
            )
            self._variable_callback_blocked = False

    def _variable_callback(self, _var_name: str, _index: str, _mode: str) -> None:
        if not self._variable_callback_blocked:
            self.set([self._variables[0].get(), self._variables[1].get()], from_variable_callback=True)

    def bind(self, sequence: str | None = None, command: Callable | None = None, *, add: str | bool = True) -> None:
        if not (add == "+" or add is True):
            msg = "'add' argument can only be '+' or True to preserve internal callbacks"
            raise ValueError(msg)
        self._canvas.bind(sequence, command, add=True)

    def unbind(self, sequence: str | None = None, funcid: str | None = None) -> None:
        if funcid is not None:
            msg = "'funcid' argument can only be None, because there is a bug in tkinter"
            raise ValueError(msg)
        self._canvas.unbind(sequence, None)
        self._create_bindings(sequence=sequence)

    def configure(self, *, require_redraw: bool = False, **kwargs: object) -> None:
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True
        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True
        if "progress_color" in kwargs:
            self._progress_color = self._check_color_type(kwargs.pop("progress_color"), transparency=True)
            require_redraw = True
        if "button_color" in kwargs:
            self._button_color_0 = self._check_color_type(kwargs["button_color"])
            self._button_color_1 = self._check_color_type(kwargs.pop("button_color"))
            require_redraw = True
        if "button_hover_color" in kwargs:
            self._button_hover_color = self._check_color_type(kwargs.pop("button_hover_color"))
            require_redraw = True
        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"), transparency=True)
            require_redraw = True
        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            require_redraw = True
        if "from_" in kwargs:
            self._from_ = kwargs.pop("from_")
        if "to" in kwargs:
            self._to = kwargs.pop("to")
        if "number_of_steps" in kwargs:
            self._number_of_steps = kwargs.pop("number_of_steps")
        if "hover" in kwargs:
            self._hover = kwargs.pop("hover")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "variables" in kwargs:
            if self._variables is not None:
                self._variables[0].trace_remove("write", self._variable_callback_name[0])
                self._variables[1].trace_remove("write", self._variable_callback_name[1])
            self._variables = kwargs.pop("variables")
            if self._variables is not None and self._variables != "":
                self._variable_callback_name[0] = self._variables[0].trace_add("write", self._variable_callback)
                self._variable_callback_name[1] = self._variables[1].trace_add("write", self._variable_callback)
                self.set([self._variables[0].get(), self._variables[1].get()], from_variable_callback=True)
            else:
                self._variables = None
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True
        if "button_corner_radius" in kwargs:
            self._button_corner_radius = kwargs.pop("button_corner_radius")
            require_redraw = True
        if "button_length" in kwargs:
            self._button_length = kwargs.pop("button_length")
            require_redraw = True
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> object:
        attr_map = {
            "corner_radius": self._corner_radius,
            "button_corner_radius": self._button_corner_radius,
            "border_width": self._border_width,
            "button_length": self._button_length,
            "fg_color": self._fg_color,
            "border_color": self._border_color,
            "progress_color": self._progress_color,
            "button_color": self._button_color_0,
            "button_hover_color": self._button_hover_color,
            "from_": self._from_,
            "to": self._to,
            "state": self._state,
            "number_of_steps": self._number_of_steps,
            "hover": self._hover,
            "command": self._command,
            "variables": self._variables,
            "orientation": self._orientation,
        }
        if attribute_name in attr_map:
            return attr_map[attribute_name]
        return super().cget(attribute_name)

    def focus(self) -> bool:
        return self._canvas.focus()

    def focus_set(self) -> None:
        return self._canvas.focus_set()

    def focus_force(self) -> None:
        return self._canvas.focus_force()
