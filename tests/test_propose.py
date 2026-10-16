from pathlib import Path

import pytest

from conftest import FIXED_NOW, git
from source_to_docs.propose import ProposeError, propose
from source_to_docs.scrub import scrub_file


def _edit_docs(repo: Path) -> Path:
    docs = repo / "docs"
    (docs / "exports" / "photo-bundle.md").write_text("# Photo bundle\n\nOne zip per project.\n")
    csv = docs / "exports" / "csv.md"
    csv.write_text(csv.read_text() + "\nSee also the photo bundle.\n")
    state = docs / ".source-to-docs"
    state.mkdir()
    (state / "provenance.md").write_text('- photo-bundle.md: "export all photos from a project in one zip bundle"\n')
    return docs


def test_dry_run_branches_commits_and_prints_body(docs_repo: Path, source_file: Path, names_file: Path, tmp_path: Path):
    docs = _edit_docs(docs_repo)
    clean, _ = scrub_file(source_file, tmp_path / "clean", names_file, now=FIXED_NOW)
    proposal = propose(docs, "docs/photo-bundle", "docs: photo bundle export", provenance=clean)

    assert git(docs_repo, "rev-parse", "--abbrev-ref", "HEAD") == "docs/photo-bundle"
    assert git(docs_repo, "log", "-1", "--format=%s") == "docs: photo bundle export"
    assert git(docs_repo, "status", "--porcelain", "--", "docs/exports") == ""
    assert [f[0] for f in proposal.files] == ["docs/exports/csv.md", "docs/exports/photo-bundle.md"]
    assert proposal.pr_url is None
    assert "`docs/exports/photo-bundle.md`: added, +3 -0" in proposal.body
    assert f"Original: `{source_file}`" in proposal.body
    assert "Scrubbed at: 2026-10-16T09:00:00+00:00" in proposal.body
    assert "export all photos from a project in one zip bundle" in proposal.body
    assert "- [ ] Every change traces back to a quote" in proposal.body
    # the state folder is never part of the proposal
    assert "provenance.md" not in [f[0] for f in proposal.files]
    assert git(docs_repo, "status", "--porcelain", "--", "docs/.source-to-docs") != ""


def test_refuses_protected_branch(docs_repo: Path):
    docs = _edit_docs(docs_repo)
    with pytest.raises(ProposeError, match="protected branch 'main'"):
        propose(docs, "main", "docs: anything")
    assert git(docs_repo, "log", "--oneline").count("\n") == 0


def test_nothing_to_propose_without_changed_markdown(docs_repo: Path):
    with pytest.raises(ProposeError, match="nothing to propose"):
        propose(docs_repo / "docs", "docs/empty", "docs: empty")
    assert git(docs_repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
