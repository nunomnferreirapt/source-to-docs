import json
from pathlib import Path

from source_to_docs.indexer import build_index, write_index
from source_to_docs.text import keywords


def test_index_lists_files_and_headings(docs_dir: Path):
    index = build_index(docs_dir)
    paths = [f["path"] for f in index["files"]]
    assert paths == ["exports/csv.md", "index.md", "sync/offline-sync.md"]
    sync = next(f for f in index["files"] if f["path"] == "sync/offline-sync.md")
    assert [s["heading"] for s in sync["sections"]] == ["Offline sync", "Sync status"]
    assert "failed" in sync["sections"][1]["keywords"]
    assert "sync" in sync["sections"][1]["keywords"]


def test_keywords_drop_stopwords_and_normalize_plurals():
    assert keywords("The records are stored on the devices and the records sync") == [
        "record",
        "device",
        "stored",
        "sync",
    ]


def test_write_index_skips_state_folder_and_hidden_dirs(docs_dir: Path):
    (docs_dir / ".source-to-docs").mkdir()
    (docs_dir / ".source-to-docs" / "provenance.md").write_text("# not a doc\n")
    target = write_index(docs_dir)
    assert target == docs_dir / ".source-to-docs" / "docs-index.json"
    data = json.loads(target.read_text())
    assert all(".source-to-docs" not in f["path"] for f in data["files"])
    assert len(data["files"]) == 3
