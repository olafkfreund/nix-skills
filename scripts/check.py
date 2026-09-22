#!/usr/bin/env python3
"""Offline validation of the portable skill and automated-update boundaries."""

import argparse
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from update import GENERATED, PACKAGE, UPSTREAM, digest, prose, run


def anchors(text):
    found = set(re.findall(r'id="([^"]+)"', text))
    for title in re.findall(r"^#{1,6} (.+)$", text, re.M):
        found.add(re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-"))
    return found


def links(text):
    result = []

    def collect(line):
        result.extend(re.findall(r"\]\(([^\s)]+)\)", line))
        result.extend(re.findall(r'href="([^"]+)"', line))
        return line

    prose(text, collect)
    return result


def validate(package=PACKAGE):
    package = package.resolve()
    manifest = json.loads((package / "sources.json").read_text())
    if manifest["upstream"] != UPSTREAM or not re.fullmatch(r"[0-9a-f]{40}", manifest["revision"]):
        raise ValueError("Invalid upstream provenance")
    if not re.fullmatch(r"\d+\.\d+\.\d+", manifest["release"]) or manifest["nix_version"] != manifest["release"]:
        raise ValueError("Invalid release/version")
    if not manifest["selection"]["sections"] or not manifest["selection"]["builtins"]:
        raise ValueError("Empty reference selection")
    for hashes in [manifest["inputs"], manifest["outputs"], manifest["language_inputs"]]:
        if not hashes or any(not re.fullmatch(r"[0-9a-f]{64}", h) for h in hashes.values()):
            raise ValueError("Missing/invalid source hashes")
    if set(manifest["outputs"]) != GENERATED - {"sources.json"}:
        raise ValueError("Unexpected generated outputs")
    actual = {str(p.relative_to(package)) for p in package.rglob("*") if p.is_file()}
    if actual != GENERATED | {"SKILL.md"} or any(p.is_symlink() for p in package.rglob("*")):
        raise ValueError("Unexpected package files or symlinks")
    for name, expected in manifest["outputs"].items():
        if digest((package / name).read_bytes()) != expected:
            raise ValueError(f"Content hash mismatch: {name}")
    skill = (package / "SKILL.md").read_text()
    if not skill.startswith("---\n") or "\n---\n" not in skill[4:]:
        raise ValueError("Missing skill frontmatter")
    frontmatter = skill.split("---", 2)[1]
    if not re.search(r"^name: nix-language$", frontmatter, re.M) or not re.search(r"^description: .+", frontmatter, re.M):
        raise ValueError("Missing skill name/description")
    for path in package.rglob("*.md"):
        text = path.read_text()
        if re.search(r"@docroot@|@generated@|\{\{#|@_at_", text):
            raise ValueError(f"Unresolved source directive: {path}")
        for link in links(text):
            parsed = urlsplit(link)
            if parsed.scheme:
                if parsed.scheme not in {"http", "https"}:
                    raise ValueError(f"Unsupported link: {link}")
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not target.is_relative_to(package) or not target.is_file():
                raise ValueError(f"Broken/escaping package link: {link}")
            if parsed.fragment and unquote(parsed.fragment) not in anchors(target.read_text()):
                raise ValueError(f"Missing local anchor: {link}")
    return manifest


def boundary(base, package=PACKAGE):
    """Compare both git files and curated JSON fields against a trusted base commit."""
    prefix = "skills/nix-language/"
    changes = run("git", "diff", "--name-only", base, "--").splitlines()
    if set(changes) - {prefix + name for name in GENERATED}:
        raise ValueError("Automatic update changed non-generated files")
    old = json.loads(run("git", "show", base + ":" + prefix + "sources.json"))
    new = validate(package)
    if old["selection"] != new["selection"] or old["upstream"] != new["upstream"]:
        raise ValueError("Automatic update changed curated selection/upstream")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Trusted base commit for automated-update boundary checks")
    args = parser.parse_args()
    validate()
    if args.base:
        boundary(args.base)
    print("Skill metadata, links, provenance, hashes, and file boundaries passed")
