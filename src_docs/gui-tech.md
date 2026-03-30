# GUI Technical Documentation

This document describes the widget structure and architecture of the Vexy Lines Run GUI application.

## Overview

The Vexy Lines Run GUI is built on **CustomTkinter** (a modern CustomTkinter wrapper around tkinter) and follows a hierarchical widget structure. The main `App` class inherits from `customtkinter.CTk` with optional drag-and-drop support via `tkinterdnd2`.

## Widget Hierarchy

![GUI Diagram](images/gui-diag.svg)

### Root Level

```
App (customtkinter.CTk)
├── CTkMenuBar
└── root (customtkinter.CTkFrame)
    ├── inputs_tabview (CTkTabview)
    │   ├── Lines Tab
    │   │   ├── content_frame (CTkFrame)
    │   │   │   ├── lines_list_frame (CTkScrollableFrame)
    │   │   │   └── lines_preview_container (CTkFrame)
    │   │   │       └── lines_preview_label (CTkLabel)
    │   │   └── controls_frame (CTkFrame)
    │   │       ├── add_lines_btn (CTkButton)
    │   │       ├── rm_lines_btn (CTkButton)
    │   │       └── clear_lines_btn (CTkButton)
    │   ├── Images Tab
    │   │   ├── content_frame (CTkFrame)
    │   │   │   ├── images_list_frame (CTkScrollableFrame)
    │   │   │   └── images_preview_container (CTkFrame)
    │   │   │       └── images_preview_label (CTkLabel)
    │   │   └── controls_frame (CTkFrame)
    │   │       ├── add_images_btn (CTkButton)
    │   │       ├── rm_image_btn (CTkButton)
    │   │       └── clear_images_btn (CTkButton)
    │   └── Video Tab
    │       ├── previews_frame (CTkFrame)
    │       │   ├── video_first_preview_container (CTkFrame)
    │       │   │   └── video_first_preview (CTkLabel)
    │       │   └── video_last_preview_container (CTkFrame)
    │       │       └── video_last_preview (CTkLabel)
    │       └── controls_frame (CTkFrame)
    │           ├── range_row (CTkFrame)
    │           │   ├── video_start_entry (CTkEntry)
    │           │   ├── video_range_slider (CTkRangeSlider)
    │           │   ├── video_count_label (CTkLabel)
    │           │   └── video_end_entry (CTkEntry)
    │           └── path_row (CTkFrame)
    │               ├── open_video_btn (CTkButton)
    │               ├── video_path_label (CTkLabel)
    │               └── clear_video_btn (CTkButton)
    ├── styles_tabview (CTkTabview)
    │   ├── Style Tab (start)
    │   │   ├── content_frame (CTkFrame)
    │   │   │   └── _style_previews["start"] (CTkLabel)
    │   │   └── controls_frame (CTkFrame)
    │   │       ├── open_style_btn (CTkButton)
    │   │       ├── _style_labels["start"] (CTkLabel)
    │   │       └── clear_style_btn (CTkButton)
    │   └── Style Tab (end)
    │       ├── content_frame (CTkFrame)
    │       │   └── _style_previews["end"] (CTkLabel)
    │       └── controls_frame (CTkFrame)
    │           ├── open_style_btn (CTkButton)
    │           ├── _style_labels["end"] (CTkLabel)
    │           └── clear_style_btn (CTkButton)
    └── bottom_frame (CTkFrame)
        └── controls_frame (CTkFrame)
            ├── format_menu (CTkOptionMenu)
            ├── size_menu (CTkOptionMenu)
            ├── audio_toggle (CTkSwitch)
            ├── progress_bar (CTkProgressBar)
            └── convert_button (CTkButton)
```

## Key Components

### 1. Menu Bar (`CTkMenuBar`)

The top-level menu provides access to all major functionality through cascading menus:

- **File**: Add lines, export, stop, quit
- **Lines**: Add/remove/clear line files
- **Image**: Add/remove/clear images
- **Video**: Add video, reset range, remove video
- **Style**: Open start/end styles, reset styles
- **Export**: Export settings (format, size, audio)

