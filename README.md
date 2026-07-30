# czib-fetch-opsgroup

Source repo 2 of 3 in a small pipeline that feeds the
[Test_2_CZIB](https://github.com/portiz7/test_2_czib) conflict-zone dashboard. The repo name
is historical — it originally scraped OpsGroup's blog too, but that source was dropped (see
"Why OpsGroup was dropped" below), so this repo now scrapes **safeairspace.net** only.

```
czib-fetch-easa                     ─┐
czib-fetch-opsgroup    (this repo)   ├─▶ conflict-zones-combine ─▶ Test_2_CZIB (dashboard)
                                     ─┘
```

## What this repo does

Every 6 hours (and on manual `workflow_dispatch`), `scripts/fetch_all.py` scrapes
safeairspace.net and writes `data/raw_safeairspace.json`, committed if it changed:

```json
{
  "source": "safeairspace.net",
  "fetched_at": "...",
  "countries": {
    "haiti": {
      "country": "Haiti",
      "risk_level_number": 1,
      "risk_level_label": "Do Not Fly",
      "narrative": "...",
      "related_reading": [],
      "warnings": [ { "source": "USA", "reference": "...", "issued": "...", "valid_until": "...", "plain_english": "...", "raw_text": "..." } ],
      "slug": "haiti",
      "url": "https://safeairspace.net/haiti/"
    },
    ...
  }
}
```

`risk_level_label`/`related_reading`/`warnings` are always present with an explicit "empty"
value (`"None"` / `[]` / `[]`) rather than `null`, so nothing downstream needs a null-check.
`risk_level_number: 0` is real data (safeairspace's own "No Warnings" tier), not a missing
value — confirmed against live pages after an earlier version mislabeled it as generic "None"
because that one heading format has no `" - "` separator to split on.

**safeairspace.net** (`scripts/fetch_safeairspace.py`, two-phase: `get_country_list()` /
`parse_country_page()`) scrapes every country page discovered from its `/countries/` index
(currently ~44 countries, not just the ones already in this project's curated FIR list),
pulling each country's risk level, narrative, and the full list of official warnings (source,
reference, issued/valid dates, plain-English summary, and the raw legal/NOTAM text). It skips
a country entirely (with a log warning) rather than guessing if its page can't be confidently
parsed.

This script does no cleaning, deduplication, cross-referencing with other sources, or AI
synthesis — that all happens downstream in
[conflict-zones-combine](https://github.com/portiz7/conflict-zones-combine), which reads
this repo's `data/raw_safeairspace.json` directly over `https://raw.githubusercontent.com/...`
(this repo is public specifically so that read needs no auth token).

## Why OpsGroup was dropped

OpsGroup's blog only ever covered whatever countries that one post happened to write about —
14 Middle East / Central Asia countries, fixed by the post's own scope, with no risk rating
and no structured warnings list. safeairspace.net covers every country it lists (44 and
growing) with an actual risk-level rating and structured, sourced warnings, making OpsGroup a
strict subset with less structure. Rather than keep a redundant partial overlay, OpsGroup
(`fetch_opsgroup.py`) was removed as a source entirely.

## Local run

```
pip install -r requirements.txt
python scripts/fetch_all.py            # matches production - writes data/raw_safeairspace.json
python scripts/fetch_safeairspace.py   # same thing, standalone
```
