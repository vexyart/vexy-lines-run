# this_file: vexy-lines-run/tests/test_ui_verification.py
"""Automated verification tests for UI improvements (Issue 501).

Tests verify actual UI properties by extracting constants and patterns
from app.py without requiring a display server.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


class TestExportButtonColors:
    """Verify Export button colors match specifications by parsing app.py."""

    def test_export_button_green_by_default(self):
        """Export button should be green (#2E7D32) when not exporting."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find the convert button initialization with green color
        green_pattern = r'fg_color="#([0-9A-Fa-f]+)".*text="Export'
        match = re.search(green_pattern, content, re.DOTALL)
        assert match is not None, "Could not find Export button initialization with fg_color"
        assert match.group(1).upper() == "2E7D32", f"Export button fg_color is #{match.group(1)}, expected #2E7D32"

    def test_export_button_hover_color(self):
        """Export button hover color should be #1B5E20."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find hover color in convert button initialization
        hover_pattern = r'hover_color="#([0-9A-Fa-f]+)".*text="Export'
        match = re.search(hover_pattern, content, re.DOTALL)
        assert match is not None, "Could not find Export button initialization with hover_color"
        assert match.group(1).upper() == "1B5E20", f"Export button hover_color is #{match.group(1)}, expected #1B5E20"

    def test_export_button_red_during_export(self):
        """Export button should change to red (#D32F2F) when exporting starts."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find where button is reconfigured to red during export (in _do_export before _run_export)
        red_pattern = r'def _do_export.*?\n.*?convert_button\.configure\(text="Stop", fg_color="#([0-9A-Fa-f]+)".*command=self\._stop_export'
        match = re.search(red_pattern, content, re.DOTALL)
        assert match is not None, "Could not find button reconfiguration with Stop text and red fg_color in _do_export"
        assert match.group(1).upper() == "D32F2F", f"Stop button fg_color is #{match.group(1)}, expected #D32F2F"

    def test_export_button_red_hover_color(self):
        """Stop button hover color should be #B71C1C."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find hover color in Stop button configuration (in _do_export)
        hover_pattern = r'def _do_export.*?\n.*?convert_button\.configure\(text="Stop".*hover_color="#([0-9A-Fa-f]+)".*command=self\._stop_export'
        match = re.search(hover_pattern, content, re.DOTALL)
        assert match is not None, (
            "Could not find button reconfiguration with Stop text and red hover_color in _do_export"
        )
        assert match.group(1).upper() == "B71C1C", f"Stop button hover_color is #{match.group(1)}, expected #B71C1C"

    def test_export_button_reverts_on_complete(self):
        """Export button should revert to green after export completes."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find _on_export_complete method and verify button is reset
        complete_pattern = (
            r'def _on_export_complete.*?convert_button\.configure\(\s*text="Export \\u25b6".*fg_color="#([0-9A-Fa-f]+)"'
        )
        match = re.search(complete_pattern, content, re.DOTALL)
        assert match is not None, "Could not find button reconfiguration in _on_export_complete"
        assert match.group(1).upper() == "2E7D32", f"Export complete fg_color is #{match.group(1)}, expected #2E7D32"

    def test_export_button_reverts_on_error(self):
        """Export button should revert to green after export errors."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find _on_export_error method and verify button is reset
        error_pattern = (
            r'def _on_export_error.*?convert_button\.configure\(\s*text="Export \\u25b6".*fg_color="#([0-9A-Fa-f]+)"'
        )
        match = re.search(error_pattern, content, re.DOTALL)
        assert match is not None, "Could not find button reconfiguration in _on_export_error"
        assert match.group(1).upper() == "2E7D32", f"Export error fg_color is #{match.group(1)}, expected #2E7D32"


class TestEmptyListPlaceholders:
    """Verify empty list placeholder texts match specifications."""

    def test_lines_list_empty_placeholder(self):
        """Lines list should show 'Drop lines here' when empty."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Check for placeholder text in lines list
        placeholder_matches = re.findall(r'text="Drop lines here"', content)
        assert len(placeholder_matches) >= 1, "Could not find 'Drop lines here' placeholder text"

    def test_images_list_empty_placeholder(self):
        """Images list should show 'Drop images here' when empty."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Check for placeholder text in images list
        assert 'text="Drop images here"' in content, "Could not find 'Drop images here' placeholder text"

    def test_style_picker_placeholder(self):
        """Style picker should show 'Drop lines here' when empty."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Style picker uses same text as lines
        placeholder_matches = re.findall(r'text="Drop lines here"', content)
        assert len(placeholder_matches) >= 1, "Could not find 'Drop lines here' placeholder text for style picker"


class TestButtonLabels:
    """Verify button text labels match specifications."""

    def test_add_lines_button_text(self):
        """Button to add lines should be 'Add Lines…'."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Check for Add Lines button (unicode ellipsis U+2026)
        assert 'text="Add Lines\\u2026"' in content, "Could not find 'Add Lines…' button text"

    def test_add_images_button_text(self):
        """Button to add images should be 'Add Images…'."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        assert 'text="Add Images\\u2026"' in content, "Could not find 'Add Images…' button text"

    def test_open_lines_button_text(self):
        """Button to open style lines should be 'Open Lines…'."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        assert 'text="Open Lines\\u2026"' in content, "Could not find 'Open Lines…' button text"

    def test_open_video_button_text(self):
        """Button to open video should be 'Open Video…'."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        assert 'text="Open Video\\u2026"' in content, "Could not find 'Open Video…' button text"

    def test_export_button_text_normal(self):
        """Export button should show 'Export ▶' when not exporting."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Check for text in button initialization
        assert 'text="Export \\u25b6"' in content, "Could not find 'Export ▶' button text"

    def test_export_button_text_stop(self):
        """Export button should show 'Stop' when exporting."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Check for text in configure call during export
        configure_stop_pattern = r'configure\(text="Stop"'
        match = re.search(configure_stop_pattern, content)
        assert match is not None, "Could not find 'Stop' button text configuration"


class TestMenuItems:
    """Verify menu items exist and have correct labels."""

    def test_file_menu_has_stop_export_item(self):
        """File menu should have a 'Stop' menu item for stopping export."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find File menu Stop item
        file_menu_pattern = r'file_menu\.add_option\("Stop"'
        match = re.search(file_menu_pattern, content)
        assert match is not None, "Could not find 'Stop' menu item in File menu"

    def test_export_menu_has_stop_export_item(self):
        """Export menu should have a 'Stop' menu item for stopping export."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find Export menu Stop item
        export_menu_pattern = r'export_menu\.add_option\("Stop"'
        match = re.search(export_menu_pattern, content)
        assert match is not None, "Could not find 'Stop' menu item in Export menu"

    def test_file_menu_has_export_item(self):
        """File menu should have an 'Export ▶' menu item."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find File menu Export item
        file_menu_pattern = r'file_menu\.add_option\("Export \\u25b6"'
        match = re.search(file_menu_pattern, content)
        assert match is not None, "Could not find 'Export ▶' menu item in File menu"

    def test_export_menu_has_export_item(self):
        """Export menu should have an 'Export ▶' menu item."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find Export menu Export item
        export_menu_pattern = r'export_menu\.add_option\("Export \\u25b6"'
        match = re.search(export_menu_pattern, content)
        assert match is not None, "Could not find 'Export ▶' menu item in Export menu"


class TestProgressBarVisibility:
    """Verify progress bar visibility during export lifecycle."""

    def test_progress_bar_hidden_by_default(self):
        """Progress bar should be hidden when not exporting."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find progress bar initialization
        pb_init_pattern = r"self\.progress_bar = customtkinter\.CTkProgressBar\(self\.controls_frame\)"
        match = re.search(pb_init_pattern, content)
        assert match is not None, "Could not find progress bar initialization"

        # Check for pack_forget immediately after initialization
        pb_hide_pattern = r"self\.progress_bar\.pack_forget\(\)\s*$"
        matches = re.findall(pb_hide_pattern, content, re.MULTILINE)
        assert len(matches) > 0, "Could not find progress_bar.pack_forget() to hide it initially"

    def test_progress_bar_visible_during_export(self):
        """Progress bar should be visible when export is in progress."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find where progress bar is packed during export
        pb_show_pattern = r'self\.progress_bar\.pack\(side="left".*?\)'
        match = re.search(pb_show_pattern, content)
        assert match is not None, "Could not find progress_bar.pack() to show it during export"

    def test_progress_bar_hidden_after_export_complete(self):
        """Progress bar should be hidden again after export completes."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find pack_forget in _on_export_complete
        complete_hide_pattern = r"def _on_export_complete.*?self\.progress_bar\.pack_forget\(\)"
        match = re.search(complete_hide_pattern, content, re.DOTALL)
        assert match is not None, "Could not find progress_bar.pack_forget() in _on_export_complete"

    def test_progress_bar_hidden_after_export_error(self):
        """Progress bar should be hidden after export errors."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find pack_forget in _on_export_error
        error_hide_pattern = r"def _on_export_error.*?self\.progress_bar\.pack_forget\(\)"
        match = re.search(error_hide_pattern, content, re.DOTALL)
        assert match is not None, "Could not find progress_bar.pack_forget() in _on_export_error"


class TestExportButtonStateChanges:
    """Verify export button transitions through correct states."""

    def test__is_exporting_flag_exists(self):
        """App should have _is_exporting flag to track state."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find _is_exporting flag initialization
        assert "self._is_exporting = False" in content, "Could not find _is_exporting flag initialization"

    def test_button_transitions_to_stop_on_export_start(self):
        """Button should change to 'Stop' (red) when export starts."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find _do_export method
        do_export_pattern = r'def _do_export.*?self\.convert_button\.configure\(text="Stop"'
        match = re.search(do_export_pattern, content, re.DOTALL)
        assert match is not None, "Could not find button configure with 'Stop' text in _do_export"

        # Check for _is_exporting set to True
        export_start_pattern = r"def _do_export.*?self\._is_exporting = True"
        match2 = re.search(export_start_pattern, content, re.DOTALL)
        assert match2 is not None, "Could not find _is_exporting = True in _do_export"

    def test_button_transitions_to_normal_on_export_complete(self):
        """Button should revert to 'Export ▶' (green) when export completes."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find _on_export_complete method
        complete_pattern = r"def _on_export_complete.*?self\._is_exporting = False"
        match = re.search(complete_pattern, content, re.DOTALL)
        assert match is not None, "Could not find _is_exporting = False in _on_export_complete"

        # Check for button configure with Export text
        export_complete_text = r'def _on_export_complete.*?convert_button\.configure\(\s*text="Export \\u25b6"'
        match2 = re.search(export_complete_text, content, re.DOTALL)
        assert match2 is not None, "Could not find button configure with 'Export ▶' text in _on_export_complete"

    def test_button_transitions_to_normal_on_export_error(self):
        """Button should revert to 'Export ▶' (green) when export errors."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find _on_export_error method
        error_pattern = r"def _on_export_error.*?self\._is_exporting = False"
        match = re.search(error_pattern, content, re.DOTALL)
        assert match is not None, "Could not find _is_exporting = False in _on_export_error"

        # Check for button configure with Export text
        export_error_text = r'def _on_export_error.*?convert_button\.configure\(\s*text="Export \\u25b6"'
        match2 = re.search(export_error_text, content, re.DOTALL)
        assert match2 is not None, "Could not find button configure with 'Export ▶' text in _on_export_error"

    def test_button_prevents_double_export(self):
        """Button should check _is_exporting to prevent starting a second export."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find guard check at start of _do_export
        guard_pattern = r"def _do_export.*?if self\._is_exporting:\s*return"
        match = re.search(guard_pattern, content, re.DOTALL)
        assert match is not None, "Could not find _is_exporting guard check in _do_export"

    def test_stop_button_updates_progress(self):
        """Stop button text should update with progress counter during export."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find progress update in _on_export_progress
        progress_pattern = r'convert_button\.configure\(text=f"Stop'
        match = re.search(progress_pattern, content)
        assert match is not None, "Could not find Stop button text update with progress counter"


class TestExportLifecycleIntegration:
    """Integration tests for complete export lifecycle state machine."""

    def test_lifecycle_methods_exist(self):
        """All lifecycle methods should exist."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        methods = [
            "_do_export",
            "_run_export",
            "_on_export_progress",
            "_on_export_complete",
            "_on_export_error",
            "_stop_export",
        ]
        for method in methods:
            assert re.search(rf"def {method}", content), f"Could not find {method} method"

    def test_abort_event_exists(self):
        """App should have abort_event for stopping export."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find abort_event creation
        assert "self.abort_event = threading.Event()" in content, "Could not find abort_event initialization"

    def test_abort_event_cleared_on_export_start(self):
        """abort_event should be cleared when export starts."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find abort_event.clear() in _do_export
        pattern = r"def _do_export.*?self\.abort_event\.clear\(\)"
        match = re.search(pattern, content, re.DOTALL)
        assert match is not None, "Could not find abort_event.clear() in _do_export"

    def test_abort_event_set_on_stop(self):
        """abort_event should be set when Stop is clicked."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        content = app_path.read_text()

        # Find abort_event.set() in _stop_export
        pattern = r"def _stop_export.*?self\.abort_event\.set\(\)"
        match = re.search(pattern, content, re.DOTALL)
        assert match is not None, "Could not find abort_event.set() in _stop_export"


class TestImportVerification:
    """Verify UI verification module can be imported and run without display."""

    def test_import_ui_verification_module(self):
        """Test that this module can be imported without display."""
        assert True

    def test_app_py_exists(self):
        """Verify app.py file exists."""
        app_path = Path(__file__).parent.parent / "src" / "vexy_lines_run" / "app.py"
        assert app_path.exists(), f"app.py not found at {app_path}"
