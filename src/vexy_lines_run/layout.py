# this_file: src/vexy_lines_run/layout.py
"""Layout mixin — menu bar, tabs, panels, and drag-and-drop registration."""

from __future__ import annotations

import contextlib
import re
import tkinter as tk
from typing import TYPE_CHECKING

import customtkinter
from CTkMenuBarPlus import CTkMenuBar, CustomDropdownMenu

from vexy_lines_run.widgets import CTkRangeSlider

if TYPE_CHECKING:
    from vexy_lines_run.app import App

try:
    from CTkToolTip import CTkToolTip
except ImportError:
    CTkToolTip = None  # type: ignore[assignment,misc]

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except (ImportError, RuntimeError):
    TkinterDnD = None  # type: ignore[assignment,misc]
    DND_FILES = None


class AppLayoutMixin:
    """Builds all widgets and registers drag-and-drop targets.

    Mixed into :class:`App`; every method accesses ``self`` as an ``App`` instance.
    """

    # -- type narrowing for IDE support --
    if TYPE_CHECKING:
        self: App  # type: ignore[assignment]

    def add_ctk_tooltip(self, widget: tk.Widget, message: str) -> None:
        """Add a tooltip to a widget if library is available. Handles CTk widgets that don't support bind."""
        if CTkToolTip is None:
            return
        with contextlib.suppress(NotImplementedError, tk.TclError):
            CTkToolTip(widget, message=message, delay=0.2, follow=True, x_offset=20, y_offset=10, alpha=0.95)

    def _build_layout(self) -> None:
        self._build_menu_bar()
        root = customtkinter.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=12, pady=12)
        root.grid_columnconfigure(0, weight=2, uniform="a")
        root.grid_columnconfigure(1, weight=1, uniform="a")
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=0)

        self.content_frame = customtkinter.CTkFrame(root, fg_color="transparent")
        self.content_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=2, uniform="a")
        self.content_frame.grid_columnconfigure(1, weight=1, uniform="a")
        self.content_frame.grid_rowconfigure(0, weight=1)

        self.preview_frame = customtkinter.CTkFrame(root, fg_color="transparent")
        self.preview_label = customtkinter.CTkLabel(self.preview_frame, text="")
        self.preview_label.pack(fill="both", expand=True)

        self._build_inputs_panel(self.content_frame)
        self._build_styles_panel(self.content_frame)
        self._build_outputs_section(root)

    def _build_menu_bar(self) -> None:
        menu_bar = CTkMenuBar(self)
        file_btn = menu_bar.add_cascade("File")
        menu_font = file_btn.cget("font")

        file_menu = CustomDropdownMenu(widget=file_btn, font=menu_font)
        file_menu.add_option("Add Lines\u2026", command=self._menu_add_lines, font=menu_font)
        file_menu.add_separator()
        file_menu.add_option("Export \u25b6", command=self._do_export, font=menu_font)
        file_menu.add_option("Stop", command=self._stop_export, font=menu_font)
        file_menu.add_separator()
        file_menu.add_option("Quit", command=self.destroy, accelerator="CmdOrCtrl+Q", font=menu_font)

        lines_btn = menu_bar.add_cascade("Lines", font=menu_font)
        lines_menu = CustomDropdownMenu(widget=lines_btn, font=menu_font)
        lines_menu.add_option("Add Lines\u2026", command=self._menu_add_lines, font=menu_font)
        lines_menu.add_option("Remove Selected", command=self._remove_selected_lines, font=menu_font)
        lines_menu.add_option("Remove All Lines", command=self._clear_all_lines, font=menu_font)

        image_btn = menu_bar.add_cascade("Image", font=menu_font)
        image_menu = CustomDropdownMenu(widget=image_btn, font=menu_font)
        image_menu.add_option("Add Images\u2026", command=self._menu_add_images, font=menu_font)
        image_menu.add_option("Remove Selected", command=self._remove_selected_image, font=menu_font)
        image_menu.add_option("Remove All Images", command=self._clear_all_images, font=menu_font)

        video_btn = menu_bar.add_cascade("Video", font=menu_font)
        video_menu = CustomDropdownMenu(widget=video_btn, font=menu_font)
        video_menu.add_option("Add Video\u2026", command=self._menu_add_video, font=menu_font)
        video_menu.add_option("Reset Range", command=self._reset_video_range, font=menu_font)
        video_menu.add_option("Remove Video", command=self._clear_video, font=menu_font)

        style_btn = menu_bar.add_cascade("Style", font=menu_font)
        style_menu = CustomDropdownMenu(widget=style_btn, font=menu_font)
        style_menu.add_option("Open Style\u2026", command=lambda: self._choose_style_file("start"), font=menu_font)
        style_menu.add_option("Open End Style\u2026", command=lambda: self._choose_style_file("end"), font=menu_font)
        style_menu.add_option("Reset Styles", command=self._clear_all_styles, font=menu_font)

        export_btn = menu_bar.add_cascade("Export", font=menu_font)
        export_menu = CustomDropdownMenu(widget=export_btn, font=menu_font)
        export_menu.add_option("Export \u25b6", command=self._do_export, font=menu_font)
        export_menu.add_option("Stop", command=self._stop_export, font=menu_font)
        export_menu.add_separator()
        export_menu.add_option("Location\u2026", command=self._choose_output_path, font=menu_font)
        fmt_sub = export_menu.add_submenu("Format", font=menu_font)
        for fmt in ("SVG", "PNG", "JPG", "MP4", "LINES"):
            fmt_sub.add_option(fmt, command=lambda f=fmt: self._set_format(f), font=menu_font)
        size_sub = export_menu.add_submenu("Size", font=menu_font)
        for sz in ("1x", "2x", "3x", "4x"):
            size_sub.add_option(sz, command=lambda s=sz: self._set_size(s), font=menu_font)
        audio_sub = export_menu.add_submenu("Audio", font=menu_font)
        audio_sub.add_option("On", command=lambda: self.audio_var.set(True), font=menu_font)
        audio_sub.add_option("Off", command=lambda: self.audio_var.set(False), font=menu_font)

    def _menu_add_lines(self) -> None:
        self.inputs_tabview.set("Lines")
        self._on_inputs_tab_changed("Lines")
        self._choose_lines()

    def _menu_add_images(self) -> None:
        self.inputs_tabview.set("Images")
        self._on_inputs_tab_changed("Images")
        self._choose_images()

    def _menu_add_video(self) -> None:
        self.inputs_tabview.set("Video")
        self._on_inputs_tab_changed("Video")
        self._choose_video()

    def _build_inputs_panel(self, parent: customtkinter.CTkFrame) -> None:
        self.inputs_tabview = customtkinter.CTkTabview(parent)
        self.inputs_tabview.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 10))

        lines_tab = self.inputs_tabview.add("Lines")
        images_tab = self.inputs_tabview.add("Images")
        video_tab = self.inputs_tabview.add("Video")
        self._build_lines_tab(lines_tab)
        self._build_images_tab(images_tab)
        self._build_video_tab(video_tab)
        self._install_tab_change_hook()

    def _build_lines_tab(self, tab: customtkinter.CTkFrame) -> None:
        content = customtkinter.CTkFrame(tab)
        content.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        content.grid_columnconfigure(0, weight=1, uniform="half")
        content.grid_columnconfigure(1, weight=1, uniform="half")
        content.grid_rowconfigure(0, weight=1)
        self.lines_list_frame = customtkinter.CTkScrollableFrame(content)
        self.lines_list_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=(10, 8))

        self.lines_preview_container = customtkinter.CTkFrame(content, fg_color="transparent")
        self.lines_preview_container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(10, 8))
        self.lines_preview_container.grid_propagate(False)
        self.lines_preview_container.grid_rowconfigure(0, weight=1)
        self.lines_preview_container.grid_columnconfigure(0, weight=1)

        _lines_hint = "Drop lines here" if self._has_dnd else "Click: Add Lines"
        self.lines_preview_label = customtkinter.CTkLabel(self.lines_preview_container, text=_lines_hint)
        self.lines_preview_label.grid(row=0, column=0, sticky="nwe")

        self._update_lines_preview()
        self._refresh_lines_list()
        controls = customtkinter.CTkFrame(tab)
        controls.pack(fill="x", expand=False, side="bottom", padx=8, pady=(0, 8))
        add_lines_btn = customtkinter.CTkButton(controls, text="Add Lines\u2026", command=self._choose_lines)
        add_lines_btn.pack(side="left", padx=(8, 0), pady=8)
        self.add_ctk_tooltip(add_lines_btn, "Import vector lines from files")

        rm_lines_btn = customtkinter.CTkButton(controls, text="\u2212", width=36, command=self._remove_selected_lines)
        rm_lines_btn.pack(side="left", padx=6, pady=8)
        self.add_ctk_tooltip(rm_lines_btn, "Remove selected line file from list")

        clear_lines_btn = customtkinter.CTkButton(controls, text="\u2715", width=36, command=self._clear_all_lines)
        clear_lines_btn.pack(side="right", padx=(0, 8), pady=8)
        self.add_ctk_tooltip(clear_lines_btn, "Clear all line files from list")

    def _build_images_tab(self, tab: customtkinter.CTkFrame) -> None:
        content = customtkinter.CTkFrame(tab)
        content.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        content.grid_columnconfigure(0, weight=1, uniform="half")
        content.grid_columnconfigure(1, weight=1, uniform="half")
        content.grid_rowconfigure(0, weight=1)
        self.images_list_frame = customtkinter.CTkScrollableFrame(content)
        self.images_list_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=(10, 8))

        self.images_preview_container = customtkinter.CTkFrame(content, fg_color="transparent")
        self.images_preview_container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(10, 8))
        self.images_preview_container.grid_propagate(False)
        self.images_preview_container.grid_rowconfigure(0, weight=1)
        self.images_preview_container.grid_columnconfigure(0, weight=1)

        _images_hint = "Drop images here" if self._has_dnd else "Click: Add Images"
        self.images_preview_label = customtkinter.CTkLabel(self.images_preview_container, text=_images_hint)
        self.images_preview_label.grid(row=0, column=0, sticky="nwe")

        self._update_images_preview()
        self._refresh_image_list()
        controls = customtkinter.CTkFrame(tab)
        controls.pack(fill="x", expand=False, side="bottom", padx=8, pady=(0, 8))
        add_images_btn = customtkinter.CTkButton(controls, text="Add Images\u2026", command=self._choose_images)
        add_images_btn.pack(side="left", padx=(8, 0), pady=8)
        self.add_ctk_tooltip(add_images_btn, "Import raster images to process")

        rm_images_btn = customtkinter.CTkButton(controls, text="\u2212", width=36, command=self._remove_selected_image)
        rm_images_btn.pack(side="left", padx=6, pady=8)
        self.add_ctk_tooltip(rm_images_btn, "Remove selected image from list")

        clear_images_btn = customtkinter.CTkButton(controls, text="\u2715", width=36, command=self._clear_all_images)
        clear_images_btn.pack(side="right", padx=(0, 8), pady=8)
        self.add_ctk_tooltip(clear_images_btn, "Clear all images from list")

    def _build_video_tab(self, tab: customtkinter.CTkFrame) -> None:
        previews = customtkinter.CTkFrame(tab)
        previews.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        previews.grid_columnconfigure(0, weight=1, uniform="half")
        previews.grid_columnconfigure(1, weight=1, uniform="half")
        previews.grid_rowconfigure(0, weight=1)

        self.video_first_preview_container = customtkinter.CTkFrame(previews, fg_color="transparent")
        self.video_first_preview_container.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=(10, 8))
        self.video_first_preview_container.grid_propagate(False)
        self.video_first_preview_container.grid_rowconfigure(0, weight=1)
        self.video_first_preview_container.grid_columnconfigure(0, weight=1)

        _video_hint = "Drop video here" if self._has_dnd else "Click: Open Video"
        self.video_first_preview = customtkinter.CTkLabel(self.video_first_preview_container, text=_video_hint)
        self.video_first_preview.grid(row=0, column=0, sticky="nwe")

        self.video_last_preview_container = customtkinter.CTkFrame(previews, fg_color="transparent")
        self.video_last_preview_container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(10, 8))
        self.video_last_preview_container.grid_propagate(False)
        self.video_last_preview_container.grid_rowconfigure(0, weight=1)
        self.video_last_preview_container.grid_columnconfigure(0, weight=1)

        self.video_last_preview = customtkinter.CTkLabel(self.video_last_preview_container, text="")
        self.video_last_preview.grid(row=0, column=0, sticky="nwe")

        self._update_video_previews()
        controls = customtkinter.CTkFrame(tab)
        controls.pack(fill="x", expand=False, side="bottom", padx=8, pady=(0, 8))
        range_row = customtkinter.CTkFrame(controls, fg_color="transparent")
        range_row.pack(fill="x", padx=8, pady=(8, 4))
        self.video_start_entry = customtkinter.CTkEntry(range_row, width=60)
        self.video_start_entry.pack(side="left")
        self.video_start_entry.insert(0, "1")
        self.video_start_entry.bind("<Return>", self._on_video_entries_submit)
        self.video_start_entry.bind("<FocusOut>", self._on_video_entries_submit)
        self.add_ctk_tooltip(self.video_start_entry, "Start frame index for export")

        def _range_change_cmd(values: tuple[float, float] | float) -> None:
            if isinstance(values, (list, tuple)):
                self._on_video_slider_change(values)

        self.video_range_slider = CTkRangeSlider(range_row, from_=0, to=1, command=_range_change_cmd)
        self.video_range_slider.pack(side="left", fill="x", expand=True, padx=8)
        self.video_range_slider.set([0, 1])
        self.add_ctk_tooltip(self.video_range_slider, "Slide to select frame range")
        self.video_count_label = customtkinter.CTkLabel(range_row, text="0 frames")
        self.video_count_label.pack(side="left", padx=(0, 8))
        self.video_end_entry = customtkinter.CTkEntry(range_row, width=60)
        self.video_end_entry.pack(side="left")
        self.video_end_entry.insert(0, "1")
        self.video_end_entry.bind("<Return>", self._on_video_entries_submit)
        self.video_end_entry.bind("<FocusOut>", self._on_video_entries_submit)
        self.add_ctk_tooltip(self.video_end_entry, "End frame index for export")
        path_row = customtkinter.CTkFrame(controls, fg_color="transparent")
        path_row.pack(fill="x", padx=8, pady=(0, 8))
        open_video_btn = customtkinter.CTkButton(path_row, text="Open Video\u2026", command=self._choose_video)
        open_video_btn.pack(side="left")
        self.add_ctk_tooltip(open_video_btn, "Select a video file to vectorise")
        self.video_path_label = customtkinter.CTkLabel(path_row, text="", anchor="w")
        self.video_path_label.pack(side="left", fill="x", expand=True, padx=8)
        clear_video_btn = customtkinter.CTkButton(path_row, text="\u2715", width=36, command=self._clear_video)
        clear_video_btn.pack(side="right")
        self.add_ctk_tooltip(clear_video_btn, "Remove video file")

    def _build_styles_panel(self, parent: customtkinter.CTkFrame) -> None:
        self.styles_tabview = customtkinter.CTkTabview(parent)
        self.styles_tabview.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 10))

        self._build_style_picker(self.styles_tabview.add("Style"), "start")
        self._build_style_picker(self.styles_tabview.add("End Style"), "end")

    def _build_style_picker(self, tab: customtkinter.CTkFrame, key: str) -> None:
        content = customtkinter.CTkFrame(tab)
        content.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        _style_hint = self._style_preview_hint[key]
        preview = customtkinter.CTkLabel(content, text=_style_hint)
        preview.grid(row=0, column=0, sticky="nwe", padx=10, pady=(10, 8))
        self._set_label_image(preview, None, 300, 240, placeholder=_style_hint)
        self._style_previews[key] = preview

        controls = customtkinter.CTkFrame(tab)
        controls.pack(fill="x", expand=False, side="bottom", padx=8, pady=(0, 8))
        open_style_btn = customtkinter.CTkButton(
            controls, text="Open Lines\u2026", command=lambda k=key: self._choose_style_file(k)
        )
        open_style_btn.pack(side="left", padx=(8, 0), pady=8)
        self.add_ctk_tooltip(open_style_btn, f"Choose a .lines file for the {key} style")
        path_label = customtkinter.CTkLabel(controls, text=self._style_default_text[key], anchor="w")
        path_label.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        self._style_labels[key] = path_label
        clear_style_btn = customtkinter.CTkButton(
            controls, text="\u2715", width=36, command=lambda k=key: self._clear_style_file(k)
        )
        clear_style_btn.pack(side="right", padx=(0, 8), pady=8)
        self.add_ctk_tooltip(clear_style_btn, f"Reset {key} style selection")

    def _build_outputs_section(self, parent: customtkinter.CTkFrame) -> None:
        self.bottom_frame = customtkinter.CTkFrame(parent)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.controls_frame = customtkinter.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", side="top")

        customtkinter.CTkLabel(self.controls_frame, text="Export as").pack(side="left", padx=(10, 4), pady=10)
        self.format_menu = customtkinter.CTkOptionMenu(
            self.controls_frame,
            values=["SVG", "PNG", "JPG", "MP4", "LINES"],
            variable=self.format_var,
            command=self._on_format_change,
            width=90,
        )
        self.format_menu.pack(side="left", padx=(0, 8), pady=10)
        self.add_ctk_tooltip(self.format_menu, "Choose output file format")

        self.size_menu = customtkinter.CTkOptionMenu(
            self.controls_frame, values=["\u2014"], variable=self.size_var, width=80
        )
        self.size_menu.pack(side="left", padx=(0, 8), pady=10)
        self.add_ctk_tooltip(self.size_menu, "Scale output dimensions (raster formats only)")

        self.audio_toggle = customtkinter.CTkSwitch(
            self.controls_frame, text="\u266a", variable=self.audio_var, onvalue=True, offvalue=False
        )
        self.audio_toggle.pack(side="left", padx=(0, 8), pady=10)
        self.add_ctk_tooltip(self.audio_toggle, "Include audio in video exports")

        self.progress_bar = customtkinter.CTkProgressBar(self.controls_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()

        self.convert_button = customtkinter.CTkButton(
            self.controls_frame,
            text="Export \u25b6",
            command=self._do_export,
            width=120,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
        )
        self.convert_button.pack(side="right", padx=(0, 10), pady=10)
        self.add_ctk_tooltip(self.convert_button, "Start processing and saving files")

    def _install_tab_change_hook(self) -> None:
        if segmented := getattr(self.inputs_tabview, "_segmented_button", None):
            original_cmd = segmented.cget("command")

            def _chained(tab_name: str) -> None:
                if callable(original_cmd):
                    original_cmd(tab_name)
                self._on_inputs_tab_changed(tab_name)

            segmented.configure(command=_chained)
        self.after(150, self._poll_active_tab)

    def _register_drop_targets(self) -> None:
        if TkinterDnD is None or DND_FILES is None or not getattr(self, "TkdndVersion", None):
            return
        for tab_name, widgets, handler in [
            ("Lines", [self.lines_list_frame, self.lines_preview_label], self._on_lines_drop),
            ("Images", [self.images_list_frame, self.images_preview_label], self._on_images_drop),
        ]:
            tab = self.inputs_tabview.tab(tab_name)
            targets: list[tk.Widget | customtkinter.CTkFrame] = [tab, *widgets]
            if interior := getattr(widgets[0], "_scrollable_frame", None):
                targets.append(interior)
            for t in targets:
                if dr := getattr(t, "drop_target_register", None):
                    dr(DND_FILES)
                if db := getattr(t, "dnd_bind", None):
                    db("<<Drop>>", handler)
        video_tab = self.inputs_tabview.tab("Video")
        for vt in [video_tab, self.video_first_preview, self.video_last_preview, self.video_path_label]:
            if dr := getattr(vt, "drop_target_register", None):
                dr(DND_FILES)
            if db := getattr(vt, "dnd_bind", None):
                db("<<Drop>>", self._on_video_drop)
        for key, tab_name in [("start", "Style"), ("end", "End Style")]:
            style_tab = self.styles_tabview.tab(tab_name)
            style_targets = [style_tab, self._style_previews[key], self._style_labels[key]]
            for st in style_targets:
                if dr := getattr(st, "drop_target_register", None):
                    dr(DND_FILES)
                if db := getattr(st, "dnd_bind", None):
                    db("<<Drop>>", lambda e, k=key: self._on_style_drop(e, k))

    @staticmethod
    def _parse_drop_data(data: str) -> list[str]:
        if not data:
            return []
        if "{" in data:
            return re.findall(r"\{(.+?)\}", data)
        return data.split()
