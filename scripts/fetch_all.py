#!/usr/bin/env python3
"""
fetch_all.py
------------
Orchestrator for this repo's source. Previously fetched OpsGroup's blog
post too, but that only ever covered 14 Middle East / Central Asia
countries (fixed by whatever that specific post happens to cover), while
safeairspace.net's own per-country pages cover every country it lists (44
and growing) with a real risk rating. OpsGroup was dropped as a source
entirely rather than kept as a redundant partial overlay - see
fetch_safeairspace.py for the actual scraper.

Output: data/raw_safeairspace.json — raw, unprocessed data for this
source only. Cleaning/deduplication/cross-referencing happens downstream
in conflict-zones-combine, not here.
"""

import json
import os
import sys
from datetime import datetime, timezone

from fetch_safeairspace import scrape_all as scrape_safeairspace

OUT_PATH = "data/raw_safeairspace.json"


def log(msg):
    print(f"[fetch_all] {msg}", file=sys.stderr)


def main():
    now = datetime.now(timezone.utc).isoformat()

    log("Fetching safeairspace.net...")
    safeairspace_countries = scrape_safeairspace()

    out = {
        "source": "safeairspace.net",
        "fetched_at": now,
        "countries": safeairspace_countries,
    }

    os.makedirs("data", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    log(f"Wrote {OUT_PATH} ({len(safeairspace_countries)} safeairspace.net countries)")


if __name__ == "__main__":
    main()
