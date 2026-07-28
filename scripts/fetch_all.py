#!/usr/bin/env python3
"""
fetch_all.py
------------
Orchestrator for this repo's two independent sources - same pattern as
czib-fetch-easa's fetch_easa.py, which merges its CZIB scraper and
Information Notes fetch into one data/raw_easa.json rather than two files.

  1. OpsGroup's blog post -> fetch_opsgroup.fetch_opsgroup_picture()
  2. safeairspace.net, all countries -> fetch_safeairspace.scrape_all()

Both scripts remain independently runnable (`python scripts/fetch_opsgroup.py`
or `python scripts/fetch_safeairspace.py`) for local testing against a
single source; this script is what the pipeline actually runs, and is what
writes the single data/raw_opsgroup.json that conflict-zones-combine reads.
"""

import json
import os
import sys
from datetime import datetime, timezone

from fetch_opsgroup import fetch_opsgroup_picture
from fetch_safeairspace import scrape_all as scrape_safeairspace

OUT_PATH = "data/raw_opsgroup.json"


def log(msg):
    print(f"[fetch_all] {msg}", file=sys.stderr)


def main():
    now = datetime.now(timezone.utc).isoformat()

    log("Fetching OpsGroup...")
    opsgroup_notes = fetch_opsgroup_picture()

    log("Fetching safeairspace.net...")
    safeairspace_countries = scrape_safeairspace()

    out = {
        "fetched_at": now,
        "opsgroup": {
            "source": "OpsGroup",
            "fetched_at": now,
            "country_notes": opsgroup_notes,
        },
        "safeairspace": {
            "source": "safeairspace.net",
            "fetched_at": now,
            "countries": safeairspace_countries,
        },
    }

    os.makedirs("data", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    log(f"Wrote {OUT_PATH} ({len(opsgroup_notes)} OpsGroup countries, {len(safeairspace_countries)} safeairspace.net countries)")


if __name__ == "__main__":
    main()
