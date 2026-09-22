#!/usr/bin/env python3
"""Validate registered portable packages offline, without executing their helpers."""

import argparse
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from check import anchors, links
from update import prose


def validate(root):
    root = Path(root)
    names = json.loads((root / "skills.json").read_text())
    if (not isinstance(names, list) or not names
            or any(not isinstance(n, str) or len(n) > 64
                   or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", n) for n in names)
            or any(n in {"default", "nix-skills"} for n in names)
            or names != sorted(set(names))):
        raise ValueError("Registry must be a sorted unique list of valid skill names")
    directory = root / "skills"
    if directory.is_symlink() or set(p.name for p in directory.iterdir()) != set(names):
        raise ValueError("Registry must exactly match skill directories")
    for name in names:
        package = directory / name
        if package.is_symlink() or not package.is_dir():
            raise ValueError(f"Invalid skill directory: {name}")
        for path in package.rglob("*"):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise ValueError(f"Unsupported package entry: {path}")
        text = (package / "SKILL.md").read_text()
        match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        if not match or len(match[1].splitlines()) != 2:
            raise ValueError(f"Expected exactly name and description frontmatter: {name}")
        for field in ("name", "description"):
            values = re.findall(rf"^{field}: (.+)$", match[1], re.M)
            if len(values) != 1 or not values[0].strip() or values[0].strip().lower() in {
                    "|", ">", "null", "true", "false", "yes", "no", "on", "off", '""', "''"}:
                raise ValueError(f"Expected one plain single-line {field}: {name}")
            if field == "name" and values[0] != name:
                raise ValueError(f"Frontmatter name differs from directory: {name}")
            if field == "description" and (not values[0][0].isalpha()
                    or ": " in values[0] or " #" in values[0]):
                raise ValueError(f"Use a plain text description starting with a letter: {name}")
        if not text[match.end():].strip():
            raise ValueError(f"Empty instructions: {name}")
        for path in package.rglob("*.md"):
            text = path.read_text()
            lines = []
            prose(text, lambda line: lines.append(line) or line)
            visible = "".join(lines)
            if (re.search(r"@docroot@|@generated@|\{\{#|@_at_", visible)
                    or (path == package / "SKILL.md"
                        and re.search(r"\b(?:TODO|FIXME|TBD)\b", visible))):
                raise ValueError(f"Unfinished placeholder: {path}")
            targets = links(text) + re.findall(r"^\s*\[[^\]]+\]:\s*<?([^\s>]+)>?", visible, re.M)
            for link in targets:
                parsed = urlsplit(link)
                if parsed.scheme:
                    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
                        raise ValueError(f"Unsupported URL: {link}")
                    continue
                if parsed.netloc or unquote(parsed.path).startswith("/") or "\\" in unquote(parsed.path):
                    raise ValueError(f"Nonportable resource link: {link}")
                target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
                if not target.is_relative_to(package.resolve()) or not target.is_file():
                    raise ValueError(f"Missing/escaping resource: {link}")
                if parsed.fragment and unquote(parsed.fragment) not in anchors(target.read_text()):
                    raise ValueError(f"Missing resource anchor: {link}")
    return names


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(f"Validated {len(validate(args.root))} registered skill packages (offline)")
