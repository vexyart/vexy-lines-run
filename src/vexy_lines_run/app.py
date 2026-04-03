# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false, reportPrivateUsage=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false, reportAttributeAccessIssue=false, reportConstantRedefinition=false
# this_file: src/vexy_lines_run/app.py
"""Main GUI application for Vexy Lines style transfer."""

from __future__ import annotations

import contextlib
import io
import threading
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox

from loguru import logger
from PIL import Image

from vexy_lines_run.handlers import AppHandlersMixin
from vexy_lines_run.helpers import (
    EXPORT_FORMATS_IMAGES,
    EXPORT_FORMATS_LINES,
    EXPORT_FORMATS_VIDEO,
    LINES_EXTENSIONS,
    extract_preview_from_lines,
)
from vexy_lines_run.layout import AppLayoutMixin
from vexy_lines_api.export.models import ExportRequest
from vexy_lines_run.processing import process_export

_CTK_MISSING = "customtkinter is required for the GUI. Install with: pip install customtkinter"

try:
    import customtkinter
except ImportError as exc:
    raise ImportError(_CTK_MISSING) from exc

try:
    from tkinterdnd2 import TkinterDnD
except (ImportError, RuntimeError):
    TkinterDnD = None  # type: ignore[misc]

_BASE_CLASSES: tuple[type, ...] = (customtkinter.CTk,)
if TkinterDnD is not None:
    _BASE_CLASSES = (customtkinter.CTk, TkinterDnD.DnDWrapper)


class _AppMeta(type(customtkinter.CTk)):
    """Metaclass for dynamic DnD support."""


