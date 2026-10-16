# Claude Code skill: /source-to-docs

The skill does the judgment part of the pipeline: it reads the gap report and the clean source, decides which gaps are real, drafts the doc changes, writes the provenance notes and calls `propose`. The CLI does everything deterministic.

## Install

Copy the folder into your Claude Code skills directory:

```
mkdir -p ~/.claude/skills/source-to-docs
cp skill/SKILL.md ~/.claude/skills/source-to-docs/SKILL.md
```

Or link it so updates in this repo reach the skill:

```
ln -s "$(pwd)/skill" ~/.claude/skills/source-to-docs
```

The `source-to-docs` CLI must be on the path of the shell Claude Code uses (see Install in the main README).

## Use

In Claude Code, inside the docs repo:

```
/source-to-docs update the docs from ~/inbox/call-2026-10-14.txt, names in ~/inbox/names.txt
```

The skill scrubs, runs `gaps`, decides, drafts, writes `provenance.md`, runs `propose` as a dry run and shows you the pull request body. It opens a pull request only if you say so. It never merges.

## Uninstall

```
rm -r ~/.claude/skills/source-to-docs
```
