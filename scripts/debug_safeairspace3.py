#!/usr/bin/env python3
"""Debug round 3: locate the detailed "Plain English" warning blocks in the
real DOM (they weren't direct siblings of the warnings table's heading)."""
import sys
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ConflictZoneDashboardBot/1.0)"}


def log(msg):
    print(msg, file=sys.stderr)


def dump_ancestors(el, label):
    log(f"=== ancestor chain for {label} ===")
    node = el
    depth = 0
    while node is not None and depth < 8:
        if hasattr(node, "name") and node.name:
            log(f"  [{depth}] <{node.name} class={node.get('class')} id={node.get('id')}>")
        node = node.parent
        depth += 1


def main():
    r = requests.get("https://safeairspace.net/haiti/", headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    plain_english = soup.find(string=lambda s: s and "Plain English" in s)
    log(f"'Plain English' text found: {plain_english is not None}")
    if plain_english:
        dump_ancestors(plain_english, "Plain English")
        # dump the immediate parent's full outer structure (siblings within its parent)
        parent = plain_english.parent
        grandparent = parent.parent if parent else None
        if grandparent:
            log(f"=== grandparent <{grandparent.name} class={grandparent.get('class')}> children ===")
            for i, child in enumerate(grandparent.find_all(True, recursive=False)):
                log(f"  child[{i}] <{child.name} class={child.get('class')}> text={child.get_text(' ', strip=True)[:80]!r}")

    # Also: how many total elements have class containing 'warning'?
    warn_els = soup.find_all(class_=lambda c: c and any("warning" in x.lower() for x in c))
    log("")
    log(f"=== {len(warn_els)} elements with a class containing 'warning' ===")
    for el in warn_els[:15]:
        log(f"  <{el.name} class={el.get('class')}> text={el.get_text(' ', strip=True)[:80]!r}")


if __name__ == "__main__":
    main()
