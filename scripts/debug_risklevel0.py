#!/usr/bin/env python3
"""Throwaway debug: what does the risk-level heading actually look like on
a country page where our parser produced risk_level_number=0?"""
import sys
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ConflictZoneDashboardBot/1.0)"}


def log(msg):
    print(msg, file=sys.stderr)


def main():
    for slug in ["armenia", "azerbaijan", "kenya"]:
        url = f"https://safeairspace.net/{slug}/"
        log(f"=== {url} ===")
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        h3 = soup.find("h3", class_=lambda c: c and "page-country-summary-risk-level" in c)
        if not h3:
            log("  NO risk-level h3 found at all")
            continue
        log(f"  classes: {h3.get('class')}")
        log(f"  text: {h3.get_text(' ', strip=True)!r}")


if __name__ == "__main__":
    main()
