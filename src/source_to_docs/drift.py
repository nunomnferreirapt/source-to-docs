"""Read-only watch: which gaps closed, stay open or appeared since the last run."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gaps import DEFAULT_THRESHOLD, analyze
from .indexer import STATE_DIR


@dataclass
class SourceDrift:
    source: str
    closed: list[dict[str, str]] = field(default_factory=list)
    still_open: list[dict[str, str]] = field(default_factory=list)
    new: list[dict[str, str]] = field(default_factory=list)


def state_path(docs_dir: Path) -> Path:
    return docs_dir / STATE_DIR / "drift.json"


def load_state(docs_dir: Path) -> dict[str, Any]:
    path = state_path(docs_dir)
    if not path.exists():
        return {"checked_at": None, "sources": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def current_gaps(source: Path, docs_dir: Path, threshold: float) -> list[dict[str, str]]:
    results = analyze(source.read_text(encoding="utf-8"), docs_dir, threshold)
    return [
        {"id": r.block.block_id, "title": r.block.title, "score": str(r.best_score)}
        for r in results
        if r.is_gap
    ]


def run_drift(
    docs_dir: Path,
    sources_dir: Path,
    threshold: float = DEFAULT_THRESHOLD,
    now: datetime | None = None,
    write: bool = True,
) -> list[SourceDrift]:
    previous = load_state(docs_dir)
    checked_at = (now or datetime.now(timezone.utc).replace(microsecond=0)).isoformat()
    report: list[SourceDrift] = []
    new_state: dict[str, Any] = {"checked_at": checked_at, "sources": {}}

    for source in sorted(sources_dir.glob("*.md")):
        gaps = current_gaps(source, docs_dir, threshold)
        current = {gap["id"]: gap for gap in gaps}
        before = {gap["id"]: gap for gap in previous["sources"].get(source.name, {}).get("open", [])}
        drift = SourceDrift(source.name)
        drift.closed = [before[i] for i in before if i not in current]
        drift.still_open = [current[i] for i in current if i in before]
        drift.new = [current[i] for i in current if i not in before]
        report.append(drift)
        new_state["sources"][source.name] = {"open": gaps}

    if write:
        path = state_path(docs_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(new_state, indent=2) + "\n", encoding="utf-8")
    return report


def render_drift(report: list[SourceDrift], previous_checked_at: str | None) -> str:
    since = previous_checked_at or "never (first run, every gap is new)"
    lines = ["# Drift watch", "", f"Compared with: {since}", ""]
    for drift in report:
        lines.append(f"## {drift.source}")
        lines.append("")
        lines.append(
            f"closed: {len(drift.closed)}, still open: {len(drift.still_open)}, new: {len(drift.new)}"
        )
        for label, items in (("closed", drift.closed), ("still open", drift.still_open), ("new", drift.new)):
            for item in items:
                lines.append(f"- {label}: {item['title']} ({item['id']})")
        lines.append("")
    if not report:
        lines += ["No clean sources found.", ""]
    return "\n".join(lines)