class App(AppLayoutMixin, AppHandlersMixin, *_BASE_CLASSES, metaclass=_AppMeta):  # type: ignore[misc]
    """Main application window for Vexy Lines Run."""

    def __init__(self) -> None:
        super().__init__()
        if TkinterDnD is not None:
            try:
                self.TkdndVersion = TkinterDnD._require(self)
            except RuntimeError:
                logger.warning("tkdnd library unavailable (Tcl version mismatch) — drag-and-drop disabled")
                self.TkdndVersion = None

        self.title("Vexy Lines Run")
        self.geometry("1152x648")
        self.minsize(960, 480)

        self._has_dnd: bool = bool(getattr(self, "TkdndVersion", None))

        # Hint text for empty-state previews (single source of truth)
        self._lines_hint: str = (
            "Drop Vexy Lines documents here\nto export them as SVG, images or video"
            if self._has_dnd
            else "Click: Add Lines\nto export Vexy Lines documents as SVG, images or video"
        )
        self._images_hint: str = (
            "Drop images here\nto apply a Vexy Lines style to them"
            if self._has_dnd
            else "Click: Add Images\nto apply a Vexy Lines style to images"
        )
        self._video_hint: str = (
            "Drop video here\nto apply a Vexy Lines style to it"
            if self._has_dnd
            else "Click: Open Video\nto apply a Vexy Lines style to a video"
        )

        self._style_mode: str = "fast"
        self._style_paths: dict[str, str | None] = {"start": None, "end": None}
        self._style_labels: dict[str, customtkinter.CTkLabel] = {}
        self._style_previews: dict[str, customtkinter.CTkLabel] = {}
        self._style_raw_images: dict[str, Image.Image | None] = {"start": None, "end": None}
        _style_hint = (
            "Drop Vexy Lines document here\nto use as style"
            if self._has_dnd
            else "Click: Open Lines\nto use a Vexy Lines document as style"
        )
        self._style_preview_hint: dict[str, str] = {"start": _style_hint, "end": _style_hint}
        self._style_default_text: dict[str, str] = {"start": "", "end": ""}

        self._image_paths: list[str] = []
        self._image_rows: list[customtkinter.CTkBaseClass] = []
        self._selected_image_index: int | None = None
        self._images_raw_image: Image.Image | None = None

        self._lines_paths: list[str] = []
        self._lines_rows: list[customtkinter.CTkBaseClass] = []
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
        self._export_preview_image: Image.Image | None = None

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

    # ── styles panel ──────────────────────────────────────────────────

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
            self._style_previews[key], self._style_raw_images.get(key), w, h, placeholder=self._style_preview_hint[key]
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

    def _set_style_mode(self, mode: str) -> None:
        """Set the style transfer mode and update menu checkmarks."""
        self._style_mode = mode
        self._update_style_mode_menu()

    def _update_style_mode_menu(self) -> None:
        """Update checkmarks on the Style Mode submenu buttons."""
        if not hasattr(self, "_style_mode_buttons"):
            return
        for m, btn in self._style_mode_buttons.items():
            label = m.capitalize()
            prefix = "\u2713\u2004" if self._style_mode == m else "    "
            btn.configure(text=f"{prefix}{label}")

    # ── export preview ──────────────────────────────────────────────

    def _show_export_preview(self) -> None:
        self.content_frame.grid_remove()
        self.preview_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

    def _hide_export_preview(self) -> None:
        self.preview_frame.grid_remove()
        self.content_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self._export_preview_image = None

    def _on_export_preview(self, preview_bytes: bytes) -> None:
        try:
            self._export_preview_image = Image.open(io.BytesIO(preview_bytes))
        except Exception:
            return
        self._redraw_export_preview()

    def _redraw_export_preview(self) -> None:
        if self._export_preview_image is None:
            return
        w = max(10, self.preview_frame.winfo_width())
        h = max(10, self.preview_frame.winfo_height())
        self._set_label_image(self.preview_label, self._export_preview_image, w, h)

    def _set_export_running_ui_state(self) -> None:
        self._is_exporting = True
        self.abort_event.clear()
        self._show_export_preview()
        self.convert_button.pack_forget()
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=10)
        self.progress_bar.set(0)
        self.convert_button.configure(
            text="Stop \u25a0", fg_color="#D32F2F", hover_color="#B71C1C", command=self._stop_export
        )
        self.convert_button.pack(side="right", padx=(0, 10), pady=10)

    def _reset_export_idle_ui_state(self) -> None:
        self._is_exporting = False
        self._hide_export_preview()
        self.progress_bar.pack_forget()
        self.convert_button.configure(
            text="Export \u25b6", fg_color="#2E7D32", hover_color="#1B5E20", command=self._do_export, state="normal"
        )

    # ── export lifecycle ────────────────────────────────────────────

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
        self._set_export_running_ui_state()
        self._run_export()

    def _stop_export(self) -> None:
        """Signal the export thread to stop processing."""
        if self._is_exporting:
            self.abort_event.set()
            self.convert_button.configure(state="disabled", text="Stopping...")

    def _run_export(self) -> None:
        mode = self.inputs_tabview.get().lower()
        frame_range: tuple[int, int] | None = None
        if mode == "video":
            frame_range = (max(self._video_range[0] - 1, 0), max(self._video_range[1] - 1, 0))

        request = ExportRequest(
            mode=mode,  # type: ignore[arg-type]
            input_paths=self._get_active_input_paths(),
            style_path=self._style_paths["start"],
            end_style_path=self._style_paths["end"],
            output_path=self._output_path,
            format=self.format_var.get(),  # type: ignore[arg-type]
            size=self.size_var.get(),
            audio=self.audio_var.get(),
            frame_range=frame_range,
            style_mode=self._style_mode,
            force=False,
            cleanup=False,
        )
        threading.Thread(
            target=process_export,
            args=(request,),
            kwargs={
                "abort_event": self.abort_event,
                "on_progress": lambda c, t, m: self.after(0, self._on_export_progress, c, t, m),
                "on_preview": lambda b: self.after(0, self._on_export_preview, b),
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
            self.convert_button.configure(text=f"Stop \u25a0 ({current}/{total})")
        logger.debug("Export progress: {}/{} - {}", current, total, message)

    def _on_export_complete(self, message: str) -> None:
        self._reset_export_idle_ui_state()
        logger.info("Export finished: {}", message)
        if self._output_path:
            try:
                from showinfm.showinfm import show_in_file_manager

                show_in_file_manager(self._output_path)
            except Exception:
                logger.opt(exception=True).debug("Could not reveal output in file manager")

    def _on_export_error(self, error: str) -> None:
        self._reset_export_idle_ui_state()
        if error != "Export aborted by user":
            messagebox.showerror("Export Error", error)
        logger.error("Export error: {}", error)

    # ── tab / path helpers ──────────────────────────────────────────

    def _get_active_input_paths(self) -> list[str]:
        m = self.inputs_tabview.get().lower()
        if m == "lines":
            return self._lines_paths
        if m == "images":
            return self._image_paths
        if m == "video":
            return [self._video_path] if self._video_path else []
        return []

    def _copy_cli_command(self) -> None:
        """Build the equivalent vexy-lines-cli command and copy to clipboard."""
        import shlex

        try:
            import pyperclip
        except ImportError:
            messagebox.showerror("Error", "pyperclip is not installed")
            return

        mode = self.inputs_tabview.get().lower()
        paths = self._get_active_input_paths()
        style_start = self._style_paths.get("start")
        style_end = self._style_paths.get("end")
        fmt = self.format_var.get()
        size = self.size_var.get()
        style_mode = self._style_mode

        if not paths:
            messagebox.showwarning("Copy CLI", "No input files selected.")
            return

        parts = ["vexy-lines-cli"]

        if mode == "video":
            parts.append("style_video")
            if style_start:
                parts.extend(["--style", shlex.quote(style_start)])
            if style_end:
                parts.extend(["--end-style", shlex.quote(style_end)])
            parts.extend(["--input", shlex.quote(paths[0])])
            out = self._output_path or ""
            if out:
                parts.extend(["--output", shlex.quote(out)])
            video_range = getattr(self, "_video_range", None)
            if video_range:
                parts.extend(["--start-frame", str(video_range[0])])
                parts.extend(["--end-frame", str(video_range[1])])
            audio = self.audio_var.get() if hasattr(self, "audio_var") else True
            if not audio:
                parts.append("--no-audio")
            if size and size != "\u2014":
                parts.extend(["--size", size])
            if style_mode != "fast":
                parts.extend(["--style-mode", style_mode])

        else:
            # "images" and "lines" both use style_transfer
            parts.append("style_transfer")
            if style_start:
                parts.extend(["--style", shlex.quote(style_start)])
            if style_end:
                parts.extend(["--end-style", shlex.quote(style_end)])
            parts.append("--images")
            for p in paths:
                parts.append(shlex.quote(p))
            out = self._output_path or ""
            if out:
                parts.extend(["--output-dir", shlex.quote(out)])
            if fmt:
                parts.extend(["--format", fmt.lower()])
            if size and size != "\u2014":
                parts.extend(["--size", size])
            if style_mode != "fast":
                parts.extend(["--style-mode", style_mode])

        cmd = " ".join(parts)
        pyperclip.copy(cmd)
        logger.info("Copied CLI command to clipboard: {}", cmd)

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


def main() -> None:
    """Entry point for the Vexy Lines Run application."""
    app = App()
    app.mainloop()


def launch() -> None:
    main()


if __name__ == "__main__":
    main()
