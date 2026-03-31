# DEPENDENCIES.md

## vexy-lines-run Dependencies

The `vexy-lines-run` package is the GUI desktop application layer. It relies on the following key dependencies to function:

### First-Party Dependencies
- **vexy-lines-py**: Required for parsing and handling the `.lines` document data model.
- **vexy-lines-apy**: Provides the core style engine, MCP client, and centralized export pipeline that the GUI calls.

### Third-Party Dependencies
- **customtkinter**: Provides modern, customizable, and dark-mode compatible UI widgets on top of standard Tkinter.
- **tkinterdnd2**: Enables drag-and-drop support natively within the Tkinter/CustomTkinter window.
- **Pillow**: Used for image loading, manipulation, and displaying preview images within the UI.
- **resvg-py** / **svglab**: Used for SVG rendering and handling when processing vector graphics.
- **opencv-python-headless**: Used for video frame extraction and processing without pulling in unnecessary X11/GUI libraries.
- **CTkMenuBarPlus**: Used to build modern menu bars integrated with the CustomTkinter aesthetic.
- **CTkToolTip**: Provides tooltips for GUI elements.
- **show-in-file-manager**: Used to easily open export directories or files natively in Finder/Explorer after export.
- **loguru**: Used for structured and easy-to-read application logging.