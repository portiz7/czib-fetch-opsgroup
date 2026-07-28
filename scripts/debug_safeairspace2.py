#!/usr/bin/env python3
"""Debug round 2: dump the real tag/class structure of the warnings section
on a safeairspace.net country page, and confirm the /countries/ index page."""
import sys
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ConflictZoneDashboardBot/1.0)"}


def log(msg):
    print(msg, file=sys.stderr)


def main():
    log("=== /countries/ index page ===")
    r = requests.get("https://safeairspace.net/countries/", headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    import re
    links = soup.find_all("a", href=True)
    slugs = set()
    for a in links:
        m = re.match(r"^(?:https://safeairspace\.net)?/([a-z0-9-]+)/?$", a["href"])
        if m:
            slugs.add(m.group(1))
    log(f"{len(slugs)} unique slugs on /countries/: {sorted(slugs)}")

    log("")
    log("=== Haiti page - warnings section structure ===")
    r2 = requests.get("https://safeairspace.net/haiti/", headers=HEADERS, timeout=20)
    r2.raise_for_status()
    soup2 = BeautifulSoup(r2.text, "html.parser")

    heading = soup2.find(string=lambda s: s and "Current warnings list" in s)
    log(f"warnings heading found: {heading is not None}")
    if heading:
        container = heading.find_parent(["h1", "h2", "h3", "h4", "div"])
        log(f"heading container: <{container.name} class={container.get('class')}>")
        # Walk forward through siblings/descendants, dump tag+class+short text
        node = container.find_next_sibling()
        count = 0
        while node and count < 40:
            if hasattr(node, "name") and node.name:
                text_preview = node.get_text(" ", strip=True)[:80]
                log(f"  <{node.name} class={node.get('class')}> text={text_preview!r}")
                # also peek one level of children for the first couple siblings
                if count < 6:
                    for child in node.find_all(True, recursive=False)[:6]:
                        log(f"      child <{child.name} class={child.get('class')}> text={child.get_text(' ', strip=True)[:60]!r}")
            node = node.find_next_sibling()
            count += 1

    log("")
    log("=== risk level heading structure ===")
    risk_h = soup2.find(string=lambda s: s and "Risk Level" in s)
    if risk_h:
        rc = risk_h.find_parent(["h1", "h2", "h3"])
        log(f"risk container: <{rc.name} class={rc.get('class')}> text={rc.get_text(' ', strip=True)!r}")


if __name__ == "__main__":
    main()