Built using `CTkMenuBar` from `CTkMenuBarPlus` with `CustomDropdownMenu` for submenu support.

### 2. Inputs Panel (`inputs_tabview`)

A three-tab tabview that switches between input modes:

#### Lines Tab
- **List Frame**: `CTkScrollableFrame` containing `CTkButton` widgets for each .lines file
- **Preview Container**: Shows selected line file preview via `CTkLabel` with `CTkImage`
- **Controls**: Add, remove selected (−), and clear all (×) buttons

#### Images Tab
- **List Frame**: Similar to lines, but for image files
- **Preview Container**: Shows selected image preview
- **Controls**: Add, remove selected, and clear all buttons

#### Video Tab
- **Previews**: Side-by-side first and last frame previews in the selected range
- **Range Controls**:
  - `CTkEntry` widgets for start/end frame numbers
  - `CTkRangeSlider` (custom widget) for visual range selection
  - Label showing frame count
- **Path Controls**: Open video button, path label, clear button

### 3. Styles Panel (`styles_tabview`)

Two-tab tabview for style interpolation:

- **Style Tab**: Start style document
- **End Style Tab**: End style document

Each tab contains:
- **Preview**: `CTkLabel` displaying the style's preview image
- **Controls**: Open lines file button, truncated path label, clear button

Disabled when in "Lines" input mode (lines already contain styles).

### 4. Outputs Section (`bottom_frame`)

Export settings and controls:

- **Format Menu**: `CTkOptionMenu` for selecting export format (SVG/PNG/JPG/MP4/LINES)
- **Size Menu**: `CTkOptionMenu` for scaling (1x/2x/3x/4x, disabled for vector formats)
- **Audio Toggle**: `CTkSwitch` for including/excluding audio in video exports (conditional visibility)
- **Progress Bar**: `CTkProgressBar` showing export progress (hidden unless exporting)
- **Convert Button**: `CTkButton` for starting/stopping export process

## Custom Widgets

### CTkRangeSlider

A custom two-thumb range slider widget bundled in `widgets.py`. Built as a faithful port from the reference implementation.

**Key Features:**
- Two draggable thumbs for selecting a range
- Custom drawing engine with platform-specific optimizations
- Supports horizontal and vertical orientations
- Optional step quantization
- Variable binding support (tk.IntVar/tk.DoubleVar)
- Hover effects and theming integration

**Implementation Details:**
- Inherits from `CTkBaseClass` for proper CustomTkinter integration
- Uses `CTkCanvas` for custom drawing with rounded rectangles
- Platform-specific drawing methods:
  - macOS: `circle_shapes` or `font_shapes`
  - Other: `polygon_shapes` or `font_shapes`
- Handles mouse events for thumb dragging and click-to-set
- Supports both `command` callback and variable bindings

## Window Management

### Drag and Drop

Optional drag-and-drop support via `tkinterdnd2`:

- **Lines tab**: Drops `.lines` files into list or preview
- **Images tab**: Drops image files into list or preview
- **Video tab**: Drops video files into preview area
- **Style tabs**: Drops `.lines` files into preview area

Registered on multiple widget instances (tab, container, label) for robust handling.

### Window Lifecycle

- **Initialization**: `__init__()` calls `_build_layout()`, register drop targets, bind events
- **Raise to Front**: `_raise_window()` ensures window appears on top via `after()` scheduling
- **Resize Handling**: `<Configure>` event triggers debounced `_resize_refresh()` for responsive layouts

## State Management

### Internal State Variables

- `_style_paths`: Dict mapping "start"/"end" keys to file paths
- `_style_labels`: Dict of path display labels
- `_style_raw_images`: Dict of PIL Image objects for style previews
- `_image_paths`: List of image file paths
- `_selected_image_index`: Currently selected image index
- `_lines_paths`: List of .lines file paths
- `_selected_lines_index`: Currently selected lines index
- `_video_path`: Current video file path
- `_video_range`: Tuple of (start_frame, end_frame)
- `_is_exporting`: Boolean flag for export state
- `abort_event`: `threading.Event` for stopping export threads

