#!/usr/bin/env python3
"""Refresh selected upstream documentation; no third-party Python dependencies."""

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urldefrag, urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills/nix-language"
UPSTREAM = "https://github.com/NixOS/nix"
GENERATED = {"references/language.md", "references/builtins.md", "COPYING", "sources.json"}
RELEASE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def run(*args, env=None):
    return subprocess.check_output([str(a) for a in args], text=True, env=env).strip()


def evaluate(nix, *args):
    # Match upstream's isolated documentation context without changing the caller's environment.
    env = os.environ | {"NIX_CONF_DIR": "/nonexistent", "NIX_USER_CONF_FILES": "/dev/null", "NIX_CONFIG": ""}
    return run(nix, *args, env=env)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def tags():
    result = {}
    lines = run("git", "ls-remote", "--tags", UPSTREAM + ".git").splitlines()
    for line in lines:
        sha, ref = line.split()
        name = ref.removeprefix("refs/tags/").removesuffix("^{}")
        if RELEASE.fullmatch(name):
            if ref.endswith("^{}") or name not in result:
                result[name] = sha
    if not result:
        raise ValueError("No stable numeric upstream tags found")
    return result


def resolve_release(old, available, requested):
    previous = old.get("release")
    if previous and available.get(previous) != old["revision"]:
        raise ValueError("Pinned release tag disappeared or moved; investigate manually")
    if not RELEASE.fullmatch(requested) or requested not in available:
        raise ValueError("Release must be an existing numeric stable upstream tag")
    return available[requested]


def pinned_tools(revision, release):
    ref = f"github:NixOS/nix/{revision}"
    metadata = json.loads(run("nix", "--extra-experimental-features", "nix-command flakes",
                              "flake", "metadata", "--json", ref))
    if metadata["locked"]["rev"] != revision:
        raise ValueError("Resolved source revision mismatch")
    fetched = json.loads(run("nix", "--extra-experimental-features", "nix-command flakes",
                             "flake", "prefetch", "--json", ref))
    if fetched["storePath"] != metadata["path"]:
        raise ValueError("Prefetched source does not match resolved source")
    source = Path(fetched["storePath"])
    if not re.search(r"officialRelease\s*=\s*true;", (source / "flake.nix").read_text()):
        raise ValueError("Upstream does not mark this source as an official release")
    output = run("nix", "--extra-experimental-features", "nix-command flakes", "build",
                 "--no-link", "--print-out-paths", ref + "#nix^out")
    nix = Path(output) / "bin/nix"
    if run(nix, "--version") != f"nix (Nix) {release}":
        raise ValueError("Executable does not match release version")
    return source, nix


