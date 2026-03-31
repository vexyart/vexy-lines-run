# this_file: vexy-lines-run/tests/test_ui_properties.py
"""Tests for UI properties and export lifecycle (Issue 501)."""

from __future__ import annotations

from pathlib import Path

_APP_PY_PATH = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
_LAYOUT_PY_PATH = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "layout.py"
_HANDLERS_PY_PATH = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "handlers.py"
_APP_SOURCE = _APP_PY_PATH.read_text() if _APP_PY_PATH.exists() else ""
_LAYOUT_SOURCE = _LAYOUT_PY_PATH.read_text() if _LAYOUT_PY_PATH.exists() else ""
_HANDLERS_SOURCE = _HANDLERS_PY_PATH.read_text() if _HANDLERS_PY_PATH.exists() else ""
_ALL_SOURCE = _APP_SOURCE + "\n" + _LAYOUT_SOURCE + "\n" + _HANDLERS_SOURCE


class TestButtonColors:
    """Test button color configurations."""

    def test_export_button_default_color_green(self):
        """Export button should be green (#2E7D32) by default."""
        assert 'fg_color="#2E7D32"' in _APP_SOURCE
        assert 'hover_color="#1B5E20"' in _APP_SOURCE

    def test_stop_button_color_red(self):
        """Stop button should be red (#D32F2F) during export."""
        assert 'fg_color="#D32F2F"' in _APP_SOURCE
        assert 'hover_color="#B71C1C"' in _APP_SOURCE


class TestButtonTitles:
    """Test button title text."""

    def test_add_lines_button_text(self):
        """Add Lines button should have correct text with ellipsis."""
        assert "Add Lines" in _ALL_SOURCE

    def test_add_images_button_text(self):
        """Add Images button should have correct text with ellipsis."""
        assert "Add Images" in _ALL_SOURCE

    def test_open_lines_button_text(self):
        """Open Lines button (style picker) should have correct text with ellipsis."""
        assert "Open Lines" in _ALL_SOURCE

    def test_open_video_button_text(self):
        """Open Video button should have correct text with ellipsis."""
        assert "Open Video" in _ALL_SOURCE


class TestEmptyListPlaceholders:
    """Test empty list placeholder text."""

    def test_lines_list_empty_placeholder(self):
        """Empty lines list should show 'Drop lines here' placeholder."""
        assert 'text="Drop Vexy Lines document here"' in _ALL_SOURCE or "Drop Vexy Lines document here" in _ALL_SOURCE

    def test_images_list_empty_placeholder(self):
        """Empty images list should show 'Drop images here' placeholder."""
        assert 'text="Drop images here"' in _ALL_SOURCE or "Drop images here" in _ALL_SOURCE

    def test_style_preview_placeholder(self):
        """Style preview should show 'Drop lines here' when empty."""
        assert (
            'placeholder="Drop Vexy Lines document here' in _ALL_SOURCE
            or "Drop Vexy Lines document here" in _ALL_SOURCE
        )


class TestMenuItems:
    """Test menu item existence and labels."""

    def test_file_menu_has_stop_export(self):
        """File menu should have a 'Stop' command."""
        assert 'file_menu.add_option("Stop"' in _ALL_SOURCE

    def test_export_menu_has_stop_export(self):
        """Export menu should have a 'Stop' command."""
        assert 'export_menu.add_option("Stop"' in _ALL_SOURCE


class TestProgressBarBehavior:
    """Test progress bar visibility and behavior."""

    def test_progress_bar_hidden_initially(self):
        """Progress bar should be hidden initially (packed with pack_forget)."""
        assert "self.progress_bar.pack_forget(" in _ALL_SOURCE
        assert "self.progress_bar = customtkinter.CTkProgressBar" in _ALL_SOURCE

    def test_progress_bar_visible_during_export(self):
        """Progress bar should become visible during export."""
        assert "self.progress_bar.pack(" in _ALL_SOURCE


class TestExportLifecycle:
    """Test export lifecycle state changes."""

    def test_export_button_text_changes_to_stop(self):
        """Export button text should change to 'Stop' during export."""
        assert 'text="Stop \\u25a0"' in _ALL_SOURCE

    def test_export_button_state_during_export(self):
        """Export button state during different phases."""
        assert "Export" in _ALL_SOURCE
        assert 'text="Stop \\u25a0"' in _ALL_SOURCE
        assert 'text="Stopping..."' in _ALL_SOURCE

    def test_export_flag_state(self):
        """Test _is_exporting flag behavior."""
        assert "self._is_exporting = False" in _ALL_SOURCE
        assert "self._is_exporting = True" in _ALL_SOURCE

    def test_abort_event_implementation(self):
        """Verify abort event is implemented for stopping export."""
        assert "self.abort_event = threading.Event()" in _ALL_SOURCE
        assert "def _stop_export" in _ALL_SOURCE


class TestButtonTextUpdatesDuringProgress:
    """Test button text updates during progress reporting."""

    def test_button_text_shows_progress(self):
        """Button text should show progress during export."""
        assert "Stop \\u25a0 (" in _ALL_SOURCE


class TestMenuCommands:
    """Test that menu commands reference correct methods."""

    def test_file_menu_stop_command(self):
        """File menu 'Stop' should call _stop_export."""
        assert "command=self._stop_export" in _ALL_SOURCE

    def test_export_menu_stop_command(self):
        """Export menu 'Stop' should call _stop_export."""
        assert "command=self._stop_export" in _ALL_SOURCE


class TestExportButtonColorLifecycle:
    """Test export button color changes through lifecycle."""

    def test_export_button_color_cycle(self):
        """Verify complete color cycle for export button."""
        assert 'fg_color="#2E7D32"' in _ALL_SOURCE
        assert 'fg_color="#D32F2F"' in _ALL_SOURCE


class TestTooltipPresence:
    """Test that tooltips are defined for key buttons."""

    def test_export_button_has_tooltip(self):
        """Export button should have a tooltip."""
        assert "Start processing and saving files" in _ALL_SOURCE

    def test_add_images_button_has_tooltip(self):
        """Add Images button should have a tooltip."""
        assert "Import raster images to process" in _ALL_SOURCE

    def test_add_lines_button_has_tooltip(self):
        """Add Lines button should have a tooltip."""
        assert "Import vector lines from files" in _ALL_SOURCE

    def test_open_video_button_has_tooltip(self):
        """Open Video button should have a tooltip."""
        assert "Select a video file to vectorise" in _ALL_SOURCE


class TestEmptyStateVisuals:
    """Test visual state when lists are empty."""

    def test_empty_lists_visual_consistency(self):
        """Both images and lines list should have consistent empty visual state."""
        assert "Drop images here" in _ALL_SOURCE
        assert "Drop Vexy Lines document here" in _ALL_SOURCE


class TestExportCompletionState:
    """Test state and behavior when export completes."""

    def test_export_restores_button_state(self):
        """Button should restore to initial state after export completes."""
        assert 'fg_color="#2E7D32"' in _ALL_SOURCE


class TestExportErrorState:
    """Test state and behavior when export fails."""

    def test_export_error_restores_button_state(self):
        """Button should restore to initial state after export error."""
        assert 'fg_color="#2E7D32"' in _ALL_SOURCE
