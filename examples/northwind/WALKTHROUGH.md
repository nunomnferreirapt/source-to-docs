# Walkthrough: Northwind Field Logger

Northwind Field Logger is an invented field data app. Its docs live in `docs/`, nine markdown pages in five areas. Two raw sources sit in `sources/`: a support thread about getting photos out of a project, and a demo call transcript. Both carry invented names, emails and phone numbers so the scrub has something to catch.

Every command below was run from a copy of this folder with `git init` and one commit on `main`. The output is pasted as it came out, only the `scrubbed_at` time will differ for you.

```
cp -r examples/northwind /tmp/northwind && cd /tmp/northwind
git init -b main && git add -A && git commit -m "docs: initial site"
```

## 1. Scrub the sources

Nothing reads a source before this step. Emails, phone numbers, URLs with tokens and the names in `names.txt` become placeholders. The header records what was replaced.

```
$ source-to-docs scrub sources/support-thread.md --out clean --names names.txt
wrote clean/support-thread.md (email: 3, phone: 1, url: 1, person: 8)

$ source-to-docs scrub sources/demo-transcript.md --out clean --names names.txt
wrote clean/demo-transcript.md (email: 2, phone: 1, url: 0, person: 9)

$ head -9 clean/support-thread.md
---
source: sources/support-thread.md
scrubbed_at: 2026-10-16T10:43:17+00:00
counts:
  email: 3
  phone: 1
  url: 1
  person: 8
---

$ sed -n 16p clean/support-thread.md
Hi, we finished the drainage survey last week and the client wants all the photos. There are about 1,400 photos across 3 forms. Downloading them one by one from each record is not possible for us. Is there a way to export all photos from a project in one go? Our project manager [person-2] ([email], [phone]) asked me to sort this out before Friday.

```

## 2. Index the docs

Every page, every heading, keywords per heading. `gaps` and `drift` build this in memory; the command writes it so you can look at it.

```
$ source-to-docs index docs
wrote docs/.source-to-docs/docs-index.json

```

## 3. Find the gaps

Each source is split into blocks and each block is matched against the index by keyword overlap. Blocks under the threshold are candidate gaps, with the closest pages named. This is a first pass: it is deterministic and it over-reports on purpose. The judgment comes next.

```
$ source-to-docs gaps clean/support-thread.md docs --out reports/gaps-support-thread.md
4 blocks, 4 candidate gaps, report in reports/gaps-support-thread.md
  gap: block 1, Getting all photos out of a project at ... (0.267)
  gap: block 2, Hello [person-1], yes. In the web app go ... (0.333)
  gap: block 3, That worked, thanks. One more thing: the link ... (0.2)
  gap: block 4, Clear, thank you. Also, our field team asked ... (0.267)

$ source-to-docs gaps clean/demo-transcript.md docs --out reports/gaps-demo-transcript.md
6 blocks, 4 candidate gaps, report in reports/gaps-demo-transcript.md
  gap: block 1, Demo call, Northwind Field Logger, 45 minutes. Attendees: ... (0.267)
  gap: block 2, You can schedule that. In the project, under ... (0.2)
  gap: block 4, The GeoJSON export is always WGS 84, which ... (0.333)
  gap: block 6, Last one. We have about 40 forms built ... (0.2)

$ sed -n 1,21p reports/gaps-support-thread.md
# Gap analysis

Source: clean/support-thread.md
Docs: docs
Blocks: 4, candidate gaps: 4, threshold: 0.35

## Candidate gaps

### Block 1: Getting all photos out of a project at ... (best score 0.267)

Id: 3fda2129a2
Keywords: photo, email, project, across, client, downloading, drainage, export, finished, form, friday, manager, phone, possible, record
Closest: admin/users-and-roles.md > Roles (0.267); exports/csv-and-geojson.md > CSV (0.2); exports/csv-and-geojson.md > Photos in exports (0.2)

> Subject: Getting all photos out of a project at once From: [person-1] <[email]> To: [email] Hi, we finished the drainage survey last week and the client wants all the photos. There are about 1,400 photos across 3 forms. Downloading them one by one from each record is not possible for us. Is there a  ...

### Block 2: Hello [person-1], yes. In the web app go ... (best score 0.333)

Id: b8d8980e8c
Keywords: bundle, photo, form, link, record, work, app, choose, date, days, download, email, export, field, file
Closest: exports/csv-and-geojson.md > CSV (0.333); index.md > Sections (0.333); exports/csv-and-geojson.md > Filters (0.267)

```

In the demo transcript the blocks on validation rules (3) and conflicts (5) scored above the threshold and are listed under "Covered blocks": the docs already say what the salesperson said.

## 4. Drift watch, first run

On the first run every gap is new. The state goes to `docs/.source-to-docs/drift.json`.

