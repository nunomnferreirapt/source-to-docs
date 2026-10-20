from pathlib import Path

from conftest import FIXED_NOW
from source_to_docs.scrub import read_header, scrub_file, scrub_text, strip_header


def test_emails_are_replaced_and_counted():
    result = scrub_text("Mail priya@example.com or ops.team+1@sub.example.org today.")
    assert result.text == "Mail [email] or [email] today."
    assert result.counts["email"] == 2


def test_phone_numbers_in_common_formats_are_replaced():
    text = "Call +1 (415) 555-0199, +1 (415) 555-0142 or 020 123 4567. Not 1,400 photos or Android 10."
    result = scrub_text(text)
    assert result.text == "Call [phone], [phone] or [phone]. Not 1,400 photos or Android 10."
    assert result.counts["phone"] == 3


def test_only_urls_with_tokens_are_replaced():
    text = "See https://docs.example.com/sync and https://files.example.com/d?token=abc123 now."
    result = scrub_text(text)
    assert result.text == "See https://docs.example.com/sync and [url] now."
    assert result.counts["url"] == 1


def test_names_map_to_numbered_placeholders_including_first_names():
    names = ["Priya Ramaswamy", "Tomas Herrera"]
    result = scrub_text("Priya Ramaswamy asked Tomas. Later priya replied to Tomas Herrera.", names)
    assert result.text == "[person-1] asked [person-2]. Later [person-1] replied to [person-2]."
    assert result.counts["person"] == 4


def test_scrub_file_writes_header_with_source_time_and_counts(source_file: Path, names_file: Path, tmp_path: Path):
    target, result = scrub_file(source_file, tmp_path / "clean", names_file, now=FIXED_NOW)
    assert target == tmp_path / "clean" / "thread.md"
    header = read_header(target)
    assert header["source"] == str(source_file)
    assert header["scrubbed_at"] == "2026-10-16T09:00:00+00:00"
    body = strip_header(target.read_text())
    assert "priya@example.com" not in body
    assert "Ramaswamy" not in body
    assert "token=abc123" not in body
    assert "+31 6" not in body
    assert result.counts == {"email": 1, "phone": 1, "url": 1, "person": 3}
    assert target.read_text().count("  person: 3") == 1


def test_scrub_is_deterministic(source_file: Path, names_file: Path, tmp_path: Path):
    first, _ = scrub_file(source_file, tmp_path / "a", names_file, now=FIXED_NOW)
    second, _ = scrub_file(source_file, tmp_path / "b", names_file, now=FIXED_NOW)
    assert first.read_text() == second.read_text()
