"""Curated Nixpkgs master snapshots and upstream-generated library documentation."""

import json
import posixpath
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote, urlsplit

from update import ROOT, digest, encoded, evaluate, github_json, pinned_tools, run

UPSTREAM = 'https://github.com/NixOS/nixpkgs'
PACKAGE = ROOT / 'skills/nixpkgs-development'
GENERATED = {'references/' + name + '.md' for name in ['packaging', 'customization', 'helpers', 'library']} | {'COPYING', 'sources.json'}
SHA = re.compile(r'[0-9a-f]{40}')
FENCE = re.compile(r'^\s*(`{3,}|~{3,})(.*)$')
DIV = re.compile(r'^\s*(:{3,})\s*\{\.(note|tip|warning|caution|important|example)(?:\s+#([^} ]+))?\}\s*$')
ANCHOR = re.compile(r'\{#([\w.:-]+)\}')


def resolve_revision(old, requested=None):
    if old['upstream'] != UPSTREAM or old['branch'] != 'master':
        raise ValueError('Unexpected Nixpkgs update origin/branch')
    if requested:
        if not SHA.fullmatch(requested):
            raise ValueError('Nixpkgs revision must be a full commit SHA')
        return requested
    rows = run('git', 'ls-remote', UPSTREAM + '.git', 'refs/heads/master').splitlines()
    if len(rows) != 1 or rows[0].split()[1] != 'refs/heads/master':
        raise ValueError('Cannot resolve master unambiguously')
    revision = rows[0].split()[0]
    if not SHA.fullmatch(revision):
        raise ValueError('Invalid upstream SHA')
    if revision != old['revision']:
        url = 'https://api.github.com/repos/NixOS/nixpkgs/compare/' + old['revision'] + '...' + revision
        comparison = github_json(url)
        if (comparison.get('status') != 'ahead' or comparison.get('behind_by') != 0 or
                comparison.get('merge_base_commit', {}).get('sha') != old['revision']):
            raise ValueError('Master did not advance from the recorded revision')
    return revision


def pinned_inputs(manifest, revision):
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
    source = Path(fetched['storePath'])
    system = evaluate(nix, '--extra-experimental-features', 'nix-command', 'eval', '--impure', '--raw',
                      '--expr', 'builtins.currentSystem')
    if not re.fullmatch(r'[a-z0-9_]+-[a-z0-9]+', system):
        raise ValueError('Unexpected Nix system')
    expression = f'(import {source} {{ system = "{system}"; config = {{}}; overlays = []; }}).nixpkgs-manual.lib-docs'
    output = run(*flags, 'build', '--impure', '--no-link', '--print-out-paths', '--expr', expression)
    return source, nix, system, (Path(output) / 'lib-functions.json').read_bytes()


def lines(text):
    """Identify fenced code without interpreting Nix interpolation or example headings."""
    fence = None
    offset = 0
    for line in text.splitlines(keepends=True):
        marker = FENCE.match(line.rstrip('\n'))
        if fence is not None:
            kind = 'code'
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
        elif marker:
            fence = marker[1]
            kind = 'code'
        else:
            kind = 'prose'
        yield offset, line, kind
        offset += len(line)
    if fence:
        raise ValueError('Unclosed code fence')


def headings(text):
    result, divs = [], []
    for offset, line, kind in lines(text):
        if kind != 'prose':
            continue
        start = DIV.match(line)
        if start:
            divs.append(start[1])
        elif re.fullmatch(r'\s*:{3,}\s*', line):
            if not divs:
                raise ValueError('Unmatched admonition')
            divs.pop()
        match = re.match(r'^(#{1,6}) (.*?)(?: \{#([^}]+)\})?\s*$', line)
        if match and not divs:
            result.append((offset, len(match[1]), match[2], match[3]))
    if divs:
        raise ValueError('Unclosed admonition')
    return result


def excerpt(text, selection):
    items = headings(text)
    matches = [i for i, h in enumerate(items) if h[3] == selection['anchor'] and h[2] == selection['heading']]
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous section: ' + selection['anchor'])
    i = matches[0]
    start, level, _, _ = items[i]
    end = len(text)
    for following, depth, _, _ in items[i + 1:]:
        if depth <= level or not selection['children']:
            end = following
            break
    # Ancestor introductions can constrain a child even when omitted from the excerpt.
    ancestors = []
    for j, item in enumerate(items[:i]):
        while ancestors and items[ancestors[-1]][1] >= item[1]:
            ancestors.pop()
        ancestors.append(j)
    notices = []
    for j in ancestors:
        if items[j][1] >= level:
            continue
        intro = text[items[j][0]:items[j + 1][0]]
        captured, stack = [], []
        for _, line, kind in lines(intro):
            opening = DIV.match(line) if kind == 'prose' else None
            if opening:
                stack.append(opening[2])
            if stack:
                captured.append(line)
            if kind == 'prose' and re.fullmatch(r'\s*:{3,}\s*', line) and stack:
                tag = stack.pop()
                if not stack:
                    if tag != 'example':
                        notices.append(''.join(captured))
                    captured = []
    return '\n'.join(notices) + '\n' + text[start:end].strip() + '\n'


