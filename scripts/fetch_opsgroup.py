#!/usr/bin/env python3
"""
fetch_opsgroup.py
------------------
Fetches OpsGroup's public "Middle East Airspace: Current Operational Picture"
blog post, which gives a country-by-country operational rundown.

Real structure (confirmed via a live fetch): the article uses <h4> for TWO
unrelated things, not just per-country headings:
  1. "Recent Developments" - a dated news log ("July 16-17 – More US/Iran
     strikes", "July 15 – EASA updates Middle East CZIB again", ...)
  2. "Current Airspace Picture" - the actual per-country rundown (Kuwait,
     Iran, Qatar, UAE, Bahrain, ...), which is what this scraper wants.
A blind "every <h4> is a country" scrape (the original approach) mixed both
in - confirmed against live output, where date headlines like "July 16-17 –
More US/Iran strikes" ended up as fake "countries". This version anchors on
the "Current Airspace Picture" marker text and only reads <h4> elements
that come after it in document order (via find_all_next, so it doesn't
matter how deeply nested anything is), stopping once it hits page chrome
(the tags/related-posts/newsletter section that follows the country list).

This is still the most fragile parser in the whole pipeline - OpsGroup could
restyle their blog at any time. If it returns nothing, it just logs a
warning and writes an empty result rather than guessing; conflict-zones-combine
falls back to whatever it last had for OpsGroup when this happens.

Output: data/raw_opsgroup.json — raw, unprocessed data for this source only.
Cleaning, deduplication and cross-referencing against other sources happens
downstream in the conflict-zones-combine repo, not here.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

OPSGROUP_URL = "https://ops.group/blog/middle-east-airspace-current-operational-picture/"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ConflictZoneDashboardBot/1.0)"}
TIMEOUT = 20
OUT_PATH = "data/raw_opsgroup.json"

# Page chrome that follows the per-country section - hitting an <h4> matching
# any of these means the country list has ended.
STOP_MARKERS = [
    "more on the topic", "more reading", "tags:", "new posts",
    "download the", "opsgroup", "find articles", "from the",
    "trending posts", "by david", "by ",
]


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

    article = soup.find("article") or soup
    marker = article.find(string=re.compile(r"Current Airspace Picture", re.IGNORECASE))
    if not marker:
        log("'Current Airspace Picture' marker not found - page structure may have changed")
        return {}

    result = {}
    for h4 in marker.find_all_next("h4"):
        heading = h4.get_text(strip=True)
        if not heading:
            continue
        if any(m in heading.lower() for m in STOP_MARKERS):
            break  # reached the page-chrome section that follows the country list
        para = h4.find_next_sibling("p")
        if not para:
            continue
        narrative = para.get_text(" ", strip=True)
        # A heading can cover several countries at once (confirmed live:
        # "Armenia/Azerbaijan/Afghanistan" sharing one paragraph) - split so
        # every downstream consumer gets one country per key, matching
        # safeairspace.net's shape instead of needing special-case handling
        # for combined headings.
        for country in heading.split("/"):
            country = country.strip()
            if not country:
                continue
            # Same record shape as fetch_safeairspace.parse_country_page(),
            # minus what OpsGroup's blog just doesn't have (no risk rating,
            # no separate warnings list) - explicit "None"/[] rather than
            # null, so nothing downstream needs a special case for this
            # source vs. safeairspace.net.
            result[country] = {
                "country": country,
                "risk_level_number": None,
                "risk_level_label": "None",
                "narrative": narrative,
                "related_reading": [],
                "warnings": [],
            }
    log(f"OpsGroup country notes parsed: {len(result)}")
    return result


def main():
    out = {
        "source": "OpsGroup",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "countries": fetch_opsgroup_picture(),
    }
    os.makedirs("data", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    log(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
