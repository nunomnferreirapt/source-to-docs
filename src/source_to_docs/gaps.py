"""Deterministic first pass of the gap analysis: source blocks against the docs index."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .indexer import HEADING, build_index
from .scrub import strip_header
from .text import keywords, overlap

DEFAULT_THRESHOLD = 0.35
BLOCK_KEYWORDS = 15
MIN_BLOCK_WORDS = 60
SPEAKER = re.compile(r"^\[?[\w\- ]{1,30}\]?:\s")


@dataclass
class Block:
    number: int
    title: str
    text: str
    keywords: list[str] = field(default_factory=list)

    @property
    def block_id(self) -> str:
        digest = hashlib.sha1(" ".join(sorted(self.keywords)).encode("utf-8")).hexdigest()
        return digest[:10]


@dataclass
class Match:
    path: str
    heading: str
    score: float


@dataclass
class BlockResult:
    block: Block
    matches: list[Match]
    is_gap: bool

    @property
    def best_score(self) -> float:
        return self.matches[0].score if self.matches else 0.0


def _title_for(text: str) -> str:
    """First line with some substance, speaker or mail prefix removed, cut to 8 words."""
    candidates = [SPEAKER.sub("", line).strip() for line in text.strip().splitlines()]
    candidates = [line for line in candidates if line]
    first = next((line for line in candidates if len(line.split()) >= 5), candidates[0])
    words = first.split()
    return " ".join(words[:8]) + (" ..." if len(words) > 8 else "")


def split_blocks(text: str) -> list[Block]:
    """Split by headings when the source has at least two, else by paragraph groups."""
    text = strip_header(text)
    lines = text.splitlines()
    heading_lines = [i for i, line in enumerate(lines) if HEADING.match(line)]
    chunks: list[tuple[str | None, str]] = []
    if len(heading_lines) >= 2:
        bounds = heading_lines + [len(lines)]
        intro = "\n".join(lines[: heading_lines[0]]).strip()
        if intro:
            chunks.append((None, intro))
        for start, end in zip(bounds, bounds[1:]):
            match = HEADING.match(lines[start])
            body = "\n".join(lines[start + 1 : end]).strip()
            if body:
                chunks.append((match.group(2) if match else None, body))
    else:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        group: list[str] = []
        words = 0
        for paragraph in paragraphs:
            group.append(paragraph)
            words += len(paragraph.split())
            if words >= MIN_BLOCK_WORDS:
                chunks.append((None, "\n\n".join(group)))
                group, words = [], 0
        if group:
            if chunks and words < MIN_BLOCK_WORDS // 2:
                title, previous = chunks[-1]
                chunks[-1] = (title, previous + "\n\n" + "\n\n".join(group))
            else:
                chunks.append((None, "\n\n".join(group)))

    blocks = []
    for number, (title, body) in enumerate(chunks, start=1):
        block_keywords = keywords(f"{title or ''}\n{body}", limit=BLOCK_KEYWORDS)
        blocks.append(Block(number, title or _title_for(body), body, block_keywords))
    return blocks


def match_block(block: Block, index: dict[str, Any], top: int = 3) -> list[Match]:
    matches = []
    for file in index["files"]:
        for section in file["sections"]:
            score = overlap(block.keywords, section["keywords"])
            if score > 0:
                matches.append(Match(file["path"], section["heading"], score))
    matches.sort(key=lambda m: (-m.score, m.path, m.heading))
    return matches[:top]


def analyze(source_text: str, docs_dir: Path, threshold: float = DEFAULT_THRESHOLD) -> list[BlockResult]:
    index = build_index(docs_dir)
    results = []
    for block in split_blocks(source_text):
        matches = match_block(block, index)
        best = matches[0].score if matches else 0.0
        results.append(BlockResult(block, matches, is_gap=best < threshold))
    return results


def render_report(
    results: list[BlockResult], source: Path, docs_dir: Path, threshold: float
) -> str:
    gaps = [r for r in results if r.is_gap]
    covered = [r for r in results if not r.is_gap]
    lines = [
        "# Gap analysis",
        "",
        f"Source: {source}",
        f"Docs: {docs_dir}",
        f"Blocks: {len(results)}, candidate gaps: {len(gaps)}, threshold: {threshold}",
        "",
        "## Candidate gaps",
        "",
    ]
    if not gaps:
        lines += ["No block fell below the threshold.", ""]
    for result in gaps:
        block = result.block
        lines.append(f"### Block {block.number}: {block.title} (best score {result.best_score})")
        lines.append("")
        lines.append(f"Id: {block.block_id}")
        lines.append(f"Keywords: {', '.join(block.keywords)}")
        if result.matches:
            closest = "; ".join(f"{m.path} > {m.heading} ({m.score})" for m in result.matches)
            lines.append(f"Closest: {closest}")
        else:
            lines.append("Closest: none")
        lines.append("")
        excerpt = " ".join(block.text.split())
        lines.append("> " + (excerpt[:300] + " ..." if len(excerpt) > 300 else excerpt))
        lines.append("")
    lines += ["## Covered blocks", "", "| Block | Title | Best match | Score |", "|---|---|---|---|"]
    for result in covered:
        best = result.matches[0]
        lines.append(
            f"| {result.block.number} | {result.block.title} | {best.path} > {best.heading} | {best.score} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_report(
    clean_source: Path, docs_dir: Path, out: Path, threshold: float = DEFAULT_THRESHOLD
) -> list[BlockResult]:
    results = analyze(clean_source.read_text(encoding="utf-8"), docs_dir, threshold)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report(results, clean_source, docs_dir, threshold), encoding="utf-8")
    return results
