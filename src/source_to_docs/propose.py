"""Branch, commit the changed docs and print the pull request body. Never merges."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .indexer import STATE_DIR
from .scrub import read_header

PROTECTED = {"main", "master"}

CHECKLIST = [
    "Every change traces back to a quote in the provenance section.",
    "No personal data (names, emails, phone numbers, tokens) reached the docs.",
    "Terminology matches the rest of the site.",
    "Commands and settings were tried, not copied from the source.",
    "Nothing in the source that is wrong or outdated was written down as fact.",
]


class ProposeError(RuntimeError):
    pass


@dataclass
class Proposal:
    branch: str
    title: str
    files: list[tuple[str, str, str, str]]
    body: str
    pr_url: str | None = None


def git(repo: Path, *args: str, strip: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise ProposeError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed.stdout.strip() if strip else completed.stdout


def repo_root(docs_dir: Path) -> Path:
    return Path(git(docs_dir, "rev-parse", "--show-toplevel"))


def current_branch(repo: Path) -> str:
    return git(repo, "rev-parse", "--abbrev-ref", "HEAD")


def changed_markdown(repo: Path, docs_dir: Path) -> list[str]:
    """Markdown files with changes under docs_dir, the state folder excluded."""
    relative = docs_dir.resolve().relative_to(repo.resolve()).as_posix()
    scope = "." if relative == "." else relative
    status = git(repo, "status", "--porcelain", "--untracked-files=all", "--", scope, strip=False)
    files = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        if path.endswith(".md") and f"{STATE_DIR}/" not in path:
            files.append(path)
    return sorted(files)


def render_body(
    title: str,
    files: list[tuple[str, str, str, str]],
    provenance: Path | None,
    provenance_notes: str | None,
) -> str:
    lines = [f"# {title}", "", "## Summary", ""]
    for path, label, added, removed in files:
        lines.append(f"- `{path}`: {label}, +{added} -{removed}")
    lines += ["", "## Provenance", ""]
    if provenance is not None:
        header = read_header(provenance)
        lines.append(f"- Clean source: `{provenance}`")
        lines.append(f"- Original: `{header.get('source', 'unknown')}`")
        lines.append(f"- Scrubbed at: {header.get('scrubbed_at', 'unknown')}")
    else:
        lines.append("- No source given.")
    lines.append("")
    if provenance_notes:
        lines += ["### Quotes", "", provenance_notes.strip(), ""]
    else:
        lines += ["No provenance.md found. Add the quotes each change rests on.", ""]
    lines += ["## Reviewer checklist", ""]
    lines += [f"- [ ] {item}" for item in CHECKLIST]
    lines += ["", "Opened by source-to-docs. A person reviews and merges; the tool never does."]
    return "\n".join(lines) + "\n"


def propose(
    docs_dir: Path,
    branch: str,
    title: str,
    provenance: Path | None = None,
    open_pr: bool = False,
) -> Proposal:
    if branch in PROTECTED:
        raise ProposeError(f"refusing to propose on protected branch '{branch}'")
    repo = repo_root(docs_dir)
    files = changed_markdown(repo, docs_dir)
    if not files:
        raise ProposeError("no changed markdown files under the docs folder; nothing to propose")

    existing = git(repo, "branch", "--list", branch)
    git(repo, "checkout", "-q", *([] if existing else ["-b"]), branch)
    if current_branch(repo) in PROTECTED:
        raise ProposeError("refusing to commit on a protected branch")

    git(repo, "add", "--", *files)
    git(repo, "commit", "-q", "-m", title)
    summary = committed_summary(repo)

    notes_file = docs_dir / STATE_DIR / "provenance.md"
    notes = notes_file.read_text(encoding="utf-8") if notes_file.exists() else None
    body = render_body(title, summary, provenance, notes)
    proposal = Proposal(branch, title, summary, body)

    if open_pr:
        completed = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", body, "--head", branch],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise ProposeError(f"gh pr create failed: {completed.stderr.strip()}")
        proposal.pr_url = completed.stdout.strip()
    return proposal


def committed_summary(repo: Path) -> list[tuple[str, str, str, str]]:
    """(path, status, added, removed) for every file in the commit just made."""
    names = git(repo, "show", "--format=", "--name-status", "HEAD")
    stats = git(repo, "show", "--format=", "--numstat", "HEAD")
    counts = {}
    for line in stats.splitlines():
        added, removed, path = line.split("\t")
        counts[path] = (added, removed)
    summary = []
    for line in names.splitlines():
        status, path = line.split("\t")[0][0], line.split("\t")[-1]
        label = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed"}.get(status, status)
        added, removed = counts.get(path, ("0", "0"))
        summary.append((path, label, added, removed))
    return summary
