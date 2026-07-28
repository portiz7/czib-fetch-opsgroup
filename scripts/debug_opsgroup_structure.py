#!/usr/bin/env python3
"""Throwaway debug script - dumps the real structure of the OpsGroup blog
post so the scraper can be rewritten against actual markup, same method
used to fix czib-fetch-easa."""
import sys
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ConflictZoneDashboardBot/1.0)"}
URL = "https://ops.group/blog/middle-east-airspace-current-operational-picture/"


def log(msg):
    print(msg, file=sys.stderr)


def main():
    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    for tag in ["h1", "h2", "h3", "h4", "h5", "strong"]:
        found = soup.find_all(tag)
        log(f"--- <{tag}> tags ({len(found)}) ---")
        for el in found[:40]:
            log(f"  {el.get_text(' ', strip=True)[:100]!r}")

    log("")
    log(f"=== total <table> tags: {len(soup.find_all('table'))} ===")
    log(f"=== total <article> tags: {len(soup.find_all('article'))} ===")

    article = soup.find("article") or soup.find(class_=lambda c: c and "content" in c.lower())
    if article:
        log(f"=== article/content container class={article.get('class')} - first 6000 chars of text ===")
        log(article.get_text("\n", strip=True)[:6000])
    else:
        log("no <article>/content container found - dumping body text[:6000]")
        log(soup.get_text("\n", strip=True)[:6000])


if __name__ == "__main__":
    main()
