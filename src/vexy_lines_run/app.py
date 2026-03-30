# this_file: src/vexy_lines_run/app.py
"""Main GUI application for Vexy Lines style transfer."""

from __future__ import annotations

import base64
import contextlib
import io
import threading
import tkinter as tk
import tkinter.font as tkfont
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING
from tkinter import filedialog, messagebox

import cv2
from loguru import logger
from PIL import Image

from vexy_lines import extract_preview_image
from vexy_lines_run.processing import process_export
from vexy_lines_run.widgets import CTkRangeSlider

if TYPE_CHECKING:
    from typing import Any

_CTK_MISSING = "customtkinter is required for the GUI. Install with: pip install customtkinter"
_MENUBAR_MISSING = "CTkMenuBarPlus is required for the GUI. Install with: pip install CTkMenuBarPlus"

try:
    import customtkinter
except ImportError as exc:
    raise ImportError(_CTK_MISSING) from exc

try:
    from CTkMenuBarPlus import CTkMenuBar, CustomDropdownMenu
except ImportError as exc:
    raise ImportError(_MENUBAR_MISSING) from exc

try:
    from CTkToolTip import CTkToolTip
except ImportError:
    CTkToolTip = None  # type: ignore[assignment,misc]

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    TkinterDnD = None  # type: ignore[assignment,misc]
    DND_FILES = None

IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
VIDEO_EXTENSIONS: set[str] = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
LINES_EXTENSIONS: set[str] = {".lines"}

EXPORT_FORMATS_LINES: list[str] = ["SVG", "PNG", "JPG", "LINES"]
EXPORT_FORMATS_IMAGES: list[str] = ["SVG", "PNG", "JPG"]
EXPORT_FORMATS_VIDEO: list[str] = ["MP4", "PNG", "JPG"]

MAX_STORED_STYLES = 5


def truncate_start(text: str, max_chars: int = 60) -> str:
    """Trim leading characters, keeping only the last *max_chars*."""
    if len(text) <= max_chars:
        return text
    return f"...{text[-(max_chars - 3) :]}"


def extract_preview_from_lines(filepath: str) -> bytes | None:
    """Extract the embedded preview image from a .lines file."""
    try:
        # Try to parse the file to get preview_image_data directly
        from vexy_lines import parse

        doc = parse(filepath)
        return doc.preview_image_data
    except Exception:
        with contextlib.suppress(Exception):
            tree = ET.parse(str(filepath))  # noqa: S314
            root = tree.getroot()
            pd = root.find("PreviewDoc")
            if pd is not None and pd.text:
                return base64.b64decode(pd.text.strip())
    return None


def extract_frame(video_path: str, frame_number: int = 1) -> Image.Image | None:
    """Extract a single frame from video via OpenCV."""
    try:
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    except Exception:
        return None


def fit_image_to_box(image: Image.Image, width: int, height: int) -> Image.Image:
    """Scale image to fit inside box while preserving aspect ratio."""
    fitted = image.copy()
    fitted.thumbnail((max(1, width), max(1, height)), Image.Resampling.LANCZOS)
    if fitted.mode == "RGBA":
        white = Image.new("RGBA", fitted.size, (255, 255, 255, 255))
        fitted = Image.alpha_composite(white, fitted)
    return fitted.convert("RGB")


_BASE_CLASSES: tuple[type, ...] = (customtkinter.CTk,)
if TkinterDnD is not None:
    _BASE_CLASSES = (customtkinter.CTk, TkinterDnD.DnDWrapper)


class _AppMeta(type(customtkinter.CTk)):
    """Metaclass for dynamic DnD support."""


