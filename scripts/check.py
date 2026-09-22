#!/usr/bin/env python3
"""Offline validation of the portable skill and automated-update boundaries."""

import argparse
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from update import PACKAGE, UPSTREAM, ROOT, digest, generated_files, prose, run


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


def validate(package=PACKAGE, skill="nix-language"):
    generated = generated_files(skill)
    upstream = {"nix-language": UPSTREAM, "devenv-project": "https://github.com/cachix/devenv",
                "nixpkgs-development": "https://github.com/NixOS/nixpkgs"}[skill]
    package = package.resolve()
    manifest = json.loads((package / "sources.json").read_text())
    if manifest["upstream"] != upstream or not re.fullmatch(r"[0-9a-f]{40}", manifest["revision"]):
        raise ValueError("Invalid upstream provenance")
    if skill == "nix-language":
        if not re.fullmatch(r"\d+\.\d+\.\d+", manifest["release"]) or manifest["nix_version"] != manifest["release"]:
            raise ValueError("Invalid release/version")
        if not manifest["selection"]["sections"] or not manifest["selection"]["builtins"]:
            raise ValueError("Empty reference selection")
        coverage = manifest["language_inputs"]
    elif skill == "nixpkgs-development":
        from nixpkgs import validate_manifest
        validate_manifest(manifest)
        coverage = manifest["coverage_inputs"]
    else:
        from devenv import version
        if manifest["devenv_version"] != version(manifest["release"]):
            raise ValueError("Invalid release/version")
        if not manifest["selection"]["sections"] or not manifest["selection"]["options"]:
            raise ValueError("Empty reference selection")
        coverage = manifest["documentation_inputs"]
        option_hashes = manifest["option_inputs"]
        if set(option_hashes) != set(manifest["selection"]["options"]) or any(
                not re.fullmatch(r"[0-9a-f]{64}", h) for h in option_hashes.values()):
            raise ValueError("Invalid selected option hashes")
        expected_inputs = {"docs/src/content/docs/" + s["path"] for s in manifest["selection"]["sections"]}
        expected_inputs.update(manifest["selection"]["provenance"])
        expected_inputs.update({"LICENSE", "docs/src/data/options.json",
                                "docs/public/.well-known/agent-skills/devenv-setup/SKILL.md"})
        if set(manifest["inputs"]) != expected_inputs:
            raise ValueError("Missing/unexpected selected source hashes")
    for hashes in [manifest["inputs"], manifest["outputs"], coverage]:
        if not hashes or any(not re.fullmatch(r"[0-9a-f]{64}", h) for h in hashes.values()):
            raise ValueError("Missing/invalid source hashes")
    if set(manifest["outputs"]) != generated - {"sources.json"}:
        raise ValueError("Unexpected generated outputs")
    actual = {str(p.relative_to(package)) for p in package.rglob("*") if p.is_file()}
    if actual != generated | {"SKILL.md"} or any(p.is_symlink() for p in package.rglob("*")):
        raise ValueError("Unexpected package files or symlinks")
    for name, expected in manifest["outputs"].items():
        if digest((package / name).read_bytes()) != expected:
            raise ValueError(f"Content hash mismatch: {name}")
    skill_text = (package / "SKILL.md").read_text()
    if not skill_text.startswith("---\n") or "\n---\n" not in skill_text[4:]:
        raise ValueError("Missing skill frontmatter")
    frontmatter = skill_text.split("---", 2)[1]
    if not re.search(rf"^name: {re.escape(skill)}$", frontmatter, re.M) or not re.search(r"^description: .+", frontmatter, re.M):
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


def immutable_policy(old, new, skill):
    fields = ["selection", "upstream"]
    if skill == "nixpkgs-development":
        fields += ["branch", "toolchain"]
    if any(old[field] != new[field] for field in fields):
        raise ValueError("Automatic update changed immutable skill policy")


def boundary(base, package=PACKAGE, skill="nix-language"):
    """Compare both git files and curated JSON fields against a trusted base commit."""
    prefix = f"skills/{skill}/"
    changes = run("git", "diff", "--name-only", base, "--").splitlines()
    if set(changes) - {prefix + name for name in generated_files(skill)}:
        raise ValueError("Automatic update changed non-generated files")
    old = json.loads(run("git", "show", base + ":" + prefix + "sources.json"))
    new = validate(package) if skill == "nix-language" else validate(package, skill=skill)
    immutable_policy(old, new, skill)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Trusted base commit for automated-update boundary checks")
    parser.add_argument("--skill", choices=["nix-language", "devenv-project", "nixpkgs-development"], default="nix-language")
    args = parser.parse_args()
    package = ROOT / "skills" / args.skill
    validate(package, skill=args.skill)
    if args.base:
        boundary(args.base, package, skill=args.skill)
    print("Skill metadata, links, provenance, hashes, and file boundaries passed")
