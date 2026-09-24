#!/usr/bin/env python3
"""Generate the site's skill catalog and update schedule from repository data, offline.

Reads skills.json, each skill's SKILL.md frontmatter description and sources.json,
and the `skill: [...]` matrix line and cron of .github/workflows/update.yml.
sources.json fields used: `upstream`, `release` or `branch`, and `revision`
(or `snapshot_sha256` for the wiki dump). Absent fields render as "—".
Licence names are detected from the shipped licence file; unknown texts fail.
"""

import argparse
import json
from pathlib import Path
import re

REPO = "https://github.com/olafkfreund/nix-skills/blob/main"


def description(skill_md):
    match = re.search(r"^description: (.+)$", skill_md.read_text(), re.M)
    return match[1].strip() if match else "—"


def licence_name(path):
    """Name the licence from the shipped file's text; unknown texts must be reviewed, never guessed."""
    text = Path(path).read_text()
    if "Apache License" in text and "Version 2.0" in text:
        return "Apache-2.0"
    if "GNU LESSER GENERAL PUBLIC LICENSE" in text and "Version 2.1" in text:
        return "LGPL-2.1"
    if "Permission is hereby granted, free of charge" in text:
        return "MIT"
    raise ValueError(f"Unrecognised licence text: {path}")


def source_link(upstream):
    github = re.match(r"https://github\.com/([^/]+/[^/]+?)/?$", upstream)
    label = github[1] if github else re.sub(r"^https?://([^/]+).*$", r"\1", upstream)
    return f"[{label}]({upstream})"


def pin(sources):
    label = f"release {sources['release']}" if sources.get("release") else (
        f"branch {sources['branch']}" if sources.get("branch") else "—")
    upstream, revision = sources.get("upstream", ""), sources.get("revision")
    if revision and upstream.startswith("https://github.com/"):
        return f"{label} at [`{revision[:12]}`]({upstream.rstrip('/')}/tree/{revision})"
    if revision:
        return f"{label} at `{revision[:12]}`"
    if sources.get("snapshot_sha256"):
        return f"dump snapshot `sha256:{sources['snapshot_sha256'][:12]}`"
    return label


def weekly(workflow):
    text = workflow.read_text()
    match = re.search(r"^\s*skill: \[([^\]]*)\]\s*$", text, re.M)
    if not match:
        raise ValueError(f"No `skill: [...]` matrix line in {workflow}")
    cron = re.search(r"cron: '([^']+)'", text)
    return [s.strip() for s in match[1].split(",") if s.strip()], cron[1] if cron else None


def render(root):
    root = Path(root)
    names = json.loads((root / "skills.json").read_text())
    repo_licence = f"Repository licence ({licence_name(root / 'LICENSE')})"
    rows, sections = [], []
    for name in names:
        package = root / "skills" / name
        sources_file = package / "sources.json"
        sources = json.loads(sources_file.read_text()) if sources_file.is_file() else None
        licence_file = next((f for f in ("LICENSE", "COPYING") if (package / f).is_file()), None)
        licence = (f"[{licence_name(package / licence_file)}]({REPO}/skills/{name}/{licence_file})"
                   if licence_file else repo_licence)
        source = source_link(sources["upstream"]) if sources and sources.get("upstream") else (
            "—" if sources else "Hand-written")
        rows.append(f"| [{name}](#{name}) | {source} | {licence} |")
        sections += [f"## {name}", "", description(package / "SKILL.md"), ""]
        if sources:
            sections.append(f"- **Source:** {source}, {pin(sources)}")
        sections += [f"- **Licence:** {licence}",
                     f"- **Instructions:** [SKILL.md]({REPO}/skills/{name}/SKILL.md)", ""]
    catalog = "\n".join([
        "# Skill catalog", "",
        "Generated from `skills.json`, each skill's `SKILL.md` and `sources.json` when this site was built.", "",
        "| Skill | Source | Licence |", "| --- | --- | --- |", *rows, "", *sections])

    updated, cron = weekly(root / ".github/workflows/update.yml")
    unknown = sorted(set(updated) - set(names))
    if unknown:
        raise ValueError(f"Update matrix names unregistered skills: {unknown}")
    manual = [n for n in names if n not in updated]
    schedule = "\n".join([
        "# Update schedule", "",
        "Generated from `.github/workflows/update.yml` when this site was built.", "",
        f"**Update references** runs on the schedule `{cron}` (cron, UTC) and on manual dispatch."
        if cron else "**Update references** runs on manual dispatch.", "",
        "## Refreshed automatically", "",
        *[f"- `{n}`" for n in updated], "",
        "## Changed only through reviewed pull requests", "",
        *([f"- `{n}`" for n in manual] or ["- none"]), "",
        "How a refresh becomes a merged change is described in [How updates work](../explanation/updates.md).", ""])
    return {"catalog.md": catalog, "update-schedule.md": schedule}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, text in render(args.root).items():
        (args.out / name).write_text(text)