class App(*_BASE_CLASSES, metaclass=_AppMeta):  # type: ignore[misc]
    """Main application window for Vexy Lines Run."""

    def __init__(self) -> None:
        super().__init__()
        if TkinterDnD is not None:
            self.TkdndVersion = TkinterDnD._require(self)

        self.title("Style with Vexy Lines")
        self.geometry("1024x768")
        self.minsize(960, 480)

        self._style_paths: dict[str, str | None] = {"start": None, "end": None}
        self._style_labels: dict[str, customtkinter.CTkLabel] = {}
        self._style_previews: dict[str, customtkinter.CTkLabel] = {}
        self._style_raw_images: dict[str, Image.Image | None] = {"start": None, "end": None}
        self._style_default_text: dict[str, str] = {"start": "Drop lines here", "end": "Drop lines here"}

        self._image_paths: list[str] = []
        self._image_rows: list[customtkinter.CTkLabel] = []
        self._selected_image_index: int | None = None
        self._images_raw_image: Image.Image | None = None

        self._lines_paths: list[str] = []
        self._lines_rows: list[customtkinter.CTkLabel] = []
        self._selected_lines_index: int | None = None
        self._lines_raw_image: Image.Image | None = None

        self._video_path: str = ""
        self._video_total_frames: int = 0
        self._video_has_audio: bool = False
        self._video_range: tuple[int, int] = (1, 1)
        self._syncing_video_controls: bool = False
        self._video_first_raw_image: Image.Image | None = None
        self._video_last_raw_image: Image.Image | None = None

        self._output_path: str = ""
        self.format_var = tk.StringVar(value="SVG")
        self.size_var = tk.StringVar(value="\u2014")
        self.audio_var = tk.BooleanVar(value=True)

        sample_label = customtkinter.CTkLabel(self, text="")
        sample_font = sample_label.cget("font")
        sample_label.destroy()
        if isinstance(sample_font, str):
            self._font = tkfont.nametofont(sample_font)
        else:
            self._font = tkfont.Font(font=sample_font)
        self._last_width: int = 0
        self._last_height: int = 0
        self._resize_job: str | None = None

        self.abort_event = threading.Event()
        self._is_exporting = False

        self._build_layout()
        self._register_drop_targets()
        self._update_size_dropdown_state()
        self._update_audio_toggle_visibility()
        self._update_styles_panel_state()
        self.bind("<Configure>", self._on_resize)

        self.after(50, self._raise_window)

    def _raise_window(self) -> None:
        self.lift()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
        self.focus_force()

    def add_ctk_tooltip(self, widget: tk.Widget, message: str) -> None:
        """Add a tooltip to a widget if library is available."""
        if CTkToolTip is None:
            return
        CTkToolTip(widget, message=message, delay=0.2, follow=True, x_offset=20, y_offset=10, alpha=0.95)

    def _build_layout(self) -> None:
        self._build_menu_bar()
        root = customtkinter.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=12, pady=12)
        root.grid_columnconfigure(0, weight=3)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=0)
        self._build_inputs_panel(root)
        self._build_styles_panel(root)
        self._build_outputs_section(root)

    def _build_menu_bar(self) -> None:
        menu_bar = CTkMenuBar(self)

        file_btn = menu_bar.add_cascade("File")
        file_menu = CustomDropdownMenu(widget=file_btn)
        file_menu.add_option("Add Lines\u2026", command=self._menu_add_lines)
        file_menu.add_separator()
        file_menu.add_option("Export \u25b6", command=self._do_export)
        file_menu.add_option("Stop", command=self._stop_export)
        file_menu.add_separator()
        file_menu.add_option("Quit", command=self.destroy, accelerator="CmdOrCtrl+Q")

        lines_btn = menu_bar.add_cascade("Lines")
        lines_menu = CustomDropdownMenu(widget=lines_btn)
        lines_menu.add_option("Add Lines\u2026", command=self._menu_add_lines)
        lines_menu.add_option("Remove Selected", command=self._remove_selected_lines)
        lines_menu.add_option("Remove All Lines", command=self._clear_all_lines)

        image_btn = menu_bar.add_cascade("Image")
        image_menu = CustomDropdownMenu(widget=image_btn)
        image_menu.add_option("Add Images\u2026", command=self._menu_add_images)
        image_menu.add_option("Remove Selected", command=self._remove_selected_image)
        image_menu.add_option("Remove All Images", command=self._clear_all_images)

        video_btn = menu_bar.add_cascade("Video")
        video_menu = CustomDropdownMenu(widget=video_btn)
        video_menu.add_option("Add Video\u2026", command=self._menu_add_video)
        video_menu.add_option("Reset Range", command=self._reset_video_range)
        video_menu.add_option("Remove Video", command=self._clear_video)

        style_btn = menu_bar.add_cascade("Style")
        style_menu = CustomDropdownMenu(widget=style_btn)
        style_menu.add_option("Open Style\u2026", command=lambda: self._choose_style_file("start"))
        style_menu.add_option("Open End Style\u2026", command=lambda: self._choose_style_file("end"))
        style_menu.add_option("Reset Styles", command=self._clear_all_styles)

        export_btn = menu_bar.add_cascade("Export")
        export_menu = CustomDropdownMenu(widget=export_btn)
        export_menu.add_option("Export \u25b6", command=self._do_export)
        export_menu.add_option("Stop", command=self._stop_export)
        export_menu.add_separator()
        export_menu.add_option("Location\u2026", command=self._choose_output_path)
        fmt_sub = export_menu.add_submenu("Format")
        for fmt in ("SVG", "PNG", "JPG", "MP4", "LINES"):
            fmt_sub.add_option(fmt, command=lambda f=fmt: self._set_format(f))
        size_sub = export_menu.add_submenu("Size")
        for sz in ("1x", "2x", "3x", "4x"):
            size_sub.add_option(sz, command=lambda s=sz: self._set_size(s))
        audio_sub = export_menu.add_submenu("Audio")
        audio_sub.add_option("On", command=lambda: self.audio_var.set(True))
        audio_sub.add_option("Off", command=lambda: self.audio_var.set(False))

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

    def _build_inputs_panel(self, parent: customtkinter.CTkFrame) -> None:
        self.inputs_tabview = customtkinter.CTkTabview(parent)
        self.inputs_tabview.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 10))
        self.add_ctk_tooltip(self.inputs_tabview, "Switch between input modes")
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
        self.add_ctk_tooltip(self.lines_list_frame, "Drop .lines files here")

        self.lines_preview_container = customtkinter.CTkFrame(content, fg_color="transparent")
        self.lines_preview_container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(10, 8))
        self.lines_preview_container.grid_propagate(False)
        self.lines_preview_container.grid_rowconfigure(0, weight=1)
        self.lines_preview_container.grid_columnconfigure(0, weight=1)

        self.lines_preview_label = customtkinter.CTkLabel(self.lines_preview_container, text="Drop lines here")
        self.lines_preview_label.grid(row=0, column=0, sticky="nsew")
        self.add_ctk_tooltip(self.lines_preview_label, "Preview of the selected line file")
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
        self.add_ctk_tooltip(self.images_list_frame, "Drop image files here")

        self.images_preview_container = customtkinter.CTkFrame(content, fg_color="transparent")
        self.images_preview_container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(10, 8))
        self.images_preview_container.grid_propagate(False)
        self.images_preview_container.grid_rowconfigure(0, weight=1)
        self.images_preview_container.grid_columnconfigure(0, weight=1)

        self.images_preview_label = customtkinter.CTkLabel(self.images_preview_container, text="Drop images here")
        self.images_preview_label.grid(row=0, column=0, sticky="nsew")
        self.add_ctk_tooltip(self.images_preview_label, "Preview of the selected image")
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

        self.video_first_preview = customtkinter.CTkLabel(self.video_first_preview_container, text="")
        self.video_first_preview.grid(row=0, column=0, sticky="nsew")
        self.add_ctk_tooltip(self.video_first_preview, "Preview of the first frame in range")

        self.video_last_preview_container = customtkinter.CTkFrame(previews, fg_color="transparent")
        self.video_last_preview_container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(10, 8))
        self.video_last_preview_container.grid_propagate(False)
        self.video_last_preview_container.grid_rowconfigure(0, weight=1)
        self.video_last_preview_container.grid_columnconfigure(0, weight=1)

        self.video_last_preview = customtkinter.CTkLabel(self.video_last_preview_container, text="")
        self.video_last_preview.grid(row=0, column=0, sticky="nsew")
        self.add_ctk_tooltip(self.video_last_preview, "Preview of the last frame in range")
        self._update_video_previews()
        self.video_first_preview.configure(text="")
        self.video_last_preview.configure(text="")
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
        self.add_ctk_tooltip(self.styles_tabview, "Set start and end styles for interpolation")
        self._build_style_picker(self.styles_tabview.add("Style"), "start")
        self._build_style_picker(self.styles_tabview.add("End Style"), "end")

    def _build_style_picker(self, tab: customtkinter.CTkFrame, key: str) -> None:
        content = customtkinter.CTkFrame(tab)
        content.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        preview = customtkinter.CTkLabel(content, text="Drop lines here")
        preview.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 8))
        self._set_label_image(preview, None, 300, 240, placeholder="Drop lines here")
        self._style_previews[key] = preview
        self.add_ctk_tooltip(preview, f"Preview of the {key} style document")
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

    def _poll_active_tab(self) -> None:
        self._update_audio_toggle_visibility()
        self.after(300, self._poll_active_tab)

    def _register_drop_targets(self) -> None:
        if TkinterDnD is None or DND_FILES is None:
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
        """Parse tkinterdnd2 drop data into a list of file paths."""
        if not data:
            return []
        if "{" in data:
            import re

            return re.findall(r"\{(.+?)\}", data)
        return data.split()

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
        return truncate_start(path, max(MAX_STORED_STYLES, width_px // avg))

    def _on_resize(self, event: tk.Event) -> None:
        if event.widget is not self:
            return
        w = self.winfo_width()
        h = self.winfo_height()
        if abs(w - self._last_width) <= 5 and abs(h - self._last_height) <= 5:  # noqa: PLR2004
            return
        self._last_width = w
        self._last_height = h
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(70, self._resize_refresh)

    def _resize_refresh(self) -> None:
        self._resize_job = None
        self._refresh_image_list()
        self._refresh_lines_list()
        self._retruncate_labels()
        self._redraw_images_preview()
        self._redraw_lines_preview()
        self._redraw_video_previews()
        self._set_style_preview_image("start")
        self._set_style_preview_image("end")

    def _retruncate_labels(self) -> None:
        if self._video_path:
            wpx = max(10, self.video_path_label.winfo_width() - 10)
            self.video_path_label.configure(text=self._truncate_start_for_width(self._video_path, wpx))
        for key in ("start", "end"):
            if p := self._style_paths.get(key):
                lbl = self._style_labels[key]
                wpx = max(10, lbl.winfo_width() - 10)
                lbl.configure(text=self._truncate_start_for_width(p, wpx))

    def _update_styles_panel_state(self) -> None:
        state = "disabled" if self.inputs_tabview.get() == "Lines" else "normal"
        if seg := getattr(self.styles_tabview, "_segmented_button", None):
            with contextlib.suppress(Exception):
                seg.configure(state=state)
        for key in ("start", "end"):
            tn = "Style" if key == "start" else "End Style"
            try:
                tw = self.styles_tabview.tab(tn)
                self._set_children_state(tw, state)
            except Exception:  # noqa: S112
                continue

    def _set_children_state(self, widget: tk.Widget, state: str) -> None:
        for child in widget.winfo_children():
            with contextlib.suppress(tk.TclError, ValueError):
                if hasattr(child, "configure"):
                    child.configure(state=state)  # type: ignore
            if isinstance(child, tk.Widget):
                self._set_children_state(child, state)

    def _choose_style_file(self, key: str) -> None:
        path = filedialog.askopenfilename(
            title="Choose style document", filetypes=[("Vexy Lines", "*.lines"), ("All files", "*.*")]
        )
        if path:
            self._set_style_file(key, path)

    def _set_style_file(self, key: str, path: str) -> None:
        self._style_paths[key] = path
        lbl = self._style_labels[key]
        lbl.configure(text=self._truncate_start_for_width(path, max(10, lbl.winfo_width() - 10)))
        preview_bytes = extract_preview_from_lines(path)
        if preview_bytes is not None:
            self._style_raw_images[key] = Image.open(io.BytesIO(preview_bytes))
        else:
            self._style_raw_images[key] = None
        self._set_style_preview_image(key)

    def _set_style_preview_image(self, key: str) -> None:
        try:
            container = self._style_previews[key].master
            w = max(10, container.winfo_width())
            h = max(10, container.winfo_height())
        except (KeyError, AttributeError):
            w, h = 300, 240
        self._set_label_image(
            self._style_previews[key], self._style_raw_images.get(key), w, h, placeholder="Drop lines here"
        )

    def _on_style_drop(self, event: tk.Event, key: str) -> None:
        if data := getattr(event, "data", ""):
            dropped = self._parse_drop_data(data)
            for p in dropped:
                if Path(p).suffix.lower() in LINES_EXTENSIONS:
                    self._set_style_file(key, p)
                    return

    def _clear_style_file(self, key: str) -> None:
        self._style_paths[key] = None
        self._style_labels[key].configure(text=self._style_default_text[key])
        self._style_raw_images[key] = None
        self._set_style_preview_image(key)

    def _choose_lines(self) -> None:
        files = filedialog.askopenfilenames(
            title="Choose .lines files", filetypes=[("Vexy Lines", "*.lines"), ("All files", "*.*")]
        )
        if files:
            self._add_lines(list(files))

    def _add_lines(self, paths: list[str]) -> None:
        changed = False
        for p in paths:
            if Path(p).suffix.lower() in LINES_EXTENSIONS and p not in self._lines_paths:
                self._lines_paths.append(p)
                changed = True
        if not changed:
            return
        if self._selected_lines_index is None and self._lines_paths:
            self._selected_lines_index = 0
        self._refresh_lines_list()
        self._update_lines_preview()

    def _remove_selected_lines(self) -> None:
        if self._selected_lines_index is None or not (0 <= self._selected_lines_index < len(self._lines_paths)):
            return
        del self._lines_paths[self._selected_lines_index]
        if not self._lines_paths:
            self._selected_lines_index = None
        elif self._selected_lines_index >= len(self._lines_paths):
            self._selected_lines_index = len(self._lines_paths) - 1
        self._refresh_lines_list()
        self._update_lines_preview()

    def _clear_all_lines(self) -> None:
        self._lines_paths.clear()
        self._selected_lines_index = None
        self._refresh_lines_list()
        self._update_lines_preview()

    def _refresh_lines_list(self) -> None:
        for r in self._lines_rows:
            r.destroy()
        self._lines_rows.clear()
        wpx = max(10, self.lines_list_frame.winfo_width() - 24)
        if not self._lines_paths:
            placeholder = customtkinter.CTkLabel(
                self.lines_list_frame,
                text="Drop lines here",
                font=(self._font.actual("family"), 12, "italic"),
                text_color=("#888888", "#777777"),
            )
            placeholder.pack(expand=True, pady=40)
            self._lines_rows.append(placeholder)
            return
        for i, p in enumerate(self._lines_paths):
            row = customtkinter.CTkLabel(
                self.lines_list_frame,
                text=self._truncate_start_for_width(p, wpx),
                anchor="w",
                padx=8,
                corner_radius=6,
                fg_color=("#e9e9e9", "#2a2a2a"),
            )
            row.pack(fill="x", padx=2, pady=2)
            row.bind("<Button-1>", lambda _e, idx=i: self._select_lines_row(idx))
            self._lines_rows.append(row)
        self._update_lines_row_styles()

    def _select_lines_row(self, index: int) -> None:
        if 0 <= index < len(self._lines_paths):
            self._selected_lines_index = index
            self._update_lines_row_styles()
            self._update_lines_preview()

    def _update_lines_row_styles(self) -> None:
        for idx, row in enumerate(self._lines_rows):
            row.configure(
                fg_color=("#3B8ED0", "#1F6AA5") if idx == self._selected_lines_index else ("#e9e9e9", "#2a2a2a")
            )

    def _update_lines_preview(self) -> None:
        if not self._lines_paths:
            self._lines_raw_image = None
        else:
            idx = self._selected_lines_index if self._selected_lines_index is not None else 0
            if not (0 <= idx < len(self._lines_paths)):
                idx = 0
                self._selected_lines_index = 0
            if pb := extract_preview_from_lines(self._lines_paths[idx]):
                self._lines_raw_image = Image.open(io.BytesIO(pb))
            else:
                self._lines_raw_image = None
        self._redraw_lines_preview()

    def _redraw_lines_preview(self) -> None:
        w = max(10, self.lines_preview_container.winfo_width())
        h = max(10, self.lines_preview_container.winfo_height())
        self._set_label_image(self.lines_preview_label, self._lines_raw_image, w, h, placeholder="Drop lines here")

    def _on_lines_drop(self, event: tk.Event) -> None:
        if data := getattr(event, "data", ""):
            self._add_lines(self._parse_drop_data(data))

    def _choose_images(self) -> None:
        files = filedialog.askopenfilenames(
            title="Choose images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp"), ("All files", "*.*")],
        )
        if files:
            self._add_images(list(files))

    def _add_images(self, paths: list[str]) -> None:
        changed = False
        for p in paths:
            if Path(p).suffix.lower() in IMAGE_EXTENSIONS and p not in self._image_paths:
                self._image_paths.append(p)
                changed = True
        if not changed:
            return
        if self._selected_image_index is None and self._image_paths:
            self._selected_image_index = 0
        self._refresh_image_list()
        self._update_images_preview()

    def _remove_selected_image(self) -> None:
        if self._selected_image_index is None or not (0 <= self._selected_image_index < len(self._image_paths)):
            return
        del self._image_paths[self._selected_image_index]
        if not self._image_paths:
            self._selected_image_index = None
        elif self._selected_image_index >= len(self._image_paths):
            self._selected_image_index = len(self._image_paths) - 1
        self._refresh_image_list()
        self._update_images_preview()

    def _clear_all_images(self) -> None:
        self._image_paths.clear()
        self._selected_image_index = None
        self._refresh_image_list()
        self._update_images_preview()

    def _refresh_image_list(self) -> None:
        for r in self._image_rows:
            r.destroy()
        self._image_rows.clear()
        wpx = max(10, self.images_list_frame.winfo_width() - 24)
        if not self._image_paths:
            placeholder = customtkinter.CTkLabel(
                self.images_list_frame,
                text="Drop images here",
                font=(self._font.actual("family"), 12, "italic"),
                text_color=("#888888", "#777777"),
            )
            placeholder.pack(expand=True, pady=40)
            self._image_rows.append(placeholder)
            return
        for i, p in enumerate(self._image_paths):
            row = customtkinter.CTkLabel(
                self.images_list_frame,
                text=self._truncate_start_for_width(p, wpx),
                anchor="w",
                padx=8,
                corner_radius=6,
                fg_color=("#e9e9e9", "#2a2a2a"),
            )
            row.pack(fill="x", padx=2, pady=2)
            row.bind("<Button-1>", lambda _e, idx=i: self._select_image_row(idx))
            self._image_rows.append(row)
        self._update_image_row_styles()

    def _select_image_row(self, index: int) -> None:
        if 0 <= index < len(self._image_paths):
            self._selected_image_index = index
            self._update_image_row_styles()
            self._update_images_preview()

    def _update_image_row_styles(self) -> None:
        for idx, row in enumerate(self._image_rows):
            row.configure(
                fg_color=("#3B8ED0", "#1F6AA5") if idx == self._selected_image_index else ("#e9e9e9", "#2a2a2a")
            )

    def _update_images_preview(self) -> None:
        if not self._image_paths:
            self._images_raw_image = None
        else:
            idx = self._selected_image_index if self._selected_image_index is not None else 0
            if not (0 <= idx < len(self._image_paths)):
                idx = 0
                self._selected_image_index = 0
            with contextlib.suppress(OSError, ValueError):
                self._images_raw_image = Image.open(self._image_paths[idx]).convert("RGB")
        self._redraw_images_preview()

    def _redraw_images_preview(self) -> None:
        w = max(10, self.images_preview_container.winfo_width())
        h = max(10, self.images_preview_container.winfo_height())
        self._set_label_image(self.images_preview_label, self._images_raw_image, w, h, placeholder="Drop images here")

    def _on_images_drop(self, event: tk.Event) -> None:
        if data := getattr(event, "data", ""):
            self._add_images(self._parse_drop_data(data))

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
        self._video_has_audio = True
        self._set_video_range(1, total)
        self._update_audio_toggle_visibility()

    def _get_video_frame_count(self, path: str) -> int:
        cap = cv2.VideoCapture(path)
        try:
            return max(0, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        finally:
            cap.release()

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
        self._set_label_image(self.video_first_preview, self._video_first_raw_image, w1, h1)

        w2 = max(10, self.video_last_preview_container.winfo_width())
        h2 = max(10, self.video_last_preview_container.winfo_height())
        self._set_label_image(self.video_last_preview, self._video_last_raw_image, w2, h2)

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
            self.audio_toggle.grid()
        else:
            self.audio_toggle.grid_remove()

    def _get_default_export_dir(self) -> str:
        m = self.inputs_tabview.get().lower()
        if m == "lines" and self._lines_paths:
            return str(Path(self._lines_paths[0]).parent)
        if m == "images" and self._image_paths:
            return str(Path(self._image_paths[0]).parent)
        if m == "video" and self._video_path:
            return str(Path(self._video_path).parent)
        return ""

    def _do_export(self) -> None:
        if self._is_exporting:
            return

        fmt = self.format_var.get()
        idir = self._get_default_export_dir()
        if fmt == "MP4":
            sel = filedialog.asksaveasfilename(
                title="Export as MP4",
                defaultextension=".mp4",
                filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
                initialdir=idir or None,
            )
        else:
            sel = filedialog.askdirectory(title="Choose output directory", initialdir=idir or None)
        if not sel:
            return
        self._output_path = sel

        self._is_exporting = True
        self.abort_event.clear()

        self.convert_button.pack_forget()
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=10)
        self.progress_bar.set(0)

        self.convert_button.configure(text="Stop", fg_color="#D32F2F", hover_color="#B71C1C", command=self._stop_export)
        self.convert_button.pack(side="right", padx=(0, 10), pady=10)

        self._run_export()

    def _stop_export(self) -> None:
        """Signal the export thread to stop processing."""
        if self._is_exporting:
            self.abort_event.set()
            self.convert_button.configure(state="disabled", text="Stopping...")

    def _run_export(self) -> None:
        mode = self.inputs_tabview.get().lower()
        threading.Thread(
            target=process_export,
            args=(
                mode,
                self._get_active_input_paths(),
                self._style_paths["start"],
                self._style_paths["end"],
                self._output_path,
                self.format_var.get(),
                self.size_var.get(),
            ),
            kwargs={
                "audio": self.audio_var.get(),
                "frame_range": self._video_range if mode == "video" else None,
                "abort_event": self.abort_event,
                "on_progress": lambda c, t, m: self.after(0, self._on_export_progress, c, t, m),
                "on_complete": lambda m: self.after(0, self._on_export_complete, m),
                "on_error": lambda e: self.after(0, self._on_export_error, e),
            },
            daemon=True,
        ).start()

    def _on_export_progress(self, current: int, total: int, message: str) -> None:
        if not self._is_exporting:
            return
        if total > 0:
            self.progress_bar.set(current / total)
        if not self.abort_event.is_set():
            self.convert_button.configure(text=f"Stop ({current}/{total})")
        logger.debug("Export progress: {}/{} - {}", current, total, message)

    def _on_export_complete(self, message: str) -> None:
        self._is_exporting = False
        self.progress_bar.pack_forget()
        self.convert_button.configure(
            text="Export \u25b6", fg_color="#2E7D32", hover_color="#1B5E20", command=self._do_export, state="normal"
        )
        logger.info("Export finished: {}", message)

    def _on_export_error(self, error: str) -> None:
        self._is_exporting = False
        self.progress_bar.pack_forget()
        self.convert_button.configure(
            text="Export \u25b6", fg_color="#2E7D32", hover_color="#1B5E20", command=self._do_export, state="normal"
        )
        if error != "Export aborted by user":
            messagebox.showerror("Export Error", error)
        logger.error("Export error: {}", error)

    def _get_active_input_paths(self) -> list[str]:
        m = self.inputs_tabview.get().lower()
        if m == "lines":
            return self._lines_paths
        if m == "images":
            return self._image_paths
        if m == "video":
            return [self._video_path] if self._video_path else []
        return []

    def _on_inputs_tab_changed(self, tab_name: str) -> None:
        self._update_styles_panel_state()
        self._update_audio_toggle_visibility()

        m = tab_name.lower()
        if m == "lines":
            self.format_menu.configure(values=EXPORT_FORMATS_LINES)
            if self.format_var.get() not in EXPORT_FORMATS_LINES:
                self.format_var.set("SVG")
        elif m == "images":
            self.format_menu.configure(values=EXPORT_FORMATS_IMAGES)
            if self.format_var.get() not in EXPORT_FORMATS_IMAGES:
                self.format_var.set("SVG")
        elif m == "video":
            self.format_menu.configure(values=EXPORT_FORMATS_VIDEO)
            if self.format_var.get() not in EXPORT_FORMATS_VIDEO:
                self.format_var.set("MP4")
        self._on_format_change(self.format_var.get())

    def _choose_output_path(self) -> None:
        fmt = self.format_var.get()
        idir = self._get_default_export_dir()
        if fmt == "MP4":
            sel = filedialog.asksaveasfilename(
                title="Choose output file",
                defaultextension=".mp4",
                filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
                initialdir=idir or None,
            )
        else:
            sel = filedialog.askdirectory(title="Choose output directory", initialdir=idir or None)
        if sel:
            self._output_path = sel


def main() -> None:
    """Entry point for the Vexy Lines Run application."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
