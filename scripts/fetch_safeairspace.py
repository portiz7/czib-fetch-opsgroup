#!/usr/bin/env python3
"""
fetch_safeairspace.py
----------------------
Third source in this repo (alongside OpsGroup's own blog): safeairspace.net,
a community-run country-by-country airspace risk tracker. Two-phase scraper,
same pattern as the EASA CZIB scraper in czib-fetch-easa:

  Phase 1 - get_country_list(): the /countries/ index page -> country slugs
  Phase 2 - parse_country_page(): one country page -> structured record

Real page structure (confirmed via a live fetch, not guessed):
  - /countries/ lists every country as a plain-slug link (safeairspace.net/{slug}/);
    a handful of non-country slugs ("about", "countries", "summary") are excluded.
  - Each country page has a fixed CMS layout inside #page-country-info-wrap:
      <h3 class="page-country-summary-risk-level page-country-summary-risk-level-N">
        Risk Level: <word> - <label>
      </h3>
      ...narrative <p> paragraphs, optionally a "Read: <link>" paragraph...
      <h3 class="page-country-warninglist">Current warnings list :</h3>
      <table>...one row per warning: Source | Reference | Issued | Valid to...</table>
      <div class="page-country-sources">
        <div class="page-country-source">       <- one per warning, SAME ORDER as the table rows
          ...source/reference/issued text...
          <div class="page-country-source-plain">Plain English: <text></div>
          ...raw NOTAM/AIC legal text follows as further siblings...
        </div>
        ...
      </div>
  The risk level number lives right in the CSS class name (more reliable than
  parsing "One"/"Two"/"Three"/"Four" out of the heading text). The summary
  table and the detailed "Plain English"/raw-text blocks are two separate
  DOM structures for the same warnings, matched here by position/order.

Output: data/raw_safeairspace.json — raw, unprocessed data for this source
only. Cleaning/deduplication/cross-referencing happens downstream in
conflict-zones-combine, not here.
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://safeairspace.net"
COUNTRIES_INDEX_URL = f"{BASE_URL}/countries/"
NON_COUNTRY_SLUGS = {"about", "countries", "summary"}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ConflictZoneDashboardBot/1.0)"}
TIMEOUT = 20
RETRIES = 3
RETRY_BACKOFF = 2
REQUEST_DELAY = 0.4

OUT_PATH = "data/raw_safeairspace.json"


def log(msg):
    print(f"[fetch_safeairspace] {msg}", file=sys.stderr)


def _get(url):
    last_exc = None
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            return r
        except Exception as e:
            last_exc = e
            log(f"  GET {url} failed (attempt {attempt}/{RETRIES}): {e}")
            if attempt < RETRIES:
                time.sleep(RETRY_BACKOFF * attempt)
    raise last_exc


def _clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def get_country_list():
    """Phase 1: scrape /countries/ for every country slug."""
    log(f"Fetching country index: {COUNTRIES_INDEX_URL}")
    try:
        r = _get(COUNTRIES_INDEX_URL)
    except Exception as e:
        log(f"Country index fetch failed permanently: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    slugs = []
    seen = set()
    for a in soup.find_all("a", href=True):
        m = re.match(r"^(?:https://safeairspace\.net)?/([a-z0-9-]+)/?$", a["href"])
        if not m:
            continue
        slug = m.group(1)
        if slug in NON_COUNTRY_SLUGS or slug in seen:
            continue
        seen.add(slug)
        slugs.append(slug)

    slugs.sort()
    log(f"Country index parsed: {len(slugs)} countries")
    return [(slug, f"{BASE_URL}/{slug}/") for slug in slugs]


def _parse_risk_level(soup):
    h3 = soup.find("h3", class_=lambda c: c and "page-country-summary-risk-level" in c)
    if not h3:
        return None, None
    number = None
    for cls in h3.get("class", []):
        m = re.match(r"page-country-summary-risk-level-(\d+)$", cls)
        if m:
            number = int(m.group(1))
    text = _clean(h3.get_text(" ", strip=True))
    label = None
    if " - " in text:
        label = text.split(" - ", 1)[1].strip()
    return number, label


def _parse_narrative(soup, risk_h3, warnings_h3):
    """Collects <p> paragraphs between the risk-level heading and the
    warnings-list heading (whichever of those two exists), pulling out the
    optional "Read: <link>" reference paragraph separately."""
    if risk_h3 is None:
        return "", None

    narrative_parts = []
    related_reading = None
    for el in risk_h3.find_all_next():
        if warnings_h3 is not None and el is warnings_h3:
            break
        if getattr(el, "name", None) != "p":
            continue
        text = _clean(el.get_text(" ", strip=True))
        if not text:
            continue
        if text.lower().startswith("read:"):
            a = el.find("a", href=True)
            if a:
                related_reading = {"title": _clean(a.get_text(" ", strip=True)), "url": a["href"]}
            continue
        if "about risk levels" in text.lower():
            continue
        narrative_parts.append(text)

    return " ".join(narrative_parts), related_reading


def _parse_warnings_table(warnings_h3):
    if warnings_h3 is None:
        return []
    table = warnings_h3.find_next("table")
    if not table:
        return []
    rows = table.find_all("tr")
    out = []
    for row in rows:
        cells = [_clean(c.get_text(" ", strip=True)) for c in row.find_all(["td", "th"])]
        if len(cells) < 4 or cells[0].lower() == "source":  # skip header row
            continue
        out.append({
            "source": cells[0],
            "reference": cells[1],
            "issued": cells[2],
            "valid_until": cells[3],
        })
    return out


def _parse_warning_detail_blocks(soup):
    container = soup.find("div", class_="page-country-sources")
    if not container:
        return []
    blocks = container.find_all("div", class_="page-country-source", recursive=False)
    details = []
    for block in blocks:
        plain_div = block.find("div", class_="page-country-source-plain")
        plain_english = ""
        raw_text = ""
        if plain_div:
            plain_english = re.sub(
                r"^Plain English:\s*", "", _clean(plain_div.get_text(" ", strip=True)), flags=re.IGNORECASE
            ).strip()
            raw_parts = [_clean(sib.get_text(" ", strip=True)) for sib in plain_div.find_next_siblings()]
            raw_text = " ".join(p for p in raw_parts if p)
        details.append({"plain_english": plain_english, "raw_text": raw_text})
    return details


def parse_country_page(slug, url):
    """Phase 2: scrape one country page into a full normalized record."""
    log(f"Fetching country page: {url}")
    try:
        r = _get(url)
    except Exception as e:
        log(f"  Country page fetch failed permanently: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    wrap = soup.find(id="page-country-info-wrap") or soup.find("article") or soup

    h2s = wrap.find_all("h2")
    name = next((_clean(h.get_text(" ", strip=True)) for h in h2s if h.get_text(strip=True).lower() != "current map"), slug)

    risk_h3 = soup.find("h3", class_=lambda c: c and "page-country-summary-risk-level" in c)
    warnings_h3 = soup.find("h3", class_="page-country-warninglist")

    risk_level_number, risk_level_label = _parse_risk_level(soup)
    narrative, related_reading = _parse_narrative(soup, risk_h3, warnings_h3)

    table_rows = _parse_warnings_table(warnings_h3)
    detail_blocks = _parse_warning_detail_blocks(soup)

    warnings = []
    for i, row in enumerate(table_rows):
        entry = dict(row)
        if i < len(detail_blocks):
            entry.update(detail_blocks[i])
        else:
            entry.update({"plain_english": "", "raw_text": ""})
        warnings.append(entry)

    return {
        "slug": slug,
        "name": name,
        "url": url,
        "risk_level_number": risk_level_number,
        "risk_level_label": risk_level_label,
        "narrative": narrative,
        "related_reading": related_reading,
        "warnings": warnings,
    }


def scrape_all():
    countries = get_country_list()
    results = {}
    for i, (slug, url) in enumerate(countries):
        data = parse_country_page(slug, url)
        if data is None:
            log(f"  skipping {slug} - page parse failed")
            continue
        results[slug] = data
        if i < len(countries) - 1:
            time.sleep(REQUEST_DELAY)
    log(f"scrape_all complete: {len(results)}/{len(countries)} countries fully parsed")
    return results


def main():
    countries = scrape_all()
    out = {
        "source": "safeairspace.net",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "countries": countries,
    }
    os.makedirs("data", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    log(f"Wrote {OUT_PATH} with {len(countries)} countries")


if __name__ == "__main__":
    main()