def expand_includes(text, path, read, active=()):
    if path in active:
        raise ValueError('Cyclic documentation include')
    output, index = [], 0
    source_lines = text.splitlines(keepends=True)
    while index < len(source_lines):
        line = source_lines[index]
        marker = FENCE.match(line.rstrip('\n'))
        if marker:
            end = index + 1
            while end < len(source_lines):
                close = FENCE.match(source_lines[end].rstrip('\n'))
                if close and close[1][0] == marker[1][0] and len(close[1]) >= len(marker[1]) and not close[2].strip():
                    break
                end += 1
            if end == len(source_lines):
                raise ValueError('Unclosed fence')
            if marker[2].startswith('{=include=}'):
                if marker[2].strip() != '{=include=} sections':
                    raise ValueError('Unsupported documentation include mode')
                for name in ''.join(source_lines[index + 1:end]).splitlines():
                    if not name.strip() or Path(name).is_absolute() or '..' in Path(name).parts:
                        raise ValueError('Invalid include path')
                    child = str(Path(path).parent / name.strip())
                    output.append(expand_includes(read(child), child, read, active + (path,)))
            else:
                output.extend(source_lines[index:end + 1])
            index = end + 1
        else:
            output.append(line)
            index += 1
    return ''.join(output)


def parse_library(data, source):
    document = json.loads(data)
    if not isinstance(document, dict) or document.get('schemaVersion') != 1:
        raise ValueError('Unsupported nixdoc schema')
    entries = {}
    for item in document['entries']:
        name = item['id']
        location = item['source']
        path = source / location['file']
        if (name in entries or not isinstance(item['attrPath'], str) or not isinstance(item['description'], str) or
                not path.resolve().is_relative_to(source.resolve()) or not path.is_file() or
                not isinstance(location['line'], int) or not 1 <= location['line'] <= len(path.read_text().splitlines())):
            raise ValueError('Invalid or ambiguous nixdoc record: ' + name)
        entries[name] = item
    if not entries or not isinstance(document['groups'], list):
        raise ValueError('Empty/invalid nixdoc export')
    return document, entries


def index_anchors(text, path, anchors):
    title = Path(path).name
    pending = None
    for _, line, kind in lines(text):
        if kind != 'prose':
            continue
        heading = re.match(r'^\s*#{1,6} (.+?)(?:\s+\{#.*)?\s*$', line)
        if heading:
            title = heading[1]
            if pending:
                anchors.setdefault(pending, set()).add((path, title))
                pending = None
        elif pending and line.strip():
            anchors.setdefault(pending, set()).add((path, title))
            pending = None
        for anchor in ANCHOR.findall(line):
            anchors.setdefault(anchor, set()).add((path, title))
        block = DIV.match(line)
        if block and block[3]:
            pending = block[3]
    if pending:
        anchors.setdefault(pending, set()).add((path, title))