```
$ source-to-docs drift docs --sources clean
# Drift watch

Compared with: never (first run, every gap is new)

## demo-transcript.md

closed: 0, still open: 0, new: 4
- new: Demo call, Northwind Field Logger, 45 minutes. Attendees: ... (bc1fa70bd3)
- new: You can schedule that. In the project, under ... (2772e51aec)
- new: The GeoJSON export is always WGS 84, which ... (03a3ad0759)
- new: Last one. We have about 40 forms built ... (29c32a1544)

## support-thread.md

closed: 0, still open: 0, new: 4
- new: Getting all photos out of a project at ... (3fda2129a2)
- new: Hello [person-1], yes. In the web app go ... (b8d8980e8c)
- new: That worked, thanks. One more thing: the link ... (e34a34bbf6)
- new: Clear, thank you. Also, our field team asked ... (28ae2cbdf0)

```

## 5. The judgment part

This is where the Claude Code skill (`/source-to-docs`) does its work: read `reports/gaps-support-thread.md` and `clean/support-thread.md`, decide which candidate gaps are real, and write the doc changes. For this walkthrough the result is in `proposed/`:

- `proposed/photo-bundle.md`: a new page `docs/exports/photo-bundle.md`.
- One line changed in `docs/exports/csv-and-geojson.md` ("Photos in exports" now points to the new page).
- Two lines added in `docs/sync/offline-sync.md` (the failed-record filter).
- `proposed/provenance.md`: the quotes each change rests on, written to `docs/.source-to-docs/provenance.md`.

Block 1 of the support thread (the customer's problem statement) and block 2 (the answer) describe one gap. Block 3 (sign-in on the link, size limit) became the "Limits" section. Block 4 became the filter note. The photo counts and the Friday deadline were left out: they are about one customer, not the product.

## 6. Propose: branch, commit, print the pull request body

Dry run by default. `--open-pr` would hand the same body to `gh pr create`. The tool never merges and refuses `--branch main`.

```
$ source-to-docs propose docs --branch docs/photo-bundle --title "docs: photo bundle export and failed-record filter" --provenance clean/support-thread.md
committed 3 file(s) on branch docs/photo-bundle; dry run, no pull request opened

# docs: photo bundle export and failed-record filter

## Summary

- `docs/exports/csv-and-geojson.md`: modified, +1 -1
- `docs/exports/photo-bundle.md`: added, +21 -0
- `docs/sync/offline-sync.md`: modified, +2 -0

## Provenance

- Clean source: `clean/support-thread.md`
- Original: `sources/support-thread.md`
- Scrubbed at: 2026-10-16T10:43:17+00:00

### Quotes

Source: clean/support-thread.md

- `exports/photo-bundle.md` (new): "In the web app go to Project, then Exports, then choose Photo bundle. It makes a zip file with one folder per form and the photos named after the record id and the field short name."
- `exports/photo-bundle.md`, Limits: "The bundle limit is 20 GB per request. Above that, filter by form or date range and make more than one bundle. The limit and the 7-day link are the same for all plans."
- `exports/photo-bundle.md`, sign-in note: "The link opens for the person who requested the bundle, so a sign-in is expected if the browser session had expired."
- `exports/csv-and-geojson.md`, Photos in exports: pointer to the new page.
- `sync/offline-sync.md`, Sync status: "on the record list, tap the filter icon and choose Status, then Failed. That filter stays until you clear it."

Not written down: the 1,400 and 10,000 photo counts (customer-specific), the Friday deadline, anything about the drainage survey.

## Reviewer checklist

- [ ] Every change traces back to a quote in the provenance section.
- [ ] No personal data (names, emails, phone numbers, tokens) reached the docs.
- [ ] Terminology matches the rest of the site.
- [ ] Commands and settings were tried, not copied from the source.
- [ ] Nothing in the source that is wrong or outdated was written down as fact.

Opened by source-to-docs. A person reviews and merges; the tool never does.

$ git log --oneline
beb1c57 docs: photo bundle export and failed-record filter
35f0a3d docs: initial site

$ git status --short
?? clean/
?? docs/.source-to-docs/
?? reports/

```

`clean/`, `reports/` and `docs/.source-to-docs/` stay untracked: the proposal only takes markdown under the docs folder, state excluded.

## 7. Drift watch, second run

Same command as step 4. The four support-thread gaps are closed by the proposed commit; the four demo-transcript gaps are still open and would be the next piece of work.

```
$ source-to-docs drift docs --sources clean
# Drift watch

Compared with: 2026-10-16T10:43:17+00:00

## demo-transcript.md

closed: 0, still open: 4, new: 0
- still open: Demo call, Northwind Field Logger, 45 minutes. Attendees: ... (bc1fa70bd3)
- still open: You can schedule that. In the project, under ... (2772e51aec)
- still open: The GeoJSON export is always WGS 84, which ... (03a3ad0759)
- still open: Last one. We have about 40 forms built ... (29c32a1544)

## support-thread.md

closed: 4, still open: 0, new: 0
- closed: Getting all photos out of a project at ... (3fda2129a2)
- closed: Hello [person-1], yes. In the web app go ... (b8d8980e8c)
- closed: That worked, thanks. One more thing: the link ... (e34a34bbf6)
- closed: Clear, thank you. Also, our field team asked ... (28ae2cbdf0)

```

Exit code is 0 either way. The watch reports; people decide.
