#!/usr/bin/env python3
"""Generate the site's skill catalog and update schedule from repository data, offline.

Reads skills.json, each skill's SKILL.md frontmatter description and sources.json,
and the `skill: [...]` matrix line and cron of .github/workflows/update.yml.
sources.json fields used: `upstream`, `release` or `branch`, and `revision`
(or `snapshot_sha256` for the wiki dump). Absent fields render as "—".
"""

import argparse
import json
from pathlib import Path
import re

REPO = "https://github.com/olafkfreund/nix-skills/blob/main"


def description(skill_md):
    match = re.search(r"^description: (.+)$", skill_md.read_text(), re.M)
    return match[1].strip() if match else "—"


def pinned(sources):
    label = sources.get("release") or sources.get("branch")
    digest = sources.get("revision") or sources.get("snapshot_sha256")
    parts = [label, f"`{digest[:12]}`" if digest else None]
    return " ".join(p for p in parts if p) or "—"


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
    rows = []
    for name in names:
        package = root / "skills" / name
        sources_file = package / "sources.json"
        sources = json.loads(sources_file.read_text()) if sources_file.is_file() else None
        licence = next((f for f in ("LICENSE", "COPYING") if (package / f).is_file()), None)
        rows.append("| [{0}]({1}/skills/{0}/SKILL.md) | {2} | {3} | {4} | {5} | {6} |".format(
            name, REPO, description(package / "SKILL.md").replace("|", "\\|"),
            "generated from upstream" if sources else "hand-written",
            sources.get("upstream", "—") if sources else "—",
            pinned(sources) if sources else "—",
            f"[{licence}]({REPO}/skills/{name}/{licence})" if licence else "repository licence"))
    catalog = "\n".join([
        "# Skill catalog", "",
        "Generated from `skills.json` and each skill's `sources.json` when this site was built.", "",
        "| Skill | Description | Kind | Upstream | Pinned | Licence |",
        "| --- | --- | --- | --- | --- | --- |", *rows, ""])

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
