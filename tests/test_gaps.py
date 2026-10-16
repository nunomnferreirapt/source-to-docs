from pathlib import Path

from conftest import SOURCE
from source_to_docs.gaps import analyze, split_blocks, write_report


def test_source_with_headings_splits_by_heading():
    text = "# A\n\nfirst body here\n\n# B\n\nsecond body here\n"
    blocks = split_blocks(text)
    assert [b.title for b in blocks] == ["A", "B"]
    assert blocks[1].text == "second body here"


def test_source_without_headings_groups_paragraphs_by_size():
    short = "Sales: Thanks for joining.\n\n"
    long_paragraph = "Lena: " + " ".join(["word"] * 70) + "\n\n"
    blocks = split_blocks(short + long_paragraph + short + long_paragraph + "Sales: Bye.\n")
    assert len(blocks) == 2
    assert blocks[0].title.startswith("word word word")
    assert blocks[1].text.endswith("Sales: Bye.")


def test_covered_block_is_not_a_gap_and_uncovered_block_is(docs_dir: Path):
    results = analyze(SOURCE, docs_dir)
    by_title = {r.block.title: r for r in results}
    photo = next(r for t, r in by_title.items() if "photo" in t.lower())
    status = next(r for t, r in by_title.items() if "status" in t.lower())
    assert photo.is_gap
    assert photo.matches[0].path == "exports/csv.md"
    assert not status.is_gap
    assert status.matches[0].heading == "Sync status"


def test_gap_report_names_closest_match_and_quotes_excerpt(docs_dir: Path, tmp_path: Path):
    clean = tmp_path / "thread.md"
    clean.write_text(SOURCE, encoding="utf-8")
    out = tmp_path / "gaps.md"
    results = write_report(clean, docs_dir, out)
    report = out.read_text()
    assert report.startswith("# Gap analysis")
    assert f"candidate gaps: {sum(r.is_gap for r in results)}" in report
    assert "Closest: exports/csv.md > Export to CSV" in report
    assert "> Is there a way to export all photos" in report
    assert "| Sync status question | sync/offline-sync.md > Sync status |" in report
