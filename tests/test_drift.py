import json
from pathlib import Path

from conftest import FIXED_NOW, SOURCE
from source_to_docs.drift import load_state, render_drift, run_drift


def _clean_dir(tmp_path: Path) -> Path:
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "thread.md").write_text(SOURCE, encoding="utf-8")
    return clean


def test_first_run_reports_every_gap_as_new_and_stores_state(docs_dir: Path, tmp_path: Path):
    clean = _clean_dir(tmp_path)
    report = run_drift(docs_dir, clean, now=FIXED_NOW)
    assert len(report) == 1
    assert report[0].new and not report[0].closed and not report[0].still_open
    state = json.loads((docs_dir / ".source-to-docs" / "drift.json").read_text())
    assert state["checked_at"] == "2026-10-16T09:00:00+00:00"
    assert len(state["sources"]["thread.md"]["open"]) == len(report[0].new)
    text = render_drift(report, None)
    assert "first run" in text and "new: " in text


def test_second_run_sees_a_gap_close_after_docs_change(docs_dir: Path, tmp_path: Path):
    clean = _clean_dir(tmp_path)
    first = run_drift(docs_dir, clean, now=FIXED_NOW)
    open_before = len(first[0].new)

    (docs_dir / "exports" / "photo-bundle.md").write_text(
        "# Photo bundle export\n\nExport all photos from a project in one zip bundle with one folder "
        "per form. Photos are named after the record id and the field short name. A download link "
        "is sent by email.\n"
    )
    previous = load_state(docs_dir)["checked_at"]
    second = run_drift(docs_dir, clean, now=FIXED_NOW)
    assert len(second[0].closed) >= 1
    assert len(second[0].closed) + len(second[0].still_open) == open_before
    assert not second[0].new
    text = render_drift(second, previous)
    assert "Compared with: 2026-10-16T09:00:00+00:00" in text
    assert "- closed: " in text
