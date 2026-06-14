# this_file: vexy-lines-run/tests/test_rename.py
"""Tests for vexy_lines_run.rename (GUI-side AI rename glue)."""

from __future__ import annotations

import io
import textwrap
from pathlib import Path

import pytest
from PIL import Image

from vexy_lines import parse
from vexy_lines_run import rename as run_rename

_LINES_XML = textwrap.dedent("""\
    <?xml version="1.0" encoding="utf-8"?>
    <Project caption="Demo" version="2.1" dpi="150">
      <Document width_mm="100.0" height_mm="100.0" dpi="300"/>
      <Objects>
        <LrSection caption="Group A" object_id="1" expanded="1">
          <Objects>
            <FreeMesh caption="Layer 1" object_id="10" visible="1">
              <Objects>
                <LinearStrokesTmpl caption="L1" object_id="100" color_name="#000000"/>
                <CircleStrokesTmpl caption="C1" object_id="101" color_name="#000000"/>
              </Objects>
            </FreeMesh>
          </Objects>
        </LrSection>
      </Objects>
    </Project>
""")


class FakeClient:
    def __init__(self):
        self.opened = None

    def open_document(self, path):
        self.opened = path
        return "ok"

    def set_visible(self, object_id, *, visible):  # noqa: ARG002
        return "ok"


def _png() -> bytes:
    img = Image.new("RGB", (30, 30), (255, 255, 255))
    img.putpixel((5, 5), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def lines_file(tmp_path: Path) -> Path:
    p = tmp_path / "demo.lines"
    p.write_text(_LINES_XML, encoding="utf-8")
    return p


def test_count_fills(lines_file: Path):
    assert run_rename.count_fills(lines_file) == 2


def test_run_ai_rename_reports_progress_and_completes(lines_file: Path, tmp_path: Path):
    progress: list[tuple[int, int, str]] = []
    completed: list[tuple[object, object]] = []
    out = tmp_path / "out.lines"

    plan = run_rename.run_ai_rename(
        lines_file,
        out,
        client=FakeClient(),
        on_progress=lambda c, t, m: progress.append((c, t, m)),
        on_complete=lambda p, path: completed.append((p, path)),
        on_error=lambda e: pytest.fail(f"unexpected error: {e}"),
        # engine injection (test-only):
        render_lines_png=lambda _c, _p: _png(),
        describe=lambda _png: "marked region here",
        suggest=lambda _items: "the layer",
        save_artifacts=False,
        work_dir=tmp_path / "work",
    )

    assert plan is not None
    assert len(plan.fills) == 2
    # initial 0/2 progress + one per fill
    assert progress[0][0] == 0
    assert progress[-1] == (2, 2, "Describing fill 2/2")
    assert completed and completed[0][1] == out
    # file actually written with renamed captions
    doc = parse(out)
    assert out.is_file()
    assert doc.groups  # parsed fine


def test_run_ai_rename_reports_error(lines_file: Path, tmp_path: Path):
    errors: list[str] = []

    def boom(_client, _path):
        msg = "render exploded"
        raise RuntimeError(msg)

    result = run_rename.run_ai_rename(
        lines_file,
        tmp_path / "out.lines",
        client=FakeClient(),
        on_error=lambda e: errors.append(e),
        render_lines_png=boom,
        describe=lambda _png: "x y z",
        suggest=lambda _items: "l",
        save_artifacts=False,
        work_dir=tmp_path / "work",
    )

    assert result is None
    assert errors and "render exploded" in errors[0]


def test_start_ai_rename_thread_runs(lines_file: Path, tmp_path: Path):
    completed: list[object] = []
    out = tmp_path / "out.lines"

    thread = run_rename.start_ai_rename_thread(
        lines_file,
        out,
        client=FakeClient(),
        on_complete=lambda _p, path: completed.append(path),
        render_lines_png=lambda _c, _p: _png(),
        describe=lambda _png: "a b c",
        suggest=lambda _items: "l",
        save_artifacts=False,
        work_dir=tmp_path / "work",
    )
    thread.join(timeout=10)
    assert not thread.is_alive()
    assert completed == [out]
