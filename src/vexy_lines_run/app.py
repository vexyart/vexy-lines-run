# this_file: src/vexy_lines_run/app.py
"""Main GUI application for Vexy Lines style transfer.

A CustomTkinter desktop application with three input-mode tabs (Lines, Images,
Video), style picker panels, export controls, and optional drag-and-drop.
"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Any

import customtkinter as ctk
from loguru import logger
from PIL import Image, ImageTk

if TYPE_CHECKING:
    from collections.abc import Sequence

# ---------------------------------------------------------------------------
# Optional drag-and-drop support
# ---------------------------------------------------------------------------
_HAS_DND = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore[import-untyped]

    _HAS_DND = True
except ImportError:
    TkinterDnD = None  # type: ignore[assignment,misc]
    DND_FILES = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
VIDEO_EXTENSIONS: set[str] = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
LINES_EXTENSIONS: set[str] = {".lines"}
ALL_INPUT_EXTENSIONS: set[str] = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | LINES_EXTENSIONS

EXPORT_FORMATS_LINES: list[str] = ["SVG", "PNG", "JPG", "LINES"]
EXPORT_FORMATS_IMAGES: list[str] = ["SVG", "PNG", "JPG"]
EXPORT_FORMATS_VIDEO: list[str] = ["MP4", "PNG", "JPG"]

SIZE_OPTIONS: list[str] = ["1x", "2x"]

APP_TITLE = "Vexy Lines"
APP_MIN_WIDTH = 900
APP_MIN_HEIGHT = 640
DEFAULT_APPEARANCE = "dark"
DEFAULT_THEME = "blue"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def truncate_middle(text: str, max_width: int = 40) -> str:
    """Truncate *text* in the middle with an ellipsis if it exceeds *max_width*.

    Args:
        text: The string to truncate.
        max_width: Maximum allowed character width.

    Returns:
        Truncated string with ``...`` in the centre, or the original if short
        enough.
    """
    if len(text) <= max_width:
        return text
    keep = max_width - 3  # room for "..."
    left = keep // 2
    right = keep - left
    return f"{text[:left]}...{text[-right:]}"


def truncate_start(text: str, max_chars: int = 60) -> str:
    """Truncate the beginning of *text*, keeping the last *max_chars* characters.

    Args:
        text: The string to truncate.
        max_chars: Maximum allowed character length.

    Returns:
        String prefixed with ``...`` when truncation occurs.
    """
    if len(text) <= max_chars:
        return text
    return f"...{text[-(max_chars - 3):]}"


def extract_preview_from_lines(filepath: str | Path) -> bytes | None:
    """Extract the embedded preview image from a ``.lines`` file.

    Uses the vexy_lines parser to read the preview PNG stored inside the
    ``.lines`` XML structure.

    Args:
        filepath: Path to a ``.lines`` file.

    Returns:
        Raw PNG bytes if a preview exists, otherwise ``None``.
    """
    try:
        from vexy_lines import extract_preview_image

        return extract_preview_image(str(filepath))
    except Exception:
        logger.opt(exception=True).debug("Could not extract preview from {}", filepath)
        return None


def extract_frame(video_path: str | Path, frame_number: int = 0) -> Image.Image | None:
    """Extract a single frame from a video file as a PIL Image.

    Requires OpenCV (``opencv-python``).

    Args:
        video_path: Path to the video file.
        frame_number: Zero-based frame index to extract.

    Returns:
        A PIL ``Image`` on success, or ``None`` if extraction fails.
    """
    try:
        import cv2  # type: ignore[import-untyped]
        import numpy as np

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret: bool
        frame: np.ndarray  # type: ignore[type-arg]
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)
    except Exception:
        logger.opt(exception=True).debug("Could not extract frame {} from {}", frame_number, video_path)
        return None


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


class App(ctk.CTk):  # type: ignore[misc]
    """Main Vexy Lines GUI window.

    Extends ``customtkinter.CTk`` (or ``TkinterDnD.Tk`` when tkinterdnd2 is
    available) to provide a three-tab interface for style transfer across
    .lines files, raster images, and video.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        # Use DnD-enabled Tk root when available
        if _HAS_DND and TkinterDnD is not None:
            # TkinterDnD.Tk patches the root; we initialise CTk on top
            super().__init__()
            logger.info("Drag-and-drop support enabled (tkinterdnd2)")
        else:
            super().__init__()
            if not _HAS_DND:
                logger.info("Drag-and-drop not available (install tkinterdnd2)")

        self.title(APP_TITLE)
        self.minsize(APP_MIN_WIDTH, APP_MIN_HEIGHT)
        ctk.set_appearance_mode(DEFAULT_APPEARANCE)
        ctk.set_default_color_theme(DEFAULT_THEME)

        # State --------------------------------------------------------
        self._input_paths: list[str] = []
        self._style_path: str | None = None
        self._end_style_path: str | None = None
        self._export_running = False
        self._export_thread: threading.Thread | None = None

        # UI variables -------------------------------------------------
        self._format_var = ctk.StringVar(value="SVG")
        self._size_var = ctk.StringVar(value="1x")
        self._audio_var = ctk.BooleanVar(value=True)

        # Build UI -----------------------------------------------------
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construct the complete widget tree."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main container
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        # ---- Top: tab view for input modes ---------------------------
        self._tabview = ctk.CTkTabview(main, height=360)
        self._tabview.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        self._tab_lines = self._tabview.add("Lines")
        self._tab_images = self._tabview.add("Images")
        self._tab_video = self._tabview.add("Video")

        self._build_tab_lines(self._tab_lines)
        self._build_tab_images(self._tab_images)
        self._build_tab_video(self._tab_video)

        # ---- Middle: style pickers -----------------------------------
        style_frame = ctk.CTkFrame(main)
        style_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        style_frame.grid_columnconfigure((0, 1), weight=1)

        self._build_style_picker(style_frame, col=0, label="Style", is_end=False)
        self._build_style_picker(style_frame, col=1, label="End Style (optional)", is_end=True)

        # ---- Bottom: export controls ---------------------------------
        export_frame = ctk.CTkFrame(main)
        export_frame.grid(row=2, column=0, sticky="ew")
        self._build_export_controls(export_frame)

    # ------------------------------------------------------------------
    # Tab builders
    # ------------------------------------------------------------------

    def _build_tab_lines(self, parent: ctk.CTkFrame) -> None:
        """Build the Lines input tab."""
        parent.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(parent, text="Drop or select .lines files", anchor="w")
        label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self._lines_listbox = tk.Listbox(parent, height=6, selectmode=tk.EXTENDED)
        self._lines_listbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        parent.grid_rowconfigure(1, weight=1)

        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        ctk.CTkButton(btn_frame, text="Add Files...", width=120, command=self._on_add_lines).pack(
            side="left", padx=(0, 5)
        )
        ctk.CTkButton(btn_frame, text="Clear", width=80, command=self._on_clear_lines).pack(side="left")

        self._lines_preview_label = ctk.CTkLabel(parent, text="")
        self._lines_preview_label.grid(row=3, column=0, pady=(0, 10))

        # Enable DnD if available
        if _HAS_DND and DND_FILES is not None:
            self._lines_listbox.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
            self._lines_listbox.dnd_bind("<<Drop>>", self._on_drop_lines)  # type: ignore[attr-defined]

    def _build_tab_images(self, parent: ctk.CTkFrame) -> None:
        """Build the Images input tab."""
        parent.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(parent, text="Drop or select image files", anchor="w")
        label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self._images_listbox = tk.Listbox(parent, height=6, selectmode=tk.EXTENDED)
        self._images_listbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        parent.grid_rowconfigure(1, weight=1)

        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        ctk.CTkButton(btn_frame, text="Add Files...", width=120, command=self._on_add_images).pack(
            side="left", padx=(0, 5)
        )
        ctk.CTkButton(btn_frame, text="Clear", width=80, command=self._on_clear_images).pack(side="left")

        if _HAS_DND and DND_FILES is not None:
            self._images_listbox.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
            self._images_listbox.dnd_bind("<<Drop>>", self._on_drop_images)  # type: ignore[attr-defined]

    def _build_tab_video(self, parent: ctk.CTkFrame) -> None:
        """Build the Video input tab."""
        parent.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(parent, text="Select a video file", anchor="w")
        label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        file_frame = ctk.CTkFrame(parent, fg_color="transparent")
        file_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        file_frame.grid_columnconfigure(0, weight=1)

        self._video_path_label = ctk.CTkLabel(file_frame, text="No video selected", anchor="w")
        self._video_path_label.grid(row=0, column=0, sticky="ew")

        ctk.CTkButton(file_frame, text="Browse...", width=100, command=self._on_browse_video).grid(
            row=0, column=1, padx=(10, 0)
        )

        # Video preview
        self._video_preview_label = ctk.CTkLabel(parent, text="")
        self._video_preview_label.grid(row=2, column=0, pady=10)

        # Frame range slider (placeholder -- real widget in widgets.py)
        range_frame = ctk.CTkFrame(parent, fg_color="transparent")
        range_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        ctk.CTkLabel(range_frame, text="Frame range:").pack(side="left")
        self._frame_start_var = ctk.StringVar(value="0")
        self._frame_end_var = ctk.StringVar(value="0")
        ctk.CTkEntry(range_frame, textvariable=self._frame_start_var, width=60).pack(side="left", padx=5)
        ctk.CTkLabel(range_frame, text="to").pack(side="left")
        ctk.CTkEntry(range_frame, textvariable=self._frame_end_var, width=60).pack(side="left", padx=5)

        if _HAS_DND and DND_FILES is not None:
            self._video_path_label.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
            self._video_path_label.dnd_bind("<<Drop>>", self._on_drop_video)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Style picker
    # ------------------------------------------------------------------

    def _build_style_picker(
        self,
        parent: ctk.CTkFrame,
        *,
        col: int,
        label: str,
        is_end: bool,
    ) -> None:
        """Build a style file picker panel.

        Args:
            parent: Container frame.
            col: Grid column index.
            label: Display label text.
            is_end: If ``True`` this is the end-style (interpolation target).
        """
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=col, sticky="nsew", padx=5, pady=5)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 0)
        )

        path_label = ctk.CTkLabel(frame, text="None", anchor="w")
        path_label.grid(row=1, column=0, sticky="ew", padx=10, pady=2)

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        browse_cmd = self._on_browse_end_style if is_end else self._on_browse_style
        clear_cmd = self._on_clear_end_style if is_end else self._on_clear_style

        ctk.CTkButton(btn_row, text="Browse...", width=100, command=browse_cmd).pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_row, text="Clear", width=60, command=clear_cmd).pack(side="left")

        # Preview thumbnail area
        preview = ctk.CTkLabel(frame, text="")
        preview.grid(row=3, column=0, pady=(0, 10))

        if is_end:
            self._end_style_label = path_label
            self._end_style_preview = preview
        else:
            self._style_label = path_label
            self._style_preview = preview

    # ------------------------------------------------------------------
    # Export controls
    # ------------------------------------------------------------------

    def _build_export_controls(self, parent: ctk.CTkFrame) -> None:
        """Build the export format / size / button bar."""
        parent.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(parent, text="Format:").grid(row=0, column=0, padx=(10, 5), pady=10)
        self._format_menu = ctk.CTkOptionMenu(parent, variable=self._format_var, values=EXPORT_FORMATS_IMAGES)
        self._format_menu.grid(row=0, column=1, padx=(0, 15))

        ctk.CTkLabel(parent, text="Size:").grid(row=0, column=2, padx=(0, 5))
        ctk.CTkOptionMenu(parent, variable=self._size_var, values=SIZE_OPTIONS, width=70).grid(
            row=0, column=3, sticky="w"
        )

        self._audio_check = ctk.CTkCheckBox(parent, text="Audio", variable=self._audio_var)
        self._audio_check.grid(row=0, column=4, padx=15)

        self._export_btn = ctk.CTkButton(
            parent,
            text="Export",
            width=120,
            command=self._on_export,
        )
        self._export_btn.grid(row=0, column=5, padx=(0, 10), pady=10)

        self._progress_bar = ctk.CTkProgressBar(parent)
        self._progress_bar.grid(row=1, column=0, columnspan=6, sticky="ew", padx=10, pady=(0, 10))
        self._progress_bar.set(0)

    # ------------------------------------------------------------------
    # Input callbacks
    # ------------------------------------------------------------------

    def _on_add_lines(self) -> None:
        """Open file dialog for .lines files."""
        paths = filedialog.askopenfilenames(
            title="Select .lines files",
            filetypes=[("Lines files", "*.lines"), ("All files", "*.*")],
        )
        self._add_paths_to_listbox(self._lines_listbox, list(paths))

    def _on_clear_lines(self) -> None:
        self._lines_listbox.delete(0, tk.END)
        self._input_paths = []

    def _on_add_images(self) -> None:
        """Open file dialog for image files."""
        exts = " ".join(f"*{e}" for e in sorted(IMAGE_EXTENSIONS))
        paths = filedialog.askopenfilenames(
            title="Select image files",
            filetypes=[("Image files", exts), ("All files", "*.*")],
        )
        self._add_paths_to_listbox(self._images_listbox, list(paths))

    def _on_clear_images(self) -> None:
        self._images_listbox.delete(0, tk.END)
        self._input_paths = []

    def _on_browse_video(self) -> None:
        """Open file dialog for a video file."""
        exts = " ".join(f"*{e}" for e in sorted(VIDEO_EXTENSIONS))
        path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[("Video files", exts), ("All files", "*.*")],
        )
        if path:
            self._set_video_path(path)

    def _set_video_path(self, path: str) -> None:
        """Update the video tab with a new file path."""
        self._input_paths = [path]
        self._video_path_label.configure(text=truncate_start(path))
        # Try to show a preview frame
        thumb = extract_frame(path, frame_number=0)
        if thumb is not None:
            self._show_thumbnail(self._video_preview_label, thumb)

    # ------------------------------------------------------------------
    # Style callbacks
    # ------------------------------------------------------------------

    def _on_browse_style(self) -> None:
        path = filedialog.askopenfilename(
            title="Select style (.lines)",
            filetypes=[("Lines files", "*.lines"), ("All files", "*.*")],
        )
        if path:
            self._style_path = path
            self._style_label.configure(text=truncate_middle(Path(path).name))
            preview_bytes = extract_preview_from_lines(path)
            if preview_bytes:
                self._show_thumbnail_bytes(self._style_preview, preview_bytes)

    def _on_clear_style(self) -> None:
        self._style_path = None
        self._style_label.configure(text="None")
        self._style_preview.configure(image=None, text="")  # type: ignore[arg-type]

    def _on_browse_end_style(self) -> None:
        path = filedialog.askopenfilename(
            title="Select end style (.lines)",
            filetypes=[("Lines files", "*.lines"), ("All files", "*.*")],
        )
        if path:
            self._end_style_path = path
            self._end_style_label.configure(text=truncate_middle(Path(path).name))
            preview_bytes = extract_preview_from_lines(path)
            if preview_bytes:
                self._show_thumbnail_bytes(self._end_style_preview, preview_bytes)

    def _on_clear_end_style(self) -> None:
        self._end_style_path = None
        self._end_style_label.configure(text="None")
        self._end_style_preview.configure(image=None, text="")  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Drag-and-drop callbacks
    # ------------------------------------------------------------------

    def _on_drop_lines(self, event: Any) -> None:
        paths = self._parse_drop_data(event.data)
        valid = [p for p in paths if Path(p).suffix.lower() in LINES_EXTENSIONS]
        self._add_paths_to_listbox(self._lines_listbox, valid)

    def _on_drop_images(self, event: Any) -> None:
        paths = self._parse_drop_data(event.data)
        valid = [p for p in paths if Path(p).suffix.lower() in IMAGE_EXTENSIONS]
        self._add_paths_to_listbox(self._images_listbox, valid)

    def _on_drop_video(self, event: Any) -> None:
        paths = self._parse_drop_data(event.data)
        videos = [p for p in paths if Path(p).suffix.lower() in VIDEO_EXTENSIONS]
        if videos:
            self._set_video_path(videos[0])

    @staticmethod
    def _parse_drop_data(data: str) -> list[str]:
        """Parse tkinterdnd2 drop data into a list of file paths.

        Handles both space-separated and brace-enclosed formats that
        tkinterdnd2 may produce on different platforms.
        """
        if "{" in data:
            # Brace-enclosed paths (may contain spaces)
            import re

            return re.findall(r"\{(.+?)\}", data)
        return data.split()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _on_export(self) -> None:
        """Start an export in a background thread."""
        if self._export_running:
            messagebox.showinfo("Export", "An export is already in progress.")
            return

        # Determine current mode
        current_tab = self._tabview.get()
        mode_map = {"Lines": "lines", "Images": "images", "Video": "video"}
        mode = mode_map.get(current_tab, "images")

        # Collect input paths from the appropriate tab
        if mode == "lines":
            self._input_paths = list(self._lines_listbox.get(0, tk.END))
        elif mode == "images":
            self._input_paths = list(self._images_listbox.get(0, tk.END))
        # video already set via _set_video_path

        if not self._input_paths:
            messagebox.showwarning("Export", "No input files selected.")
            return

        # Ask for output location
        fmt = self._format_var.get()
        if fmt == "MP4":
            output = filedialog.asksaveasfilename(
                defaultextension=".mp4",
                filetypes=[("MP4 video", "*.mp4")],
            )
        else:
            output = filedialog.askdirectory(title="Select output folder")

        if not output:
            return

        # Frame range for video
        frame_range: tuple[int, int] | None = None
        if mode == "video":
            try:
                frame_range = (int(self._frame_start_var.get()), int(self._frame_end_var.get()))
            except ValueError:
                frame_range = None

        self._export_running = True
        self._export_btn.configure(state="disabled")
        self._progress_bar.set(0)

        from vexy_lines_run.processing import process_export

        self._export_thread = threading.Thread(
            target=process_export,
            kwargs={
                "mode": mode,
                "input_paths": self._input_paths,
                "style_path": self._style_path,
                "end_style_path": self._end_style_path,
                "output_path": output,
                "fmt": fmt,
                "size": self._size_var.get(),
                "audio": self._audio_var.get(),
                "frame_range": frame_range,
                "on_progress": self._on_export_progress,
                "on_complete": self._on_export_complete,
                "on_error": self._on_export_error,
            },
            daemon=True,
        )
        self._export_thread.start()

    def _on_export_progress(self, fraction: float, message: str) -> None:
        """Called from worker thread to report progress."""
        self.after(0, self._progress_bar.set, fraction)

    def _on_export_complete(self, message: str) -> None:
        """Called from worker thread on success."""

        def _done() -> None:
            self._export_running = False
            self._export_btn.configure(state="normal")
            self._progress_bar.set(1.0)
            messagebox.showinfo("Export", message)

        self.after(0, _done)

    def _on_export_error(self, error: str) -> None:
        """Called from worker thread on failure."""

        def _err() -> None:
            self._export_running = False
            self._export_btn.configure(state="normal")
            self._progress_bar.set(0)
            messagebox.showerror("Export Error", error)

        self.after(0, _err)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _add_paths_to_listbox(self, listbox: tk.Listbox, paths: Sequence[str]) -> None:
        """Append *paths* to a Tk Listbox, updating internal state."""
        for p in paths:
            listbox.insert(tk.END, p)
            self._input_paths.append(p)

    def _show_thumbnail(self, label: ctk.CTkLabel, img: Image.Image, size: int = 128) -> None:
        """Display a PIL Image as a thumbnail on a CTkLabel."""
        img.thumbnail((size, size))
        photo = ImageTk.PhotoImage(img)
        label.configure(image=photo, text="")
        label.image = photo  # type: ignore[attr-defined]  # prevent GC

    def _show_thumbnail_bytes(self, label: ctk.CTkLabel, data: bytes, size: int = 128) -> None:
        """Display raw image bytes as a thumbnail on a CTkLabel."""
        import io

        img = Image.open(io.BytesIO(data))
        self._show_thumbnail(label, img, size)


# ---------------------------------------------------------------------------
# Public launch function
# ---------------------------------------------------------------------------


def launch() -> None:
    """Create and run the Vexy Lines GUI application.

    This is the main entry point -- call it from ``__main__`` or a console
    script.
    """
    logger.info("Starting Vexy Lines GUI")
    app = App()
    app.mainloop()