def convert(text, path, revision, anchors, bundled, manpages, full_text=None):
    """Translate the selected NRD forms, never altering executable fenced content."""
    output, stack = [], []
    definitions = {}
    for _, line, kind in lines(full_text if full_text is not None else text):
        match = re.match(r'^\s*\[([^]]+)\]:\s*(\S+)\s*$', line) if kind == 'prose' else None
        if match:
            if match[1] in definitions:
                raise ValueError('Duplicate link definition')
            definitions[match[1]] = match[2]
    def destination(target, label):
        parsed = urlsplit(target)
        if parsed.scheme:
            if parsed.scheme not in {'http', 'https'}:
                raise ValueError('Unsupported URL scheme')
            return f'[{label or target}]({target})'
        if parsed.netloc:
            raise ValueError('Protocol-relative link')
        if parsed.fragment:
            choices = anchors.get(unquote(parsed.fragment), set())
            if parsed.path:
                desired = posixpath.normpath(str(Path(path).parent / unquote(parsed.path)))
                choices = {item for item in choices if item[0] == desired}
            if len(choices) != 1:
                raise ValueError('Missing/ambiguous anchor: ' + target)
            source_path, title = next(iter(choices))
            label = label or title
            if parsed.fragment in bundled:
                return f'[{label}]({bundled[parsed.fragment]}#{parsed.fragment})'
            return f'[{label}]({UPSTREAM}/blob/{revision}/{source_path}) (source section: {title})'
        # Relative source paths are resolved only against recorded existing source files.
        desired = posixpath.normpath(str(Path(path).parent / unquote(parsed.path)))
        key = 'path:' + desired
        if key not in anchors:
            raise ValueError('Unresolved relative source link: ' + target)
        return f'[{label or desired}]({UPSTREAM}/blob/{revision}/{desired})'
    for _, line, kind in lines(text):
        if kind == 'code':
            if re.match(r'^\s*`{3,}\{=', line):
                raise ValueError('Unresolved generated fence')
            output.append(line)
            continue
        opening = DIV.match(line)
        if opening:
            stack.append(opening[2])
            if opening[3]:
                output.append(f'<a id="{opening[3]}"></a>\n\n')
            output.append('**' + opening[2].title() + '**\n\n')
            continue
        if re.fullmatch(r'\s*:{3,}\s*', line):
            if not stack:
                raise ValueError('Unmatched admonition')
            output.append('\n**End ' + stack.pop() + '.**\n\n')
            continue
        if re.match(r'^\s*:::', line):
            raise ValueError('Unknown admonition')
        line = re.sub(r'<!--.*?-->', '', line)
        def role(match):
            name, value = match[1], match[2]
            if name == 'manpage':
                if value not in manpages:
                    raise ValueError('Missing manpage mapping: ' + value)
                return f'[`{value}`]({manpages[value]})'
            if name not in {'command', 'env', 'file', 'option', 'var'}:
                raise ValueError('Unsupported literal role: ' + name)
            return '`' + value + '`'
        line = re.sub(r'\{([\w-]+)\}`([^`]+)`', role, line)
        protected = []
        def protect(match):
            protected.append(match[0])
            return f'\x00{len(protected)-1}\x00'
        line = re.sub(r'(`+).*?\1', protect, line)
        if re.match(r'^\s*\[[^]]+\]:', line):
            continue
        line = re.sub(r'\[([^]\n]*)\]\[([^]\n]+)\]',
                      lambda m: destination(definitions[m[2]], m[1]), line)
        line = re.sub(r'\[([^]\n]*)\]\(([^\s)]+)\)', lambda m: destination(m[2], m[1]), line)
        line = re.sub(r'\[\]\{#([\w.:-]+)\}', r'<a id="\1"></a>', line)
        line = re.sub(r'[ \t]*\{#([\w.:-]+)\}[ \t]*', lambda m: f'\n\n<a id="{m[1]}"></a>', line)
        line = re.sub(r'(</a>)[ \t]+$', r'\1', line)
        # Portable definition lists: retain the term, mark the following definition.
        line = re.sub(r'^(\s*):\s+', r'\1Definition: ', line)
        if re.search(r'\{[.#=]|\{[\w-]+\}`|@[-\w]+@|<!--|\]\[', line):
            raise ValueError('Unresolved documentation syntax: ' + line.strip())
        for i, value in enumerate(protected):
            line = line.replace(f'\x00{i}\x00', value)
        output.append(line)
    if stack:
        raise ValueError('Unclosed admonition')
    return ''.join(output)


