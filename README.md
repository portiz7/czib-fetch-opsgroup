# czib-fetch-opsgroup

Source repo 2 of 3 in a small pipeline that feeds the
[Test_2_CZIB](https://github.com/portiz7/test_2_czib) conflict-zone dashboard. Despite the
name, this repo now covers **two** independent community/aviation-press sources (kept in the
same repo rather than split further, per project decision), merged into a single output file
— same pattern as czib-fetch-easa merging CZIBs + Information Notes into one `raw_easa.json`.

```
czib-fetch-easa                     ─┐
czib-fetch-opsgroup    (this repo)   ├─▶ conflict-zones-combine ─▶ Test_2_CZIB (dashboard)
                                     ─┘
```

## What this repo does

Every 6 hours (and on manual `workflow_dispatch`), `scripts/fetch_all.py` runs both sources
and writes **one** `data/raw_opsgroup.json`, committed if it changed:

```json
{
  "fetched_at": "...",
  "opsgroup": { "source": "OpsGroup", "fetched_at": "...", "countries": { "Kuwait": {...}, ... } },
  "safeairspace": { "source": "safeairspace.net", "fetched_at": "...", "countries": { "haiti": {...}, ... } }
}
```

`opsgroup.countries` and `safeairspace.countries` share the same per-country record shape
(this was NOT true in an earlier version - OpsGroup used to just be a flat `{country: text}`
map while safeairspace had a full structured object; unified after review to remove the
inconsistency):

```json
{
  "country": "Kuwait",
  "risk_level_number": null,
  "risk_level_label": "None",
  "narrative": "...",
  "related_reading": [],
  "warnings": []
}
```

`risk_level_label`/`related_reading`/`warnings` are always present with an explicit "empty"
value (`"None"` / `[]` / `[]`) rather than `null`, specifically so nothing downstream needs a
null-check for a field a given source just doesn't have (OpsGroup never has a risk rating or
a structured warnings list - only safeairspace.net does). safeairspace.net's records also
carry two extra fields beyond the shared shape, `slug` and `url`, which are harmless to keep.

1. **OpsGroup** (`scripts/fetch_opsgroup.py`, `fetch_opsgroup_picture()`) pulls OpsGroup's
   public "Middle East Airspace: Current Operational Picture" blog post — a country-by-country
   operational rundown, no login required. A heading covering several countries at once (e.g.
   "Armenia/Azerbaijan/Afghanistan", confirmed live) is split into one record per country, all
   sharing that heading's paragraph as `narrative` - so every consumer gets one country per key,
   never a combined key.
2. **safeairspace.net** (`scripts/fetch_safeairspace.py`, two-phase: `get_country_list()` /
   `parse_country_page()`) scrapes every country page discovered from its `/countries/` index
   (currently ~44 countries, not just the ones already in this project's curated FIR list),
   pulling each country's risk level, narrative, and the full list of official warnings
   (source, reference, issued/valid dates, plain-English summary, and the raw legal/NOTAM
   text).

**fetch_opsgroup.py** is the most fragile parser in the whole pipeline — OpsGroup could
restyle their blog post at any time without notice. The page also mixes two unrelated
`<h4>` sections (a dated "Recent Developments" news log and the actual "Current Airspace
Picture" per-country rundown) - the parser anchors on the "Current Airspace Picture" marker
text specifically so it doesn't scrape the dated headlines as if they were countries (a real
bug found and fixed during development). If parsing fails, it just returns an empty
`countries` object and logs a warning rather than guessing - this has genuinely happened
in production from a plain network timeout to ops.group, not a parser bug.

**fetch_safeairspace.py** skips a country entirely (with a log warning) rather than guessing
if its page can't be confidently parsed.

Neither script does cleaning, deduplication, cross-referencing with other sources, or AI
synthesis — that all happens downstream in
[conflict-zones-combine](https://github.com/portiz7/conflict-zones-combine), which reads
this repo's `data/raw_opsgroup.json` directly over `https://raw.githubusercontent.com/...`
(this repo is public specifically so that read needs no auth token).

## Local run

```
pip install -r requirements.txt
python scripts/fetch_all.py            # matches production - writes the combined data/raw_opsgroup.json
python scripts/fetch_opsgroup.py       # OpsGroup only, for quick iteration
python scripts/fetch_safeairspace.py   # safeairspace.net only, for quick iteration
```
