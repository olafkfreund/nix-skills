#!/usr/bin/env python3
"""Validate mdBook sources offline: relative links, anchors, Nix style, SUMMARY.md coverage."""

import argparse
from pathlib import Path
from urllib.parse import unquote, urlsplit

from check import anchors, links
from nix_style import findings


def validate(src):
    src = Path(src).resolve()
    pages = {p.relative_to(src).as_posix() for p in src.rglob("*.md")}
    summary = src / "SUMMARY.md"
    listed = set()
    for link in links(summary.read_text()):
        path = unquote(urlsplit(link).path)
        if path and not urlsplit(link).scheme:
            listed.add(path)
    missing = sorted(listed - pages)
    if missing:
        raise ValueError(f"SUMMARY.md lists missing pages: {missing}")
    unlisted = sorted(pages - listed - {"SUMMARY.md"})
    if unlisted:
        raise ValueError(f"Pages not listed in SUMMARY.md: {unlisted}")
    for page in sorted(pages):
        path = src / page
        text = path.read_text()
        for kind, line in findings(text):
            raise ValueError(f"Nix style ({kind}): {page}: {line}")
        for link in links(text):
            parsed = urlsplit(link)
            if parsed.scheme:
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not target.is_relative_to(src) or not target.is_file():
                raise ValueError(f"Broken link in {page}: {link}")
            if parsed.fragment and unquote(parsed.fragment) not in anchors(target.read_text()):
                raise ValueError(f"Missing anchor in {page}: {link}")
    return sorted(pages)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path)
    print(f"Validated {len(validate(parser.parse_args().src))} documentation pages (offline)")