def generate(old, revision, source, library):
    inputs = {}
    def read(path):
        resolved = (source / path).resolve()
        if not resolved.is_relative_to(source.resolve()) or not resolved.is_file():
            raise ValueError('Missing/escaping source: ' + path)
        data = resolved.read_bytes()
        inputs[path] = digest(data)
        return data.decode()
    document, entries = parse_library(library, source)
    selected = old['selection']
    if len(set(selected['apis'])) != len(selected['apis']):
        raise ValueError('Duplicate API selection')
    for name in selected['apis']:
        if name not in entries or entries[name]['attrPath'] != name:
            raise ValueError('Missing selected API: ' + name)
    anchors = {}
    coverage = {}
    for folder, pattern in [('doc', '*.md'), ('lib', '*.nix')]:
        for file in sorted((source / folder).rglob(pattern)):
            path = str(file.relative_to(source))
            coverage[path] = digest(file.read_bytes())
            if folder == 'doc':
                index_anchors(file.read_text(), path, anchors)
                anchors['path:' + path] = {(path, file.stem)}
    for record in document['entries']:
        anchor = 'function-library-' + record['id']
        anchors[anchor] = {(record['source']['file'], record['attrPath'])}
    catalogue = json.loads(read('doc/function-catalog.json'))
    for group in document['groups']:
        paths = [s['file'] for s in catalogue['sources'] if group['id'] in s['groups']]
        path = paths[0] if paths else 'doc/function-catalog.json'
        anchors['sec-functions-library-' + group['id']] = {(path, 'lib.' + group['id'])}
        index_anchors(group.get('description', ''), path, anchors)
    excerpts = []
    bundled = {}
    for item in selected['sections']:
        full = read(item['path'])
        text = expand_includes(excerpt(full, item), item['path'], read)
        local = {}
        index_anchors(text, item['path'], local)
        for anchor in local:
            if anchor in bundled:
                raise ValueError('Duplicate packaged anchor: ' + anchor)
            bundled[anchor] = item['reference'] + '.md'
        excerpts.append((item, text))
    for name in selected['apis']:
        bundled['function-library-' + name] = 'library.md'
    manpages = json.loads(read('doc/manpage-urls.json'))
    version = read('.version').strip()
    header = (f'Nixpkgs master snapshot `{revision}`; development series {version}.\n\n'
              'Modified excerpts from the Nixpkgs contributors; see [COPYING](../COPYING). '
              'Source citations are pinned; public manual links may move.\n\n')
    documents = {name: '# ' + name.title() + '\n\n' + header for name in ['packaging', 'customization', 'helpers', 'library']}
    for item, text in excerpts:
        documents[item['reference']] += f"- [{item['heading']}](#{item['anchor']})\n"
    for name in selected['apis']:
        documents['library'] += f'- [`{name}`](#function-library-{name})\n'
    for item, text in excerpts:
        body = '\n\n' + f"[Upstream source]({UPSTREAM}/blob/{revision}/{item['path']})\n\n"
        if item.get('note'):
            body += '**Adaptation note:** ' + item['note'] + '\n\n'
        body += convert(text, item['path'], revision, anchors, bundled, manpages, read(item['path']))
        documents[item['reference']] += body
    for name in selected['apis']:
        entry = entries[name]
        path = entry['source']['file']
        read(path)
        text = f'\n\n## `{name}` {{#function-library-{name}}}\n\n' + entry['description'] + '\n'
        documents['library'] += (f'\n\n[Declaration]({UPSTREAM}/blob/{revision}/{path}#L{entry["source"]["line"]})\n'
                                 + convert(text, path, revision, anchors, bundled, manpages))
    for path in ['doc/README.md', 'doc/nav.json', 'doc/doc-support/lib-function-docs.nix',
                 'doc/doc-support/package.nix', 'pkgs/by-name/ni/nixdoc/package.nix',
                 'pkgs/by-name/ni/nixos-render-docs/src/nixos_render_docs/nixdoc.py']:
        read(path)
    inputs['generated:lib-functions.json'] = digest(library)
    files = {'references/' + name + '.md': (text.rstrip() + '\n').encode() for name, text in documents.items()}
    if (source / 'NOTICE').exists():
        raise ValueError('New upstream NOTICE requires reviewed packaging')
    files['COPYING'] = read('COPYING').encode()
    manifest = {'upstream': UPSTREAM, 'branch': 'master', 'revision': revision, 'source_version': version,
                'toolchain': old['toolchain'], 'selection': selected, 'inputs': inputs, 'coverage_inputs': coverage,
                'api_inputs': {name: digest(encoded(entries[name])) for name in selected['apis']},
                'outputs': {name: digest(data) for name, data in sorted(files.items())}}
    files['sources.json'] = encoded(manifest)
    return files, manifest


