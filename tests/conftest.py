from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

FIXED_NOW = datetime(2026, 10, 16, 9, 0, tzinfo=timezone.utc)

DOCS = {
    "index.md": "# Field Logger docs\n\nForms, sync and exports for field data collection.\n",
    "sync/offline-sync.md": (
        "# Offline sync\n\nRecords are stored on the device and sent when a connection exists.\n\n"
        "## Sync status\n\nEach record shows pending, sent or failed. Failed records are retried "
        "on the next sync.\n"
    ),
    "exports/csv.md": (
        "# Export to CSV\n\nOne CSV file per form with field short names as columns, "
        "record id, created at and position.\n"
    ),
}

SOURCE = """## Photo bundle export

From: Priya Ramaswamy <priya@example.com>

Is there a way to export all photos from a project in one zip bundle? Downloading photos one by one
from each record is not possible with 1,400 photos. The bundle should have one folder per form with
photos named after the record id and the field short name. A download link by email would be fine.

From: Support

Yes, the photo bundle is under Exports. Call Priya on +31 6 1234 5678 if the link https://files.example.com/d?token=abc123 fails.

## Sync status question

From: Priya

Each record shows a sync status, pending, sent or failed, and failed records are retried on the next sync
when the device has a connection. Records stay on the device until sent and confirmed.
"""


def write_docs(root: Path) -> Path:
    docs = root / "docs"
    for relative, text in DOCS.items():
        path = docs / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return docs


@pytest.fixture
def docs_dir(tmp_path: Path) -> Path:
    return write_docs(tmp_path)


@pytest.fixture
def source_file(tmp_path: Path) -> Path:
    path = tmp_path / "sources" / "thread.txt"
    path.parent.mkdir()
    path.write_text(SOURCE, encoding="utf-8")
    return path


@pytest.fixture
def names_file(tmp_path: Path) -> Path:
    path = tmp_path / "names.txt"
    path.write_text("# names\nPriya Ramaswamy\nTomas Herrera\n", encoding="utf-8")
    return path


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture
def docs_repo(tmp_path: Path) -> Path:
    """A temporary git repo on main with the docs tree committed."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "commit.gpgsign", "false")
    write_docs(repo)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "docs: initial")
    return repo
