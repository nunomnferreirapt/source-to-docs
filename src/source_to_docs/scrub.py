"""Remove personal data from a source before any model reads it."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL = re.compile(r"https?://[^\s<>\"')\]]+")
TOKEN_PARAM = re.compile(
    r"(?:^|[?&/;#])(?:token|access_token|auth|apikey|api_key|key|sig|signature|"
    r"secret|password|session|sid)(?:=|/)",
    re.IGNORECASE,
)
PHONE = re.compile(
    r"(?<![\w/.-])(?:\+\d{1,3}[\s.-]?)?(?:\(\d{1,4}\)[\s.-]?)?"
    r"\d{1,4}(?:[\s.-]?\d{2,4}){2,5}(?![\w/-])"
)
HEADER_FIELD = re.compile(r"^(\w+):\s*(.+)$")


@dataclass
class ScrubResult:
    text: str
    counts: dict[str, int] = field(
        default_factory=lambda: {"email": 0, "phone": 0, "url": 0, "person": 0}
    )


def load_names(names_file: Path | None) -> list[str]:
    """One name per line. Order defines the placeholder number."""
    if names_file is None or not names_file.exists():
        return []
    lines = names_file.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def _name_patterns(names: list[str]) -> list[tuple[re.Pattern[str], str]]:
    """Full name and first name both map to the same placeholder."""
    patterns: list[tuple[re.Pattern[str], str]] = []
    for number, name in enumerate(names, start=1):
        placeholder = f"[person-{number}]"
        parts = name.split()
        variants = [name]
        if len(parts) > 1 and len(parts[0]) >= 3:
            variants.append(parts[0])
        for variant in variants:
            pattern = re.compile(rf"(?<![\w\[])({re.escape(variant)})(?![\w\]])", re.IGNORECASE)
            patterns.append((pattern, placeholder))
    return patterns


def scrub_text(text: str, names: list[str] | None = None) -> ScrubResult:
    """Replace emails, phones, URLs with tokens and listed names. Deterministic."""
    result = ScrubResult(text=text)

    def count(category: str, placeholder: str):
        def replace(_match: re.Match[str]) -> str:
            result.counts[category] += 1
            return placeholder

        return replace

    result.text = EMAIL.sub(count("email", "[email]"), result.text)

    def replace_url(match: re.Match[str]) -> str:
        url = match.group(0)
        if TOKEN_PARAM.search(url):
            result.counts["url"] += 1
            return "[url]"
        return url

    result.text = URL.sub(replace_url, result.text)

    def replace_phone(match: re.Match[str]) -> str:
        candidate = match.group(0)
        digits = sum(char.isdigit() for char in candidate)
        if digits < 9 or digits > 15:
            return candidate
        result.counts["phone"] += 1
        return "[phone]"

    result.text = PHONE.sub(replace_phone, result.text)

    for pattern, placeholder in _name_patterns(names or []):
        result.text = pattern.sub(count("person", placeholder), result.text)

    return result


def render_header(source: Path, scrubbed_at: datetime, counts: dict[str, int]) -> str:
    lines = ["---", f"source: {source}", f"scrubbed_at: {scrubbed_at.isoformat()}", "counts:"]
    lines += [f"  {category}: {count}" for category, count in counts.items()]
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def read_header(clean_source: Path) -> dict[str, str]:
    """Return the top-level header fields of a scrubbed file (source, scrubbed_at)."""
    fields: dict[str, str] = {}
    lines = clean_source.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return fields
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = HEADER_FIELD.match(line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields


def strip_header(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    return text[end + 4 :].lstrip("\n") if end != -1 else text


def scrub_file(
    source: Path,
    out_dir: Path,
    names_file: Path | None = None,
    now: datetime | None = None,
) -> tuple[Path, ScrubResult]:
    """Scrub one source file into <out_dir>/<name>.md with a header."""
    names = load_names(names_file)
    result = scrub_text(source.read_text(encoding="utf-8"), names)
    scrubbed_at = now or datetime.now(timezone.utc).replace(microsecond=0)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{source.stem}.md"
    target.write_text(render_header(source, scrubbed_at, result.counts) + result.text, encoding="utf-8")
    return target, result