def prose(text, transform):
    """Transform prose only, leaving fenced examples unchanged (including blockquotes)."""
    result, fence = [], None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^[ >\t]*(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            result.append(line)
        else:
            result.append(line if fence else transform(line))
    if fence:
        raise ValueError("Unclosed code fence")
    return "".join(result)


def section(text, heading):
    """Exact heading selection, excluding child sections when heading is the page title."""
    # Search original offsets, but ignore headings inside fenced examples.
    headings = []
    offset = 0
    fence = False
    for line in text.splitlines(keepends=True):
        if re.match(r"^[ >\t]*(`{3,}|~{3,})", line):
            fence = not fence
        match = re.match(r"^(#{1,6}) (.+?)\s*$", line)
        if match and not fence:
            headings.append((offset, len(match[1]), match[2]))
        offset += len(line)
    matches = [i for i, item in enumerate(headings) if item[2] == heading]
    if len(matches) != 1:
        raise ValueError(f"Missing or ambiguous section: {heading}")
    i = matches[0]
    start, level, _ = headings[i]
    end = len(text)
    for following, depth, _ in headings[i + 1:]:
        if depth <= level or level == 1:
            end = following
            break
    return text[start:end].strip() + "\n"


def render(text, full_text, path, manual, extra_definitions=None):
    definitions = dict(extra_definitions or {})
    pattern = re.compile(r"^\s*\[([^\]]+)\]:\s*(\S+)\s*$")

    def collect(line):
        match = pattern.match(line)
        if match:
            key = match[1].casefold()
            if key in definitions and definitions[key] != match[2]:
                raise ValueError(f"Ambiguous reference definition: {key}")
            definitions[key] = match[2]
        return line

    prose(full_text, collect)
    base = manual + path.removesuffix(".md") + ".html"

    def target(link):
        if urlsplit(link).scheme:
            return link
        if link.startswith("//"):
            raise ValueError("Ambiguous protocol-relative documentation link")
        link = link.replace("@docroot@/", manual)
        link = re.sub(r"\.md(?=#|$)", ".html", link)
        resolved = urljoin(base, link)
        if not resolved.startswith(manual):
            raise ValueError(f"Documentation link escapes manual: {link}")
        return resolved

    def convert(line):
        if pattern.match(line):
            return ""
        protected = []

        def protect(match):
            if "[" not in match[0] and "]" not in match[0]:
                return match[0]
            protected.append(match[0])
            return f"\x00{len(protected) - 1}\x00"

        line = re.sub(r"(`+).*?\1", protect, line)
        # Support the upstream inline, full-reference, and shortcut link forms.
        line = re.sub(r"(?<!\\)\[([^\]\n]+)\]\[([^\]\n]*)\]",
                      lambda m: f"[{m[1]}]({definitions[(m[2] or m[1]).casefold()]})", line)
        line = re.sub(r"(?<!\\)\[([^\]\n]+)\](?![\[(])",
                      lambda m: f"[{m[1]}]({definitions[m[1].casefold()]})"
                      if m[1].casefold() in definitions else m[0], line)
        line = re.sub(r"\]\(([^\s)]+)\)", lambda m: "](" + target(m[1]) + ")", line)
        line = re.sub(r'href="([^"]+)"', lambda m: 'href="' + target(m[1]) + '"', line)
        # mdBook custom anchors are not portable Markdown.
        line = re.sub(r"\{#([\w-]+)\}", lambda m: f'<a id="{m[1]}"></a>', line)
        for i, original in enumerate(protected):
            line = line.replace(f"\x00{i}\x00", original)
        if not line.endswith("  \n"):
            line = re.sub(r"[ \t]+\n$", "\n", line)
        return line

    result = prose(text, convert)
    if re.search(r"@docroot@|@generated@|\{\{#|@_at_", result):
        raise ValueError(f"Unsupported/unresolved upstream directive in {path}")
    return result


def check_external(contents, manual):
    urls = set()
    for text in contents:
        urls.update(re.findall(re.escape(manual) + r'[^\s)<>"\]]+', text))
    pages = {}
    for url in sorted(urls):
        page, anchor = urldefrag(url)
        if page not in pages:
            with urlopen(Request(page, headers={"User-Agent": "nix-skills-reference-check"}), timeout=30) as response:
                if not response.url.startswith(manual):
                    raise ValueError(f"Manual redirected outside pinned version: {page}")
                pages[page] = html.unescape(response.read().decode())
        if anchor and not re.search(r'(?:id|name)=["\']' + re.escape(anchor) + r'["\']', pages[page]):
            raise ValueError(f"Missing published manual anchor: {url}")


def generate(old, release, revision, source, nix):
    manual = "https://nix.dev/manual/nix/" + ".".join(release.split(".")[:2]) + "/"
    inputs = {}

    def read(path):
        data = (source / path).read_bytes()
        inputs[path] = digest(data)
        return data.decode()

    header = (f"Nix {release}; upstream revision `{revision}`.\n\n"
              "Selected upstream excerpts, with links adapted for this package. "
              "Copyright the Nix contributors; see [COPYING](../COPYING).\n\n")
    language = "# Language reference\n\n" + header
    for i, selection in enumerate(old["selection"]["sections"], 1):
        title = re.sub(r"\s*\{#[^}]+\}", "", selection["heading"])
        language += f"- [{title}](#section-{i})\n"
    language += "\n"
    for i, selection in enumerate(old["selection"]["sections"], 1):
        path, heading = selection["path"], selection["heading"]
        full = read("doc/manual/source/" + path)
        excerpt = section(full, heading)
        language += (f'<a id="section-{i}"></a>\n\n'
                     + f"[Upstream source]({UPSTREAM}/blob/{revision}/doc/manual/source/{path})\n\n"
                     + render(excerpt, full, path, manual, selection.get("link_definitions")) + "\n")

    language_info = json.loads(evaluate(nix, "__dump-language"))
    selected = {name: language_info[name] for name in old["selection"]["builtins"]}
    inputs["generated:language.json"] = digest(encoded(language_info))
    for path in ["doc/manual/generate-builtins.nix", "doc/manual/utils.nix", "flake.nix", "flake.lock", ".version"]:
        read(path)
    with tempfile.TemporaryDirectory() as directory:
        info = Path(directory) / "builtins.json"
        info.write_bytes(encoded(selected))
        expr = (f"import {source}/doc/manual/generate-builtins.nix "
                f"(builtins.fromJSON (builtins.readFile {info}))")
        builtins = evaluate(nix, "--extra-experimental-features", "nix-command", "eval", "--raw",
                       "--impure", "--store", "dummy://", "-I", f"nix={source}/doc/manual", "--expr", expr)
    contents = "\n".join(f"- [{name}](#builtins-{name})" for name in sorted(selected)) + "\n\n"
    builtins = ("# Built-in reference\n\n" + header + contents
                + f"[Upstream generator]({UPSTREAM}/blob/{revision}/doc/manual/generate-builtins.nix)\n\n"
                + "<dl>\n" + render(builtins, builtins, "language/builtins.md", manual) + "\n</dl>\n")
    copying = read("COPYING")
    # Hash all language inputs so update reports also identify material outside the curated subset.
    language_hashes = {str(p.relative_to(source)): digest(p.read_bytes())
                       for p in sorted((source / "doc/manual/source/language").rglob("*.md"))}
    files = {"references/language.md": (language.rstrip() + "\n").encode(), "references/builtins.md": builtins.encode(),
             "COPYING": copying.encode()}
    manifest = {"upstream": UPSTREAM, "release": release, "revision": revision, "nix_version": release,
                "selection": old["selection"], "inputs": inputs, "language_inputs": language_hashes,
                "outputs": {path: digest(data) for path, data in sorted(files.items())}}
    files["sources.json"] = encoded(manifest)
    check_external([language, builtins], manual)
    result = evaluate(nix, "--extra-experimental-features", "nix-command", "eval", "--json",
                 "--file", ROOT / "tests/language.nix")
    if result != "true":
        raise ValueError("Semantic assertions did not return true")
    return files, manifest


def publish(files, package=PACKAGE, skill="nix-language"):
    """Validate a complete staging copy, then restore old bytes if replacement fails."""
    generated = generated_files(skill)
    from check import validate
    if set(files) != generated:
        raise ValueError("Unexpected generated file set")
    with tempfile.TemporaryDirectory(dir=package.parent) as directory:
        staged = Path(directory) / "skill"
        shutil.copytree(package, staged)
        for name, data in files.items():
            target = staged / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        validate(staged, skill=skill)
        original = {name: (package / name).read_bytes() if (package / name).exists() else None for name in files}
        try:
            for name in sorted(files):
                (package / name).parent.mkdir(parents=True, exist_ok=True)
                os.replace(staged / name, package / name)
        except BaseException:
            for name, data in original.items():
                if data is None:
                    (package / name).unlink(missing_ok=True)
                else:
                    (package / name).write_bytes(data)
            raise


def report(old, new):
    before, after = old.get("language_inputs", {}), new["language_inputs"]
    changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
    selected = {"doc/manual/source/" + s["path"] for s in new["selection"]["sections"]}
    rows = [f"Update Nix references from {old.get('release', 'initial')} ({old.get('revision', 'none')}) "
            f"to {new['release']} ({new['revision']}).", "", "Changed language sources:", ""]
    rows += [f"- `{p}` ({'selected' if p in selected else 'outside selection — review coverage'})" for p in changed]
    if not changed:
        rows.append("No language source files changed; provenance still advances to the new release.")
    rows += ["", "Built-in metadata changed: " + str(old.get("inputs", {}).get("generated:language.json") !=
                                                     new["inputs"]["generated:language.json"]), ""]
    return "\n".join(rows)


def generated_files(skill):
    if skill == "nix-language":
        return GENERATED
    if skill == "devenv-project":
        from devenv import GENERATED as devenv_files
        return devenv_files
    if skill == "nixpkgs-development":
        from nixpkgs import GENERATED as nixpkgs_files
        return nixpkgs_files
    raise ValueError("Unknown skill")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", choices=["nix-language", "devenv-project", "nixpkgs-development"], default="nix-language")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--release")
    mode.add_argument("--revision")
    mode.add_argument("--latest", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.skill == "nixpkgs-development":
        if args.release:
            parser.error("Nixpkgs uses --revision, not --release")
        from nixpkgs import main as nixpkgs_main
        return nixpkgs_main(args)
    if args.revision:
        parser.error("--revision is only supported for nixpkgs-development")
    if args.skill == "devenv-project":
        from devenv import main as devenv_main
        return devenv_main(args)
    old = json.loads((PACKAGE / "sources.json").read_text())
    available = tags()
    release = (max(available, key=lambda value: tuple(map(int, value.split(".")))) if args.latest
               else args.release or old["release"])
    revision = resolve_release(old, available, release)
    if args.latest and revision == old.get("revision"):
        print("Already at newest stable tag; no update")
        return
    source, nix = pinned_tools(revision, release)
    files, new = generate(old, release, revision, source, nix)
    if args.check:
        changed = [name for name, data in files.items() if (PACKAGE / name).read_bytes() != data]
        if changed:
            raise ValueError(f"Regeneration differs: {changed}")
        print("Reproducibility, external links, and semantic assertions passed")
    else:
        publish(files)
        (ROOT / ".update-report.md").write_text(report(old, new))
        print(f"Generated Nix {release} references at {revision}")


if __name__ == "__main__":
    main()
