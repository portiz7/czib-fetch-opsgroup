#!/usr/bin/env python3
"""Throwaway debug script - inspects safeairspace.net's structure: how to
discover the full country list, and what fields a country page exposes."""
import re
import sys
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ConflictZoneDashboardBot/1.0)"}
HOME_URL = "https://safeairspace.net/"
SAMPLE_URL = "https://safeairspace.net/haiti/"


def log(msg):
    print(msg, file=sys.stderr)


def main():
    log(f"=== HOMEPAGE: {HOME_URL} ===")
    r = requests.get(HOME_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Look for internal links that look like country pages (single path segment)
    links = soup.find_all("a", href=True)
    country_like = []
    seen = set()
    for a in links:
        href = a["href"]
        m = re.match(r"^(?:https://safeairspace\.net)?/([a-z0-9-]+)/?$", href)
        if m and m.group(1) not in ("", "wp-content", "wp-admin", "feed", "sitemap", "privacy-policy", "about", "contact", "blog"):
            slug = m.group(1)
            if slug not in seen:
                seen.add(slug)
                country_like.append((slug, a.get_text(" ", strip=True)))
    log(f"Found {len(country_like)} country-like links:")
    for slug, text in country_like[:60]:
        log(f"  /{slug}/  text={text!r}")

    log("")
    log(f"=== SAMPLE COUNTRY PAGE: {SAMPLE_URL} ===")
    r2 = requests.get(SAMPLE_URL, headers=HEADERS, timeout=20)
    r2.raise_for_status()
    soup2 = BeautifulSoup(r2.text, "html.parser")

    for tag in ["h1", "h2", "h3", "h4", "strong"]:
        found = soup2.find_all(tag)
        log(f"--- <{tag}> tags ({len(found)}) ---")
        for el in found[:25]:
            log(f"  {el.get_text(' ', strip=True)[:120]!r}")

    main_tag = soup2.find("main") or soup2.find(["article"])
    log(f"main/article found: {main_tag is not None}")
    if main_tag:
        log("=== main/article full text, first 6000 chars ===")
        log(main_tag.get_text("\n", strip=True)[:6000])
    else:
        log("=== body text, first 6000 chars ===")
        log(soup2.get_text("\n", strip=True)[:6000])


if __name__ == "__main__":
    main()
