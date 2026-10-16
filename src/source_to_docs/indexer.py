"""Build docs-index.json: files, headings and keywords per heading."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .text import keywords

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
STATE_DIR = ".source-to-docs"


def iter_markdown(docs_dir: Path) -> list[Path]:
    """Markdown files under docs_dir, hidden folders and the state folder skipped."""
    files = []
    for path in sorted(docs_dir.rglob("*.md")):
        relative = path.relative_to(docs_dir)
        if any(part.startswith(".") for part in relative.parts):
            continue
        files.append(path)
    return files


def split_sections(text: str, fallback_title: str) -> list[dict[str, Any]]:
    """One section per heading; text before the first heading becomes an intro."""
    sections: list[dict[str, Any]] = []
    heading, level, body = fallback_title, 1, []
    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            if body or sections or heading != fallback_title:
                sections.append({"heading": heading, "level": level, "body": "\n".join(body)})
            level, heading, body = len(match.group(1)), match.group(2), []
        else:
            body.append(line)
    sections.append({"heading": heading, "level": level, "body": "\n".join(body)})
    return [section for section in sections if section["body"].strip() or section["heading"]]


def index_file(path: Path, docs_dir: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(docs_dir).as_posix()
    sections = split_sections(text, fallback_title=path.stem.replace("-", " "))
    title = next((s["heading"] for s in sections if s["level"] == 1), path.stem)
    title_keywords = keywords(title)
    indexed = []
    for section in sections:
        section_keywords = keywords(f"{section['heading']}\n{section['body']}")
        for keyword in title_keywords:
            if keyword not in section_keywords:
                section_keywords.append(keyword)
        indexed.append(
            {"heading": section["heading"], "level": section["level"], "keywords": section_keywords}
        )
    return {"path": relative, "title": title, "sections": indexed}


def build_index(docs_dir: Path) -> dict[str, Any]:
    files = [index_file(path, docs_dir) for path in iter_markdown(docs_dir)]
    return {"docs_dir": str(docs_dir), "files": files}


def write_index(docs_dir: Path, out: Path | None = None) -> Path:
    index = build_index(docs_dir)
    target = out or docs_dir / STATE_DIR / "docs-index.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return target
