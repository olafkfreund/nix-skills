"""NixOS manual system-operations excerpts from a pinned Nixpkgs master snapshot."""

import json
from pathlib import Path
import re
import tempfile

from nixpkgs import SHA, UPSTREAM, convert, excerpt, expand_includes, index_anchors, lines, resolve_revision
from update import ROOT, digest, encoded, evaluate, pinned_tools, run

PACKAGE = ROOT / 'skills/nixos-operations'
GENERATED = {'references/operations.md', 'COPYING', 'sources.json'}
MANUAL = 'nixos/doc/manual/'
OPTION_LINK = re.compile(r'\]\(#(opt-[^)\s]+)\)')


def join_wrapped_links(text):
    """Rejoin link text that the source wraps across exactly two prose lines."""
    items = list(lines(text))
    output, index = [], 0
    while index < len(items):
        _, line, kind = items[index]
        index += 1
        # A joined line is re-checked, so several wrapped links in one paragraph all rejoin;
        # one link still spans at most two lines because the next line must start its closing.
        while (kind == 'prose' and index < len(items) and items[index][2] == 'prose' and
               re.search(r'\[[^\]\n]*$', line.rstrip('\n')) and re.match(r'^[^\[\]\n]*\]\(', items[index][1])):
            joined = line.rstrip('\n').rstrip() + ' ' + items[index][1].lstrip()
            line = re.sub(r'\s+\]\(', '](', joined, count=1)
            index += 1
        output.append(line)
    return ''.join(output)


def check_local_links(document):
    """Fail on any prose link to a local anchor that the output does not define."""
    ids = set(re.findall(r'id="([^"]+)"', document))
    for _, line, kind in lines(document):
        for anchor in re.findall(r'\]\(#([^)\s]+)\)', line) if kind == 'prose' else []:
            if anchor not in ids:
                raise ValueError('Unconverted local link: #' + anchor)


def fetch(manifest, revision):
    if not SHA.fullmatch(revision):
        raise ValueError('Invalid source revision')
    tool = manifest['toolchain']
    if tool['upstream'] != 'https://github.com/NixOS/nix':
        raise ValueError('Unexpected evaluator origin')
    _, nix = pinned_tools(tool['revision'], tool['release'])
    flags = (nix, '--extra-experimental-features', 'nix-command flakes')
    fetched = json.loads(run(*flags, 'flake', 'prefetch', '--json', 'github:NixOS/nixpkgs/' + revision))
    if fetched['locked']['rev'] != revision:
        raise ValueError('Fetched source identity mismatch')
    return Path(fetched['storePath']), nix


def option_declarations(nix, source, names):
    """Declaring files of the named NixOS options at the pinned source."""
    with tempfile.TemporaryDirectory(prefix='nixos-operations-') as directory:
        args = Path(directory) / 'args.json'
        # Option names travel as JSON data so they can never become Nix code.
        args.write_bytes(encoded({'names': sorted(names), 'stateVersion': (source / '.version').read_text().strip()}))
        expr = (f'let a = builtins.fromJSON (builtins.readFile {args}); lib = import {source}/lib; '
                f'nixos = import {source}/nixos/lib/eval-config.nix {{ system = "x86_64-linux"; '
                'modules = [ { system.stateVersion = a.stateVersion; } ]; }; '
                'in map (o: { inherit (o) name; declarations = map toString o.declarations; }) '
                '(builtins.filter (o: builtins.elem o.name a.names) (lib.optionAttrSetToDocList nixos.options))')
        found = json.loads(evaluate(nix, '--extra-experimental-features', 'nix-command', 'eval', '--impure',
                                    '--json', '--expr', expr))
    prefix = str(source) + '/'
    return {item['name']: [d.removeprefix(prefix) for d in item['declarations'] if d.startswith(prefix)]
            for item in found}