### Tkinter Variables

- `format_var`: `tk.StringVar` for export format selection
- `size_var`: `tk.StringVar` for export size selection
- `audio_var`: `tk.BooleanVar` for audio toggle state

## UI State Transitions

### Tab Switching

When switching between input tabs (`_on_inputs_tab_changed`):

1. Update available export formats:
   - Lines: SVG, PNG, JPG, LINES
   - Images: SVG, PNG, JPG
   - Video: MP4, PNG, JPG
2. Disable/enable styles panel (disabled for Lines mode)
3. Update audio toggle visibility
4. Trigger size dropdown state update

### Format Changes

When export format changes (`_on_format_change`):

1. Update size dropdown options:
   - Vector formats (SVG, LINES): Disable size menu (show "—")
   - Raster formats (PNG, JPG, MP4): Enable size menu (1x-4x)
2. Update audio toggle visibility

### Audio Toggle Visibility

Audio toggle is only visible when:
- Video tab is active
- Video is loaded
- Video has audio track
- Export format is MP4
- Full video range is selected (1 to total frames)

## Responsive Layout

### Handling Window Resizes

1. `<Configure>` event triggers debounced resize handler
2. `_resize_refresh()` updates all dynamic widths/heights
3. Lists repack with new widths, path labels re-truncated
4. All preview images redrawn to fit new container sizes

### Path Truncation

Long paths are truncated with leading "..." to fit available width:
```python
def truncate_start(text: str, max_chars: int = 60) -> str:
    if len(text) <= max_chars:
        return text
    return f"...{text[-(max_chars - 3):]}"
```

Font-based calculation for pixel-accurate truncation based on widget width.

## Tooltips

Optional tooltips via `CTkToolTip` library:
- Added to all interactive widgets for user guidance
- Gracefully handles widgets that don't support direct binding
- Configured with delay and positioning for better UX

## Threading

Export operations run in background threads:
- `threading.Thread` spawns `process_export()` from `processing.py`
- `abort_event` signals thread to stop
- Callbacks use `app.after()` to update UI from main thread
- Progress, completion, and error callbacks update UI safely

## Key Method Architecture

### Layout Building
- `_build_layout()`: Top-level structure
- `_build_menu_bar()`: Menu construction
- `_build_inputs_panel()`: Tabview with three tabs
- `_build_styles_panel()`: Style picker tabs
- `_build_outputs_section()`: Export controls

### Tab Builders
- `_build_lines_tab()`: Lines-specific widgets
- `_build_images_tab()`: Image-specific widgets
- `_build_video_tab()`: Video-specific widgets
- `_build_style_picker()`: Style picker widgets (reusable)

### Video Range Management
- `_set_video_range()`: Validates and sets range
- `_on_video_slider_change()`: Handles slider input
- `_on_video_entries_submit()`: Handles manual entry input
- `_syncing_video_controls`: Prevents update loops

### Image Management
- `_set_label_image()`: Fits and sets label images
- `fit_image_to_box()`: Aspect-ratio-preserving scaling
- `_redraw_*_preview()`: Refresh specific previews

## File Patterns

Supported file extensions:
- **Lines**: `.lines`
- **Images**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp`
- **Videos**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`

## Dependencies

### Required
- `customtkinter`: Modern tkinter wrapper with dark mode
- `CTkMenuBarPlus`: Enhanced menu bar with dropdowns
- `PIL` (Pillow): Image processing
- `cv2` (OpenCV): Video reading
- `loguru`: Logging

### Optional
- `CTkToolTip`: Tooltip support
- `tkinterdnd2`: Drag and drop support
- `showinfm`: Reveal output in file manager (macOS)

## Future Enhancements

Potential areas for GUI improvement:
1. Additional export formats (TIF, WEBP)
2. Batch processing with progress details
3. Custom theme configuration
4. Preset management (save/load style combinations)
5. Keyboard shortcuts for common operations
6. Export queue for multiple jobs
