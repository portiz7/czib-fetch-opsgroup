# czib-fetch-opsgroup

Source repo 2 of 2 in a small pipeline that feeds the
[Test_2_CZIB](https://github.com/portiz7/test_2_czib) conflict-zone dashboard.

```
czib-fetch-easa                     ─┐
czib-fetch-opsgroup    (this repo)   ├─▶ conflict-zones-combine ─▶ Test_2_CZIB (dashboard)
                                     ─┘
```

## What this repo does

Every 6 hours (and on manual `workflow_dispatch`), `scripts/fetch_opsgroup.py`:

1. Pulls OpsGroup's public "Middle East Airspace: Current Operational Picture" blog
   post — a country-by-country operational rundown, no login required.
2. Writes the raw, unprocessed result to `data/raw_opsgroup.json`, and commits it if it
   changed.

This is the most fragile parser in the whole pipeline — OpsGroup could restyle their
blog post at any time without notice. If parsing fails, this repo just writes an empty
`country_notes` object and logs a warning rather than guessing; downstream,
[conflict-zones-combine](https://github.com/portiz7/conflict-zones-combine) falls back to whatever it last
had for OpsGroup.

This repo does **no** cleaning, deduplication, cross-referencing with other sources, or
AI synthesis — that all happens downstream in conflict-zones-combine, which reads this repo's
`data/raw_opsgroup.json` directly over `https://raw.githubusercontent.com/...` (this
repo is public specifically so that read needs no auth token).

## Local run

```
pip install -r requirements.txt
python scripts/fetch_opsgroup.py
```