def generate(old, revision, source, declarations):
    inputs = {}

    def read(path):
        resolved = (source / path).resolve()
        if not resolved.is_relative_to(source.resolve()) or not resolved.is_file():
            raise ValueError('Missing/escaping source: ' + path)
        data = resolved.read_bytes()
        inputs[path] = digest(data)
        return data.decode()

    selected = old['selection']
    anchors, coverage = {}, {}
    for folder in ['doc', 'nixos/doc/manual']:
        for file in sorted((source / folder).rglob('*.md')):
            path = str(file.relative_to(source))
            coverage[path] = digest(file.read_bytes())
            index_anchors(file.read_text(), path, anchors)
            anchors['path:' + path] = {(path, file.stem)}
    # Reviewed option links resolve to the option's declaring file at this pin.
    for item in selected['sections']:
        for anchor, option in item.get('option_links', {}).items():
            files = declarations.get(option, [])
            if not files:
                raise ValueError('Mapped option has no in-tree declaration: ' + option)
            if anchor in anchors:
                raise ValueError('Option anchor collides with a manual anchor: ' + anchor)
            read(files[0])
            anchors[anchor] = {(files[0], option)}
    excerpts, bundled = [], {}
    for item in selected['sections']:
        full = read(item['path'])
        text = join_wrapped_links(expand_includes(excerpt(full, item), item['path'], read))
        # Only prose links are converted, so fenced examples never need a mapping.
        used = {anchor for _, line, kind in lines(text) if kind == 'prose' for anchor in OPTION_LINK.findall(line)}
        mapped = set(item.get('option_links', {}))
        if used - mapped:
            raise ValueError('Unmapped option link: ' + ', '.join(sorted(used - mapped)))
        if mapped - used:
            raise ValueError('Unused option link mapping: ' + ', '.join(sorted(mapped - used)))
        local = {}
        index_anchors(text, item['path'], local)
        for anchor in local:
            if anchor in bundled:
                raise ValueError('Duplicate packaged anchor: ' + anchor)
            bundled[anchor] = 'operations.md'
        excerpts.append((item, text))
    manpages = json.loads(read('doc/manpage-urls.json'))
    version = read('.version').strip()
    document = ('# Operations\n\n'
                f'NixOS manual from Nixpkgs master snapshot `{revision}`; development series {version}.\n\n'
                'Modified excerpts from the Nixpkgs contributors; see [COPYING](../COPYING). '
                'Source citations are pinned; public manual links may move.\n\n')
    for item, _ in excerpts:
        document += f"- [{item['heading']}](#{item['anchor']})\n"
    for item, text in excerpts:
        document += ('\n\n' + f"[Upstream source]({UPSTREAM}/blob/{revision}/{item['path']})\n\n"
                     + convert(text, item['path'], revision, anchors, bundled, manpages, read(item['path'])))
    check_local_links(document)
    if (source / 'NOTICE').exists():
        raise ValueError('New upstream NOTICE requires reviewed packaging')
    files = {'references/operations.md': (document.rstrip() + '\n').encode(), 'COPYING': read('COPYING').encode()}
    manifest = {'upstream': UPSTREAM, 'branch': 'master', 'revision': revision, 'source_version': version,
                'toolchain': old['toolchain'], 'selection': selected, 'inputs': inputs,
                'coverage_inputs': coverage, 'outputs': {name: digest(data) for name, data in sorted(files.items())}}
    files['sources.json'] = encoded(manifest)
    return files, manifest


def validate_manifest(manifest):
    if manifest['branch'] != 'master' or not re.fullmatch(r'\d+\.\d+', manifest['source_version']):
        raise ValueError('Invalid Nixpkgs branch/development version')
    tool = manifest['toolchain']
    if (tool['upstream'] != 'https://github.com/NixOS/nix' or
            not SHA.fullmatch(tool['revision']) or not re.fullmatch(r'\d+\.\d+\.\d+', tool['release'])):
        raise ValueError('Invalid pinned evaluator')
    sections = manifest['selection']['sections']
    if not sections or set(manifest['selection']) != {'sections'}:
        raise ValueError('Empty/invalid NixOS operations selection')
    if len({item['anchor'] for item in sections}) != len(sections):
        raise ValueError('Duplicate section anchor')
    expected = {'COPYING', '.version', 'doc/manpage-urls.json'}
    for item in sections:
        links = item.get('option_links', {})
        if (not set(item) <= {'path', 'heading', 'anchor', 'children', 'option_links'} or
                not item['path'].startswith(MANUAL) or not item['heading'] or type(item['children']) is not bool or
                not re.fullmatch(r'[\w.:-]+', item['anchor']) or not isinstance(links, dict) or
                any(not re.fullmatch(r'opt-[\w.:<>-]+', k) or not isinstance(v, str) or not v
                    for k, v in links.items())):
            raise ValueError('Invalid section selection')
        expected.add(item['path'])
    if not expected <= manifest['inputs'].keys():
        raise ValueError('Missing consumed input hashes')
    for field in ['inputs', 'coverage_inputs']:
        for name, value in manifest[field].items():
            if Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name:
                raise ValueError('Invalid provenance path')
            if not re.fullmatch(r'[0-9a-f]{64}', value):
                raise ValueError('Invalid provenance hash')


def report(old, new):
    rows = [f"Update NixOS operations references from {old['revision']} to {new['revision']} "
            f"(series {new['source_version']}).", '']
    for field in ['inputs', 'coverage_inputs']:
        before, after = old.get(field, {}), new[field]
        changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
        rows += [field + ' changes:', ''] + ['- `' + name + '`' for name in changed]
        if not changed:
            rows.append('None; this may be a provenance-only refresh.')
        rows.append('')
    return '\n'.join(rows)


def main(args):
    from update import publish
    # Read the recorded manifest directly; publish() validates the complete staged package.
    old = json.loads((PACKAGE / 'sources.json').read_text())
    revision = resolve_revision(old) if args.latest else args.revision or old['revision']
    if args.latest and revision == old['revision']:
        print('Already at recorded Nixpkgs master SHA; no update')
        return
    source, nix = fetch(old, revision)
    names = {option for item in old['selection']['sections'] for option in item.get('option_links', {}).values()}
    files, new = generate(old, revision, source, option_declarations(nix, source, names))
    if args.check:
        changed = [name for name, content in files.items() if (PACKAGE / name).read_bytes() != content]
        if changed:
            raise ValueError('Regeneration differs: ' + repr(changed))
        print('NixOS operations source identity and reproducibility checks passed')
    else:
        publish(files, PACKAGE, skill='nixos-operations')
        (ROOT / '.update-report.md').write_text(report(old, new))
        print('Generated NixOS operations references at ' + revision)
