# this_file: vexy-lines-run/tests/test_handlers.py
"""Focused tests for list-controller helpers in vexy_lines_run.handlers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from vexy_lines_run.handlers import AppHandlersMixin


class _HandlersHarness(AppHandlersMixin):
    pass


class _FakeFont:
    def actual(self, key: str) -> str:
        assert key == "family"
        return "Arial"


class _FakeFrame:
    def winfo_width(self) -> int:
        return 200


class TestListMutations:
    def test_add_lines_selects_first_valid_index_when_none_selected(self):
        harness = object.__new__(_HandlersHarness)
        harness._lines_paths = []
        harness._selected_lines_index = None
        harness._refresh_lines_list = MagicMock()
        harness._update_lines_preview = MagicMock()

        harness._add_lines(["ignore.png", "first.lines", "first.lines"])

        assert harness._lines_paths == ["first.lines"]
        assert harness._selected_lines_index == 0
        harness._refresh_lines_list.assert_called_once_with()
        harness._update_lines_preview.assert_called_once_with()

    def test_remove_selected_lines_repairs_selection_to_last_valid_index(self):
        harness = object.__new__(_HandlersHarness)
        harness._lines_paths = ["first.lines", "second.lines"]
        harness._selected_lines_index = 1
        harness._refresh_lines_list = MagicMock()
        harness._update_lines_preview = MagicMock()

        harness._remove_selected_lines()

        assert harness._lines_paths == ["first.lines"]
        assert harness._selected_lines_index == 0
        harness._refresh_lines_list.assert_called_once_with()
        harness._update_lines_preview.assert_called_once_with()

    def test_remove_selected_image_clears_selection_when_last_item_deleted(self):
        harness = object.__new__(_HandlersHarness)
        harness._image_paths = ["only.png"]
        harness._selected_image_index = 0
        harness._refresh_image_list = MagicMock()
        harness._update_images_preview = MagicMock()

        harness._remove_selected_image()

        assert harness._image_paths == []
        assert harness._selected_image_index is None
        harness._refresh_image_list.assert_called_once_with()
        harness._update_images_preview.assert_called_once_with()


class TestListRenderingAndPreviews:
    def test_refresh_image_list_adds_placeholder_when_empty(self):
        harness = object.__new__(_HandlersHarness)
        harness._image_paths = []
        harness._image_rows = []
        harness.images_list_frame = _FakeFrame()
        harness._images_hint = "Drop images here"
        harness._font = _FakeFont()
        placeholder = MagicMock()

        with patch("vexy_lines_run.handlers.customtkinter.CTkLabel", return_value=placeholder) as label_cls:
            harness._refresh_image_list()

        label_cls.assert_called_once_with(
            harness.images_list_frame,
            text="Drop images here",
            font=("Arial", 12, "italic"),
            text_color=("#888888", "#777777"),
        )
        placeholder.pack.assert_called_once_with(expand=True, pady=40)
        assert harness._image_rows == [placeholder]

    def test_update_lines_preview_normalizes_invalid_selection_to_zero(self):
        harness = object.__new__(_HandlersHarness)
        harness._lines_paths = ["first.lines"]
        harness._selected_lines_index = 9
        harness._lines_raw_image = None
        harness._redraw_lines_preview = MagicMock()

        with (
            patch("vexy_lines_run.handlers.extract_preview_from_lines", return_value=b"preview-bytes"),
            patch("vexy_lines_run.handlers.Image.open", return_value="opened-preview"),
        ):
            harness._update_lines_preview()

        assert harness._selected_lines_index == 0
        assert harness._lines_raw_image == "opened-preview"
        harness._redraw_lines_preview.assert_called_once_with()

    def test_update_images_preview_clears_stale_image_before_suppressed_open_failure(self):
        harness = object.__new__(_HandlersHarness)
        harness._image_paths = ["broken.png"]
        harness._selected_image_index = 0
        harness._images_raw_image = object()
        harness._redraw_images_preview = MagicMock()

        with patch("vexy_lines_run.handlers.Image.open", side_effect=OSError("broken image")):
            harness._update_images_preview()

        assert harness._images_raw_image is None
        harness._redraw_images_preview.assert_called_once_with()
