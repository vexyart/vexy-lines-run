# mypy: disable-error-code="attr-defined"
# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false, reportPrivateUsage=false, reportAttributeAccessIssue=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnnecessaryComparison=false
# this_file: src/vexy_lines_run/handlers.py
"""Handler mixin — file CRUD, preview updates, resize, format/size/audio state."""

from __future__ import annotations

import contextlib
import io
import tkinter as tk
from collections.abc import Callable, Collection
from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING

import customtkinter
from PIL import Image

from vexy_lines_run.helpers import (
    IMAGE_EXTENSIONS,
    LINES_EXTENSIONS,
    MIN_TRUNCATE_CHARS,
    VIDEO_EXTENSIONS,
    extract_frame,
    extract_preview_from_lines,
    fit_image_to_box,
    truncate_start,
)

if TYPE_CHECKING:
    from vexy_lines_run.app import App


class AppHandlersMixin:
    """Handles all CRUD operations, preview rendering, resize logic, and state updates.

    Mixed into :class:`App`; every method accesses ``self`` as an ``App`` instance.
    """

    # -- type narrowing for IDE support --
    if TYPE_CHECKING:
        self: App  # type: ignore[misc]

    # ── shared helpers ────────────────────────────────────────────────────

    def _set_label_image(
        self,
        label: customtkinter.CTkLabel,
        image: Image.Image | None,
        width: int,
        height: int,
        placeholder: str = "",
    ) -> None:
        if image is None:
            label.configure(image=None, text=placeholder)
            # CustomTkinter bug: configure(image=None) unsets label._image but doesn't
            # pass image="" to the underlying tkinter.Label, so the tk widget keeps
            # a reference to the PhotoImage. If it gets garbage collected, tk throws
            # TclError: image "pyimageN" doesn't exist when it tries to redraw.
            if hasattr(label, "_label"):
                label._label.configure(image="")
            label._image = None
            return

        fitted = fit_image_to_box(image, width, height)
        ctk_img = customtkinter.CTkImage(light_image=fitted, dark_image=fitted, size=fitted.size)
        label.configure(image=ctk_img, text="", fg_color="transparent")
        label._image = ctk_img

    def _truncate_start_for_width(self, path: str, width_px: int) -> str:
        if self._font.measure(path) <= width_px:
            return path
        avg = self._font.measure("x") or 7
        return truncate_start(path, max(MIN_TRUNCATE_CHARS, width_px // avg))

    def _add_valid_unique_paths(
        self,
        incoming_paths: list[str],
        current_paths: list[str],
        valid_extensions: Collection[str],
    ) -> bool:
        changed = False
        for path in incoming_paths:
            if Path(path).suffix.lower() in valid_extensions and path not in current_paths:
                current_paths.append(path)
                changed = True
        return changed

    def _select_first_index_if_needed(self, paths: list[str], selected_index: int | None) -> int | None:
        if selected_index is None and paths:
            return 0
        return selected_index

    def _repair_selection_after_delete(self, paths: list[str], selected_index: int | None) -> int | None:
        if not paths:
            return None
        if selected_index is None:
            return None
        return min(selected_index, len(paths) - 1)

    def _normalized_selected_index(self, paths: list[str], selected_index: int | None) -> int | None:
        if not paths:
            return None
        if selected_index is None or not (0 <= selected_index < len(paths)):
            return 0
        return selected_index

    def _remove_selected_path(self, paths: list[str], selected_index: int | None) -> tuple[bool, int | None]:
        if selected_index is None or not (0 <= selected_index < len(paths)):
            return False, selected_index
        del paths[selected_index]
        return True, self._repair_selection_after_delete(paths, selected_index)

    def _reset_list_rows(self, rows: list[customtkinter.CTkBaseClass]) -> None:
        for row in rows:
            row.destroy()
        rows.clear()

    def _rebuild_path_list_rows(
        self,
        parent: customtkinter.CTkFrame,
        rows: list[customtkinter.CTkBaseClass],
        paths: list[str],
        placeholder_text: str,
        on_select: Callable[[int], None],
    ) -> None:
        self._reset_list_rows(rows)
        width_px = max(10, parent.winfo_width() - 24)
        if not paths:
            placeholder = customtkinter.CTkLabel(
                parent,
                text=placeholder_text,
                font=(self._font.actual("family"), 12, "italic"),
                text_color=("#888888", "#777777"),
            )
            placeholder.pack(expand=True, pady=40)
            rows.append(placeholder)
            return
        for index, path in enumerate(paths):
            row = customtkinter.CTkButton(
                parent,
                text=self._truncate_start_for_width(path, width_px),
                anchor="w",
                corner_radius=6,
                fg_color=("#e9e9e9", "#2a2a2a"),
                text_color=("black", "white"),
                hover_color=("#d0d0d0", "#3a3a3a"),
                command=lambda idx=index: on_select(idx),
            )
            row.pack(fill="x", padx=2, pady=2)
            rows.append(row)

    def _style_selected_rows(self, rows: list[customtkinter.CTkBaseClass], selected_index: int | None) -> None:
        for index, row in enumerate(rows):
            if index == selected_index:
                row.configure(fg_color=("#3B8ED0", "#1F6AA5"), hover_color=("#2974A5", "#144C78"))
            else:
                row.configure(fg_color=("#e9e9e9", "#2a2a2a"), hover_color=("#d0d0d0", "#3a3a3a"))

    # ── resize ────────────────────────────────────────────────────────────

    def _on_resize(self, event: tk.Event) -> None:
        if event.widget is not self:
            return
        w = self.winfo_width()
        h = self.winfo_height()
        if abs(w - self._last_width) <= 5 and abs(h - self._last_height) <= 5:
            return
        self._last_width = w
        self._last_height = h
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(70, self._resize_refresh)

    def _resize_refresh(self) -> None:
        self._resize_job: str | None = None
        self._refresh_image_list()
        self._refresh_lines_list()
        self._retruncate_labels()
        self._redraw_images_preview()
        self._redraw_lines_preview()
        self._redraw_video_previews()
        self._set_style_preview_image("start")
        self._set_style_preview_image("end")
        if self._is_exporting:
            self._redraw_export_preview()

    def _retruncate_labels(self) -> None:
        if self._video_path:
            wpx = max(10, self.video_path_label.winfo_width() - 10)
            self.video_path_label.configure(text=self._truncate_start_for_width(self._video_path, wpx))
        for key in ("start", "end"):
            if p := self._style_paths.get(key):
                lbl = self._style_labels[key]
                wpx = max(10, lbl.winfo_width() - 10)
                lbl.configure(text=self._truncate_start_for_width(p, wpx))

    # ── lines CRUD ────────────────────────────────────────────────────────

    def _choose_lines(self) -> None:
        files = filedialog.askopenfilenames(
            title="Choose .lines files", filetypes=[("Vexy Lines", "*.lines"), ("All files", "*.*")]
        )
        if files:
            self._add_lines(list(files))

    def _add_lines(self, paths: list[str]) -> None:
        if not self._add_valid_unique_paths(paths, self._lines_paths, LINES_EXTENSIONS):
            return
        self._selected_lines_index = self._select_first_index_if_needed(self._lines_paths, self._selected_lines_index)
        self._refresh_lines_list()
        self._update_lines_preview()

    def _remove_selected_lines(self) -> None:
        removed, self._selected_lines_index = self._remove_selected_path(self._lines_paths, self._selected_lines_index)
        if not removed:
            return
        self._refresh_lines_list()
        self._update_lines_preview()

    def _clear_all_lines(self) -> None:
        self._lines_paths.clear()
        self._selected_lines_index: int | None = None
        self._refresh_lines_list()
        self._update_lines_preview()

    def _refresh_lines_list(self) -> None:
        self._rebuild_path_list_rows(
            self.lines_list_frame,
            self._lines_rows,
            self._lines_paths,
            self._lines_hint,
            self._select_lines_row,
        )
        if self._lines_paths:
            self._update_lines_row_styles()

    def _select_lines_row(self, index: int) -> None:
        if 0 <= index < len(self._lines_paths):
            self._selected_lines_index = index
            self._update_lines_row_styles()
            self._update_lines_preview()

    def _update_lines_row_styles(self) -> None:
        self._style_selected_rows(self._lines_rows, self._selected_lines_index)

    def _update_lines_preview(self) -> None:
        index = self._normalized_selected_index(self._lines_paths, self._selected_lines_index)
        if index is None:
            self._lines_raw_image = None
        else:
            self._selected_lines_index = index
            if pb := extract_preview_from_lines(self._lines_paths[index]):
                self._lines_raw_image = Image.open(io.BytesIO(pb))
            else:
                self._lines_raw_image = None
        self._redraw_lines_preview()

    def _redraw_lines_preview(self) -> None:
        w = max(10, self.lines_preview_container.winfo_width())
        h = max(10, self.lines_preview_container.winfo_height())
        self._set_label_image(self.lines_preview_label, self._lines_raw_image, w, h, placeholder=self._lines_hint)

    def _on_lines_drop(self, event: tk.Event) -> None:
        if data := getattr(event, "data", ""):
            self._add_lines(self._parse_drop_data(data))

    # ── images CRUD ───────────────────────────────────────────────────────

    def _choose_images(self) -> None:
        files = filedialog.askopenfilenames(
            title="Choose images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp"), ("All files", "*.*")],
        )
        if files:
            self._add_images(list(files))

    def _add_images(self, paths: list[str]) -> None:
        if not self._add_valid_unique_paths(paths, self._image_paths, IMAGE_EXTENSIONS):
            return
        self._selected_image_index = self._select_first_index_if_needed(self._image_paths, self._selected_image_index)
        self._refresh_image_list()
        self._update_images_preview()

    def _remove_selected_image(self) -> None:
        removed, self._selected_image_index = self._remove_selected_path(self._image_paths, self._selected_image_index)
        if not removed:
            return
        self._refresh_image_list()
        self._update_images_preview()

    def _clear_all_images(self) -> None:
        self._image_paths.clear()
        self._selected_image_index: int | None = None
        self._refresh_image_list()
        self._update_images_preview()

    def _refresh_image_list(self) -> None:
        self._rebuild_path_list_rows(
            self.images_list_frame,
            self._image_rows,
            self._image_paths,
            self._images_hint,
            self._select_image_row,
        )
        if self._image_paths:
            self._update_image_row_styles()

    def _select_image_row(self, index: int) -> None:
        if 0 <= index < len(self._image_paths):
            self._selected_image_index = index
            self._update_image_row_styles()
            self._update_images_preview()

    def _update_image_row_styles(self) -> None:
        self._style_selected_rows(self._image_rows, self._selected_image_index)

    def _update_images_preview(self) -> None:
        index = self._normalized_selected_index(self._image_paths, self._selected_image_index)
        if index is None:
            self._images_raw_image = None
        else:
            self._selected_image_index = index
            # Reset before attempting open so stale images never survive a suppressed failure
            self._images_raw_image = None
            with contextlib.suppress(OSError, ValueError):
                self._images_raw_image = Image.open(self._image_paths[index]).convert("RGB")
        self._redraw_images_preview()

    def _redraw_images_preview(self) -> None:
        w = max(10, self.images_preview_container.winfo_width())
        h = max(10, self.images_preview_container.winfo_height())
        self._set_label_image(self.images_preview_label, self._images_raw_image, w, h, placeholder=self._images_hint)

    def _on_images_drop(self, event: tk.Event) -> None:
        if data := getattr(event, "data", ""):
            self._add_images(self._parse_drop_data(data))

    # ── video CRUD ────────────────────────────────────────────────────────

    def _choose_video(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose video", filetypes=[("Videos", "*.mp4 *.mov *.avi *.mkv *.webm"), ("All files", "*.*")]
        )
        if path:
            self._apply_video_path(path)

    def _on_video_drop(self, event: tk.Event) -> None:
        if data := getattr(event, "data", ""):
            if dropped := self._parse_drop_data(data):
                self._apply_video_path(dropped[0])

    def _apply_video_path(self, path: str) -> None:
        if Path(path).suffix.lower() not in VIDEO_EXTENSIONS:
            return
        total = self._get_video_frame_count(path)
        if total <= 0:
            return
        self._video_path = path
        self.video_path_label.configure(
            text=self._truncate_start_for_width(path, max(10, self.video_path_label.winfo_width() - 10))
        )
        self._video_total_frames = total
        self._video_has_audio = self._probe_video_audio(path)
        self._set_video_range(1, total)
        self._update_audio_toggle_visibility()

    def _get_video_frame_count(self, path: str) -> int:
        """Return total frame count for *path*, or 0 on failure."""
        try:
            from vexy_lines_api.video import probe

            info = probe(path)
            return info.total_frames
        except Exception:
            return 0

    def _probe_video_audio(self, path: str) -> bool:
        """Check whether a video file contains an audio track."""
        try:
            from vexy_lines_api.video import probe

            return probe(path).has_audio
        except Exception:
            return True

    def _clear_video(self) -> None:
        self._video_path = ""
        self._video_total_frames = 0
        self._video_has_audio = False
        self._video_range = (1, 1)
        self.video_path_label.configure(text="")
        self.video_start_entry.delete(0, "end")
        self.video_start_entry.insert(0, "1")
        self.video_end_entry.delete(0, "end")
        self.video_end_entry.insert(0, "1")
        self.video_count_label.configure(text="0 frames")
        self._syncing_video_controls = True
        self.video_range_slider.configure(from_=0, to=1)
        self.video_range_slider.set([0, 1])
        self._syncing_video_controls = False
        self._video_first_raw_image = None
        self._video_last_raw_image = None
        self._redraw_video_previews()
        self._update_audio_toggle_visibility()

    def _on_video_slider_change(self, values: tuple[float, float] | list[float] | None) -> None:
        if not self._syncing_video_controls and values is not None and self._video_total_frames > 0:
            self._set_video_range(round(values[0]), round(values[1]))

    def _on_video_entries_submit(self, _event: tk.Event | None) -> None:
        if self._video_total_frames <= 0:
            return
        try:
            lo, hi = int(self.video_start_entry.get().strip()), int(self.video_end_entry.get().strip())
        except ValueError:
            lo, hi = self._video_range
        self._set_video_range(lo, hi)

    def _set_video_range(self, low: int, high: int) -> None:
        if self._video_total_frames <= 0:
            return
        low = max(1, min(low, self._video_total_frames))
        high = max(1, min(high, self._video_total_frames))
        if low > high:
            low, high = high, low
        self._video_range = (low, high)
        self._syncing_video_controls = True
        self.video_range_slider.configure(from_=1, to=self._video_total_frames)
        self.video_range_slider.set([low, high])
        self._syncing_video_controls = False
        self.video_start_entry.delete(0, "end")
        self.video_start_entry.insert(0, str(low))
        self.video_end_entry.delete(0, "end")
        self.video_end_entry.insert(0, str(high))
        self.video_count_label.configure(text=f"{high - low + 1} frames")
        self._update_video_previews()
        self._update_audio_toggle_visibility()

    def _update_video_previews(self) -> None:
        if not self._video_path or self._video_total_frames <= 0:
            self._video_first_raw_image = None
            self._video_last_raw_image = None
        else:
            lo, hi = self._video_range
            self._video_first_raw_image = extract_frame(self._video_path, lo)
            self._video_last_raw_image = extract_frame(self._video_path, hi)
        self._redraw_video_previews()

    def _redraw_video_previews(self) -> None:
        w1 = max(10, self.video_first_preview_container.winfo_width())
        h1 = max(10, self.video_first_preview_container.winfo_height())
        self._set_label_image(
            self.video_first_preview, self._video_first_raw_image, w1, h1, placeholder=self._video_hint
        )

        w2 = max(10, self.video_last_preview_container.winfo_width())
        h2 = max(10, self.video_last_preview_container.winfo_height())
        self._set_label_image(self.video_last_preview, self._video_last_raw_image, w2, h2)

    # ── format / size / audio ─────────────────────────────────────────────

    def _on_format_change(self, _value: str) -> None:
        self._update_size_dropdown_state()
        self._update_audio_toggle_visibility()

    def _update_size_dropdown_state(self) -> None:
        fmt = self.format_var.get()
        if fmt in ("SVG", "LINES"):
            self.size_var.set("\u2014")
            self.size_menu.configure(values=["\u2014"], state="disabled")
            return
        valid = ["1x", "2x", "3x", "4x"]
        cur = self.size_var.get()
        self.size_menu.configure(values=valid, state="normal")
        self.size_var.set(cur if cur in valid else "1x")

    def _update_audio_toggle_visibility(self) -> None:
        vid = self.inputs_tabview.get() == "Video"
        loaded = bool(self._video_path and self._video_total_frames > 0)
        mp4 = self.format_var.get() == "MP4"
        full = self._video_total_frames > 0 and self._video_range == (1, self._video_total_frames)
        if vid and loaded and self._video_has_audio and mp4 and full:
            self.audio_toggle.pack(side="left", padx=(0, 8), pady=10)
        else:
            self.audio_toggle.pack_forget()

    # ── menu shortcut helpers ─────────────────────────────────────────────

    def _reset_video_range(self) -> None:
        if self._video_total_frames > 0:
            self._set_video_range(1, self._video_total_frames)

    def _clear_all_styles(self) -> None:
        self._clear_style_file("start")
        self._clear_style_file("end")

    def _set_format(self, fmt: str) -> None:
        self.format_var.set(fmt)
        self._on_format_change(fmt)

    def _set_size(self, size: str) -> None:
        self.size_var.set(size)

    def _poll_active_tab(self) -> None:
        self._update_audio_toggle_visibility()
        self.after(300, self._poll_active_tab)
