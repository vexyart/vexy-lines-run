# this_file: vexy-lines-run/tests/test_ui_issue_501.py
"""Automated verification tests for UI improvements (Issue 501)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from vexy_lines_run.app import App


@pytest.fixture
def app():
    mocks = [
        patch("customtkinter.CTk.__init__", return_value=None),
        patch("customtkinter.CTk.title"),
        patch("customtkinter.CTk.geometry"),
        patch("customtkinter.CTk.minsize"),
        patch("customtkinter.CTk.after"),
        patch("customtkinter.CTk.bind"),
        patch("customtkinter.CTk.lift"),
        patch("customtkinter.CTk.attributes"),
        patch("customtkinter.CTk.focus_force"),
        patch("customtkinter.CTk.winfo_width", return_value=1024),
        patch("customtkinter.CTk.winfo_height", return_value=768),
        patch("customtkinter.CTkFrame"),
        patch("customtkinter.CTkLabel"),
        patch("customtkinter.CTkButton"),
        patch("customtkinter.CTkTabview"),
        patch("customtkinter.CTkScrollableFrame"),
        patch("customtkinter.CTkEntry"),
        patch("customtkinter.CTkOptionMenu"),
        patch("customtkinter.CTkSwitch"),
        patch("customtkinter.CTkProgressBar"),
        patch("customtkinter.CTkImage"),
        patch("CTkMenuBarPlus.CTkMenuBar"),
        patch("CTkMenuBarPlus.CustomDropdownMenu"),
        patch("vexy_lines_run.app.tkfont.Font"),
        patch("vexy_lines_run.app.tkfont.nametofont"),
        patch.object(App, "after"),
        patch.object(App, "bind"),
        patch.object(App, "winfo_width", return_value=1024),
        patch.object(App, "winfo_height", return_value=768),
    ]

    for m in mocks:
        m.start()

    instance = App()
    yield instance

    for m in reversed(mocks):
        m.stop()


def test_export_button_color_is_green(app):
    actual_color = app.convert_button.cget("fg_color").upper()
    assert actual_color in ["#2E7D32", "#28A745"]


def test_empty_list_placeholders(app):
    with patch("customtkinter.CTkLabel") as mock_label:
        app._refresh_lines_list()
        texts = [call.kwargs.get("text") for call in mock_label.call_args_list]
        assert "Drop lines here" in texts

    with patch("customtkinter.CTkLabel") as mock_label:
        app._refresh_image_list()
        texts = [call.kwargs.get("text") for call in mock_label.call_args_list]
        assert "Drop images here" in texts


def test_button_labels(app):
    from customtkinter import CTkButton

    button_texts = [call.kwargs.get("text") for call in CTkButton.call_args_list if "text" in call.kwargs]

    assert any("Add Images" in t for t in button_texts)
    assert any("Add Lines" in t for t in button_texts)
    assert any("Open Lines" in t for t in button_texts)
    assert any("Open Video" in t for t in button_texts)


def test_stop_export_menu_items(app):
    from CTkMenuBarPlus import CustomDropdownMenu

    stop_calls = [
        call
        for call in CustomDropdownMenu.return_value.add_option.call_args_list
        if call.args and call.args[0] == "Stop"
    ]
    assert len(stop_calls) >= 2


def test_progress_bar_visibility_lifecycle(app):
    assert app.progress_bar.pack_forget.called

    with (
        patch("vexy_lines_run.app.filedialog.askdirectory", return_value="/tmp"),
        patch("vexy_lines_run.app.App._run_export"),
    ):
        app._do_export()

    assert app.progress_bar.pack.called
    assert app.progress_bar.set.called_with(0)


def test_export_button_state_change_during_export(app):
    with (
        patch("vexy_lines_run.app.filedialog.askdirectory", return_value="/tmp"),
        patch("vexy_lines_run.app.App._run_export"),
    ):
        app._do_export()

    assert app.convert_button.configure.called
    calls = app.convert_button.configure.call_args_list
    stop_call = next((c for c in calls if c.kwargs.get("text") == "Stop"), None)
    assert stop_call is not None
    assert stop_call.kwargs.get("fg_color").upper() in ["#D32F2F", "#DC3545"]
