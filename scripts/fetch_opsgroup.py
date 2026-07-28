#!/usr/bin/env python3
"""
fetch_opsgroup.py
------------------
Fetches OpsGroup's public "Middle East Airspace: Current Operational Picture"
blog post, which gives a country-by-country operational rundown.

Structure being parsed: '#### CountryName' heading followed by a paragraph.
This is the most fragile parser in the whole pipeline — OpsGroup could
restyle their blog at any time. If it returns nothing, it just logs a
warning and writes an empty result rather than guessing; conflict-zones-combine falls
back to whatever it last had for OpsGroup when this happens.

Output: data/raw_opsgroup.json — raw, unprocessed data for this source only.
Cleaning, deduplication and cross-referencing against other sources happens
downstream in the conflict-zones-combine repo, not here.
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

OPSGROUP_URL = "https://ops.group/blog/middle-east-airspace-current-operational-picture/"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ConflictZoneDashboardBot/1.0)"}
TIMEOUT = 20
OUT_PATH = "data/raw_opsgroup.json"


def log(msg):
    print(f"[fetch_opsgroup] {msg}", file=sys.stderr)


def fetch_opsgroup_picture():
    try:
        r = requests.get(OPSGROUP_URL, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        log(f"OpsGroup fetch failed: {e}")
        return {}

    result = {}
    for h4 in soup.select("h4"):
        country = h4.get_text(strip=True)
        if not country or len(country) > 40:
            continue
        para = h4.find_next_sibling("p")
        if para:
            result[country] = para.get_text(" ", strip=True)
    log(f"OpsGroup country notes parsed: {len(result)}")
    return result


def main():
    out = {
        "source": "OpsGroup",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "country_notes": fetch_opsgroup_picture(),
    }
    os.makedirs("data", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    log(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
