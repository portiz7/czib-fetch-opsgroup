# czib-fetch-opsgroup

Source repo 2 of 3 in a small pipeline that feeds the
[Test_2_CZIB](https://github.com/portiz7/test_2_czib) conflict-zone dashboard. Despite the
name, this repo now covers **two** independent community/aviation-press sources (kept in the
same repo rather than split further, per project decision).

```
czib-fetch-easa                     ─┐
czib-fetch-opsgroup    (this repo)   ├─▶ conflict-zones-combine ─▶ Test_2_CZIB (dashboard)
                                     ─┘
```

## What this repo does

Every 6 hours (and on manual `workflow_dispatch`):

1. `scripts/fetch_opsgroup.py` pulls OpsGroup's public "Middle East Airspace: Current
   Operational Picture" blog post — a country-by-country operational rundown, no login
   required — and writes `data/raw_opsgroup.json`.
2. `scripts/fetch_safeairspace.py` scrapes every country page on
   [safeairspace.net](https://safeairspace.net) (discovered from its `/countries/` index —
   currently ~44 countries, not just the ones already in this project's curated FIR list),
   pulling each country's risk level, narrative, and the full list of official warnings
   (source, reference, issued/valid dates, plain-English summary, and the raw legal/NOTAM
   text), and writes `data/raw_safeairspace.json`.

Both are committed if they changed.

**fetch_opsgroup.py** is the most fragile parser in the whole pipeline — OpsGroup could
restyle their blog post at any time without notice. The page also mixes two unrelated
`<h4>` sections (a dated "Recent Developments" news log and the actual "Current Airspace
Picture" per-country rundown) - the parser anchors on the "Current Airspace Picture" marker
text specifically so it doesn't scrape the dated headlines as if they were countries (a real
bug found and fixed during development). If parsing fails, this repo just writes an empty
`country_notes` object and logs a warning rather than guessing.

**fetch_safeairspace.py** is a two-phase scraper (`get_country_list()` /
`parse_country_page()`), same pattern as czib-fetch-easa's CZIB scraper — see that repo's
README for why this pattern is used. Skips a country entirely (with a log warning) rather
than guessing if its page can't be confidently parsed.

Neither script does cleaning, deduplication, cross-referencing with other sources, or AI
synthesis — that all happens downstream in
[conflict-zones-combine](https://github.com/portiz7/conflict-zones-combine), which reads
this repo's `data/raw_opsgroup.json` and `data/raw_safeairspace.json` directly over
`https://raw.githubusercontent.com/...` (this repo is public specifically so that read
needs no auth token).

## Local run

```
pip install -r requirements.txt
python scripts/fetch_opsgroup.py
python scripts/fetch_safeairspace.py
```