def runtime_check(source, nix, system):
    # Arguments are read as JSON so paths cannot become Nix interpolation/code.
    with tempfile.TemporaryDirectory(prefix='nixpkgs-skill-') as directory:
        args = Path(directory) / 'args.json'
        args.write_bytes(encoded({'source': str(source), 'system': system}))
        expr = f'(import {ROOT}/tests/nixpkgs/default.nix (builtins.fromJSON (builtins.readFile {args})))'
        flags = (nix, '--extra-experimental-features', 'nix-command flakes')
        if evaluate(*flags, 'eval', '--impure', '--json', '--expr', expr + '.semantics') != 'true':
            raise ValueError('Nixpkgs semantic assertions failed')
        outputs = run(*flags, 'build', '--impure', '--no-link', '--print-out-paths', '--expr',
                      f'let fixture = {expr}; in [ fixture.package fixture.shellApp ]').splitlines()
        if len(outputs) != 2:
            raise ValueError('Unexpected fixture outputs')
        packages = [Path(p) for p in outputs if (Path(p) / "message").is_file()]
        apps = [Path(p) for p in outputs if (Path(p) / "bin/nixpkgs-skill-check").is_file()]
        if len(packages) != 1 or len(apps) != 1:
            raise ValueError("Missing fixture outputs")
        package, app = packages[0], apps[0]
        if (package / 'message').read_text() != 'pinned-nixpkgs-ok\n' or (package / 'hooks').read_text() != 'prepost':
            raise ValueError('Build phase/hook output mismatch')
        if run(app / 'bin/nixpkgs-skill-check') != 'shell-helper-ok':
            raise ValueError('Shell helper output mismatch')
    print('Pinned Nixpkgs semantic, build-hook, and shell-helper checks passed')


def report(old, new):
    result = [f"Update Nixpkgs master from {old['revision']} to {new['revision']} (series {new['source_version']}).", '']
    for field in ['inputs', 'api_inputs', 'coverage_inputs']:
        before, after = old.get(field, {}), new[field]
        changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
        result += [field + ' changes:', '']
        result += ['- `' + name + '`' + (' (outside selection — review coverage)' if
                    field == 'coverage_inputs' and name not in new['inputs'] else '') for name in changed]
        if not changed:
            result.append('None; this may be a provenance-only refresh.')
        result.append('')
    return '\n'.join(result)


def validate_manifest(manifest):
    if manifest['branch'] != 'master' or not re.fullmatch(r'\d+\.\d+', manifest['source_version']):
        raise ValueError('Invalid Nixpkgs branch/development version')
    tool = manifest['toolchain']
    if (tool['upstream'] != 'https://github.com/NixOS/nix' or
            not SHA.fullmatch(tool['revision']) or not re.fullmatch(r'\d+\.\d+\.\d+', tool['release'])):
        raise ValueError('Invalid pinned evaluator')
    selection = manifest['selection']
    sections, apis = selection['sections'], selection['apis']
    if not sections or not apis or len(set(apis)) != len(apis):
        raise ValueError('Empty/duplicate Nixpkgs selection')
    if set(manifest['api_inputs']) != set(apis) or any(
            not re.fullmatch(r'[0-9a-f]{64}', h) for h in manifest['api_inputs'].values()):
        raise ValueError('Invalid selected API hashes')
    expected = {'COPYING', '.version', 'doc/function-catalog.json', 'doc/manpage-urls.json',
                'doc/README.md', 'doc/nav.json', 'doc/doc-support/lib-function-docs.nix',
                'doc/doc-support/package.nix', 'pkgs/by-name/ni/nixdoc/package.nix',
                'pkgs/by-name/ni/nixos-render-docs/src/nixos_render_docs/nixdoc.py',
                'generated:lib-functions.json'}
    for item in sections:
        if (item['reference'] not in {'packaging', 'customization', 'helpers'} or
                type(item['children']) is not bool or not item['heading'] or
                not re.fullmatch(r'[\w.:-]+', item['anchor'])):
            raise ValueError('Invalid section selection')
        expected.add(item['path'])
    if not expected <= manifest['inputs'].keys():
        raise ValueError('Missing consumed input hashes')
    for field in ['inputs', 'coverage_inputs']:
        for name in manifest[field]:
            if name == 'generated:lib-functions.json' and field == 'inputs':
                continue
            if Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name:
                raise ValueError('Invalid provenance path')


def main(args):
    from check import validate
    from update import publish
    old = validate(PACKAGE, skill='nixpkgs-development')
    revision = resolve_revision(old) if args.latest else args.revision or old['revision']
    if args.latest and revision == old['revision']:
        print('Already at recorded Nixpkgs master SHA; no update')
        return
    source, nix, system, library = pinned_inputs(old, revision)
    files, new = generate(old, revision, source, library)
    runtime_check(source, nix, system)
    if args.check:
        changed = [name for name, content in files.items() if (PACKAGE / name).read_bytes() != content]
        if changed:
            raise ValueError('Regeneration differs: ' + repr(changed))
        print('Nixpkgs source identity, reproducibility, and runtime checks passed')
    else:
        publish(files, PACKAGE, skill='nixpkgs-development')
        (ROOT / '.update-report.md').write_text(report(old, new))
        print('Generated Nixpkgs references at ' + revision)
