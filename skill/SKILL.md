---
name: source-to-docs
description: Turn a raw source (call transcript, support thread, spec) into a reviewable documentation pull request. Scrub, gap analysis, judgment, draft, propose. Use when asked to update docs from a transcript, thread, spec or meeting notes, or when asked to run /source-to-docs.
---

# source-to-docs

You turn one raw source into documentation changes that a person reviews in a pull request. The CLI does the deterministic steps; you do the judgment. Nothing merges. You never run `--open-pr` unless the user says so in this conversation.

Inputs you need: the source file, the docs folder (a git repo of markdown pages), and optionally a `names.txt` with the people named in the source. Ask for what is missing before you start.

## Steps

1. Scrub first, read second.
   `source-to-docs scrub <source> --out <clean-dir> --names <names.txt>`
   Do not open the raw source. Read only the clean copy. If the clean copy still shows a name, an email or a phone number, add it to `names.txt` or report the pattern, and scrub again.

2. Run the first pass.
   `source-to-docs gaps <clean-dir>/<name>.md <docs-dir> --out <clean-dir>/gaps-<name>.md`
   Read the report. It over-reports by design.

3. Decide, block by block. For each candidate gap ask:
   - Is this about the product, or about one customer, one deadline, one deal? Only the product goes into the docs.
   - Is it already in the closest page under other words? Then it is not a gap; at most a wording fix.
   - Is it stated as fact by someone who knows (support, product), or a guess (prospect, sales)? Guesses do not become docs.
   - Does it belong on an existing page or need a new one? Prefer extending an existing page.
   Write your decisions down as a short list before editing anything.

4. Draft the changes in the docs folder. Match the site's style: headings, sentence length, terminology, numbered steps. Short sentences. No marketing words. No names, no customer details, no numbers that identify one account.

5. Write `<docs-dir>/.source-to-docs/provenance.md`: for each change, the file and section, and the verbatim quote from the clean source it rests on. Add a line "Not written down:" listing what you left out and why. This file is read by `propose` and goes into the pull request body.

6. Propose.
   `source-to-docs propose <docs-dir> --branch docs/<short-topic> --title "docs: <what changed>" --provenance <clean-dir>/<name>.md`
   Show the user the printed pull request body. Dry run is the default. Add `--open-pr` only if the user asked for the pull request to be opened.

7. Report in five lines or fewer: files changed, gaps you judged real and not real, what was left out, and the next command for the user (review the branch, or `--open-pr`).

## Rules

- The raw source is never read by you and never committed anywhere.
- One source per branch. Do not mix sources in one proposal.
- Never commit on `main` or `master`. The CLI refuses; so do you.
- Do not edit `drift.json`. The drift watch owns it.
- If the docs folder has uncommitted changes you did not make, stop and ask.
