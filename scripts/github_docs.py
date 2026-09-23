"""Pinned GitHub Markdown snapshots used by source-maintained skills."""

import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urljoin, urlsplit

from update import ROOT, digest, encoded, publish, prose, run

SHA = re.compile(r"[0-9a-f]{40}")
FENCE = re.compile(r"^[ >\t]*(`{3,}|~{3,})")


def resolve_revision(old, upstream, branch, requested=None):
    if old.get("upstream") != upstream or old.get("branch") != branch:
        raise ValueError("Unexpected upstream or branch")
    previous = old.get("revision")
    if not SHA.fullmatch(previous or ""):
        raise ValueError("Invalid pinned revision")
    if requested:
        if not SHA.fullmatch(requested):
            raise ValueError("Revision must be a full commit SHA")
        return requested
    rows = run("git", "ls-remote", upstream + ".git", "refs/heads/" + branch).splitlines()
    if len(rows) != 1:
        raise ValueError("Cannot resolve branch unambiguously")
    revision, ref = rows[0].split()
    if ref != "refs/heads/" + branch or not SHA.fullmatch(revision):
        raise ValueError("Invalid branch revision")
    return revision


def pinned_source(upstream, revision):
    owner_repo = upstream.removeprefix("https://github.com/")
    ref = "github:" + owner_repo + "/" + revision
    flags = ("nix", "--extra-experimental-features", "nix-command flakes")
    metadata = json.loads(run(*flags, "flake", "metadata", "--json", ref))
    fetched = json.loads(run(*flags, "flake", "prefetch", "--json", ref))
    if metadata["locked"]["rev"] != revision or metadata["path"] != fetched["storePath"]:
        raise ValueError("Resolved source revision mismatch")
    return Path(fetched["storePath"])


def source_path(source, relative):
    path = (source / relative).resolve()
    if not path.is_relative_to(source.resolve()) or not path.is_file():
        raise ValueError("Missing or escaping source path: " + relative)
    return path


def source_url(upstream, revision, relative):
    return upstream + "/blob/" + revision + "/" + relative


def pin_links(text, source_path_name, upstream, revision):
    base = source_url(upstream, revision, source_path_name)

    def convert(line):
        def link(match):
            target = match[1]
            if target.startswith("#"):
                return "](" + base + target + ")"
            if target.startswith("<") or urlsplit(target).scheme:
                return match[0]
            if target.startswith("//"):
                raise ValueError("Protocol-relative link: " + target)
            resolved = urljoin(base, target)
            prefix = upstream + "/blob/" + revision + "/"
            if not resolved.startswith(prefix):
                raise ValueError("Source link escapes checkout: " + target)
            return "](" + resolved + ")"

        line = re.sub(r"\]\(([^\s)]+)\)", link, line)

        def definition(match):
            target = match[2]
            if target.startswith(("<", "#")) or urlsplit(target).scheme:
                return match[0]
            resolved = urljoin(base, target)
            prefix = upstream + "/blob/" + revision + "/"
            if not resolved.startswith(prefix):
                raise ValueError("Reference link escapes checkout: " + target)
            return match[1] + resolved

        return re.sub(r"^(\s*\[[^\]]+\]:\s+)(\S+)", definition, line)

    return prose(text, convert)


def generate(old, config, revision, source):
    inputs = {}

    def read(relative):
        path = source_path(source, relative)
        data = path.read_bytes()
        inputs[relative] = digest(data)
        return data.decode()

    files = {}
    for item in old["selection"]:
        content = read(item["source"])
        header = (
            f"Upstream source: [{item['source']}]({source_url(old['upstream'], revision, item['source'])})\n\n"
            "Modified excerpt from the upstream project; see [LICENSE](../LICENSE).\n\n"
        )
        files[item["output"]] = (header + pin_links(content, item["source"], old["upstream"], revision)).encode()

    license_data = read("LICENSE")
    files["LICENSE"] = license_data.encode()
    manifest = {
        "upstream": old["upstream"],
        "branch": old["branch"],
        "revision": revision,
        "selection": old["selection"],
        "inputs": inputs,
        "outputs": {name: digest(data) for name, data in sorted(files.items())},
    }
    files["sources.json"] = encoded(manifest)
    return files, manifest


def validate_manifest(package, config):
    manifest = json.loads((package / "sources.json").read_text())
    if (manifest.get("upstream") != config["upstream"] or
            manifest.get("branch") != config["branch"] or
            not SHA.fullmatch(manifest.get("revision", ""))):
        raise ValueError("Invalid upstream provenance")
    selection = manifest.get("selection")
    if not selection or any(set(item) != {"source", "output", "title"} for item in selection):
        raise ValueError("Invalid source selection")
    if selection != config["selection"]:
        raise ValueError("Source selection differs from reviewed provider policy")
    expected_inputs = {item["source"] for item in selection} | {"LICENSE"}
    if set(manifest.get("inputs", {})) != expected_inputs:
        raise ValueError("Missing or unexpected selected source hashes")
    expected = {item["output"] for item in selection} | {"LICENSE"}
    if set(manifest.get("outputs", {})) != expected:
        raise ValueError("Unexpected generated outputs")
    for hashes in (manifest.get("inputs", {}), manifest.get("outputs", {})):
        if not hashes or any(not re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes.values()):
            raise ValueError("Missing or invalid source hashes")
    return manifest


def generated_files(config):
    return {item["output"] for item in config["selection"]} | {"LICENSE", "sources.json"}


def immutable_policy(old, new):
    for field in ("upstream", "branch", "selection"):
        if old[field] != new[field]:
            raise ValueError("Automatic update changed immutable " + field)


def report(old, new):
    before, after = old.get("inputs", {}), new["inputs"]
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    rows = [
        f"Update {new['upstream']} {old.get('revision', 'none')} → {new['revision']}.",
        "",
        "Changed selected inputs:",
        "",
    ]
    rows.extend("- `" + path + "`" for path in changed) if changed else rows.append("None.")
    return "\n".join(rows) + "\n"


def main(args, config):
    package = ROOT / "skills" / config["skill"]
    old = json.loads((package / "sources.json").read_text())
    # --check reproduces the recorded revision; only --latest follows the live branch.
    requested = args.revision or (old["revision"] if args.check else None)
    revision = resolve_revision(old, config["upstream"], config["branch"], requested)
    if args.latest and revision == old["revision"]:
        print("Already at newest upstream revision; no update")
        return
    source = pinned_source(config["upstream"], revision)
    files, new = generate(old, config, revision, source)
    if args.check:
        changed = [name for name, data in files.items() if (package / name).read_bytes() != data]
        if changed:
            raise ValueError("Regeneration differs: " + repr(changed))
        print("Pinned source regeneration and package checks passed")
    else:
        publish(files, package, skill=config["skill"])
        (ROOT / ".update-report.md").write_text(report(old, new))
        print("Generated " + config["skill"] + " references at " + revision)
