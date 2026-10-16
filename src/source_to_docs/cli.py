"""Command line entry point: scrub, index, gaps, propose, drift."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .drift import load_state, render_drift, run_drift
from .gaps import DEFAULT_THRESHOLD, write_report
from .indexer import write_index
from .propose import ProposeError, propose
from .scrub import scrub_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="source-to-docs",
        description="From a transcript, a support thread or a spec to a reviewable docs pull request.",
    )
    parser.add_argument("--version", action="version", version=f"source-to-docs {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    scrub = sub.add_parser("scrub", help="remove personal data from a source file")
    scrub.add_argument("source", type=Path)
    scrub.add_argument("--out", type=Path, required=True, help="folder for the clean copy")
    scrub.add_argument("--names", type=Path, default=None, help="names.txt, one name per line")

    index = sub.add_parser("index", help="write docs-index.json for a docs folder")
    index.add_argument("docs_dir", type=Path)
    index.add_argument("--out", type=Path, default=None)

    gaps = sub.add_parser("gaps", help="match a clean source against the docs, list candidate gaps")
    gaps.add_argument("clean_source", type=Path)
    gaps.add_argument("docs_dir", type=Path)
    gaps.add_argument("--out", type=Path, default=Path("gaps.md"))
    gaps.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)

    prop = sub.add_parser("propose", help="branch, commit changed docs, print the PR body")
    prop.add_argument("docs_dir", type=Path)
    prop.add_argument("--branch", required=True)
    prop.add_argument("--title", required=True)
    prop.add_argument("--provenance", type=Path, default=None, help="the clean source file")
    prop.add_argument("--open-pr", action="store_true", help="run gh pr create (default: dry run)")

    drift = sub.add_parser("drift", help="report gaps closed, still open and new since last run")
    drift.add_argument("docs_dir", type=Path)
    drift.add_argument("--sources", type=Path, required=True, help="folder of clean sources")
    drift.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "scrub":
        target, result = scrub_file(args.source, args.out, args.names)
        counts = ", ".join(f"{k}: {v}" for k, v in result.counts.items())
        print(f"wrote {target} ({counts})")
        return 0

    if args.command == "index":
        target = write_index(args.docs_dir, args.out)
        print(f"wrote {target}")
        return 0

    if args.command == "gaps":
        results = write_report(args.clean_source, args.docs_dir, args.out, args.threshold)
        gaps = [r for r in results if r.is_gap]
        print(f"{len(results)} blocks, {len(gaps)} candidate gaps, report in {args.out}")
        for result in gaps:
            print(f"  gap: block {result.block.number}, {result.block.title} ({result.best_score})")
        return 0

    if args.command == "propose":
        try:
            proposal = propose(args.docs_dir, args.branch, args.title, args.provenance, args.open_pr)
        except ProposeError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        mode = f"opened {proposal.pr_url}" if proposal.pr_url else "dry run, no pull request opened"
        print(f"committed {len(proposal.files)} file(s) on branch {proposal.branch}; {mode}")
        print()
        print(proposal.body, end="")
        return 0

    if args.command == "drift":
        previous = load_state(args.docs_dir).get("checked_at")
        report = run_drift(args.docs_dir, args.sources, args.threshold)
        print(render_drift(report, previous), end="")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
