"""Release-pinned devenv excerpts; deliberately limited Markdown/MDX conversion."""

import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from update import ROOT, check_external, digest, encoded, prose, publish, run, section

PACKAGE = ROOT / 'skills/devenv-project'
UPSTREAM = 'https://github.com/cachix/devenv'
DOCS = 'docs/src/content/docs/'
SETUP = 'docs/public/.well-known/agent-skills/devenv-setup/SKILL.md'
GENERATED = {'references/configuration.md', 'references/workflows.md',
             'references/options.md', 'sources.json', 'LICENSE'}
RELEASE = re.compile(r'v[0-9]+\.[0-9]+(?:\.[0-9]+)?')


def version(release):
    if not RELEASE.fullmatch(release):
        raise ValueError('Unsupported stable release tag')
    return release[1:] + ('.0' if release.count('.') == 1 else '')


def api(path):
    with urlopen(Request('https://api.github.com/repos/cachix/devenv/' + path,
                         headers={'User-Agent': 'nix-skills'}), timeout=30) as response:
        return json.load(response)


def resolve_release(old, requested):
    version(requested)
    version(old['release'])
    releases = {name: api('releases/tags/' + name) for name in {old['release'], requested}}
    refs = {}
    for line in run('git', 'ls-remote', '--tags', UPSTREAM + '.git',
                    'refs/tags/' + old['release'] + '*', 'refs/tags/' + requested + '*').splitlines():
        sha, ref = line.split()
        name = ref.removeprefix('refs/tags/').removesuffix('^{}')
        if ref.endswith('^{}') or name not in refs:
            refs[name] = sha
    if refs.get(old['release']) != old['revision']:
        raise ValueError('Pinned devenv tag disappeared or moved')
    for name, release in releases.items():
        if not RELEASE.fullmatch(name) or release['tag_name'] != name or release['draft'] or release['prerelease']:
            raise ValueError('Expected a stable published devenv release')
    if requested not in refs:
        raise ValueError('Release tag is missing')
    return refs[requested]


def pinned_tools(revision, release):
    ref = 'github:cachix/devenv/' + revision
    flags = ('nix', '--extra-experimental-features', 'nix-command flakes')
    metadata = json.loads(run(*flags, 'flake', 'metadata', '--json', ref))
    fetched = json.loads(run(*flags, 'flake', 'prefetch', '--json', ref))
    if metadata['locked']['rev'] != revision or metadata['path'] != fetched['storePath']:
        raise ValueError('Resolved devenv source mismatch')
    cargo = (Path(fetched['storePath']) / 'Cargo.toml').read_text()
    declared = re.search(r'(?m)^\[workspace.package\]\nversion = "([^"]+)"$', cargo)
    if not declared or declared[1] != version(release):
        raise ValueError('Source version differs from release')
    output = run(*flags, 'build', '--no-link', '--print-out-paths', ref + '#devenv')
    cli = Path(output) / 'bin/devenv'
    if not re.match(r'devenv ' + re.escape(version(release)) + r'(?:\+[0-9a-f]+)?(?:\s|$)', run(cli, 'version')):
        raise ValueError('Built devenv CLI version mismatch')
    return Path(fetched['storePath']), cli


def page(text):
    match = re.match(r'\A---\n(.*?)\n---\n', text, re.S)
    if not match:
        raise ValueError('Missing document frontmatter')
    title = re.search(r'^title: (.+)$', match[1], re.M)
    if not title:
        raise ValueError('Missing document title')
    title = title[1].strip('"\'')
    body = text[match.end():]
    allowed_imports = {
        "import { Tabs, TabItem } from '@astrojs/starlight/components';",
        "import VersionCompatibility from '@cachix/site-kit/ui/VersionCompatibility.astro';",
    }
    def validate_import(line):
        if re.match(r'\s*(?:import|export)\b', line) and line.strip() not in allowed_imports:
            raise ValueError('Unknown MDX import/export')
        return line
    prose(body, validate_import)
    return '# ' + title + '\n' + body


def excerpt(text, heading):
    """Retain version notices from ancestor introductions, not unrelated siblings."""
    text = page(text)
    headings = []
    offset = 0

    def collect(line):
        nonlocal offset
        match = re.match(r'^(#{1,6}) (.+?)\s*$', line)
        if match:
            headings.append((offset, len(match[1]), match[2]))
        return line

    # Preserve offsets while excluding fenced examples from heading detection.
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        elif fence is None:
            collect(line)
        offset += len(line)
    matches = [i for i, h in enumerate(headings) if h[2] == heading]
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous section: ' + heading)
    index = matches[0]
    ancestors = []
    for i, item in enumerate(headings[:index]):
        while ancestors and headings[ancestors[-1]][1] >= item[1]:
            ancestors.pop()
        ancestors.append(i)
    ancestors = [i for i in ancestors if headings[i][1] < headings[index][1]]
    notices = []
    for i in ancestors:
        introduction = text[headings[i][0]:headings[i + 1][0]]
        def notice(line):
            if re.match(r'\s*(?:<small class="added-in">|<VersionCompatibility\b|:::(?:tip|note)\[(?:New in|Added in))', line):
                # Keep the complete admonition, including its version context.
                if line.lstrip().startswith(':::'):
                    start = introduction.index(line)
                    end = introduction.find('\n:::', start + len(line))
                    if end < 0:
                        raise ValueError('Unclosed inherited version notice')
                    notices.append(introduction[start:end + 5])
                else:
                    notices.append(line)
            return line
        prose(introduction, notice)
    return '\n'.join(notices) + '\n' + section(text, heading)


def convert(text, path):
    """Only supported wrappers are interpreted. Fenced code is never parsed as MDX."""
    output, stack = [], []
    fence = None
    tab = False
    tabs = False
    base = 'https://devenv.sh/' + re.sub(r'\.mdx?$', '/', path)
    for raw in text.splitlines(keepends=True):
        line = raw
        if tab and line.startswith('    '):
            line = line[4:]
        marker = re.match(r'^\s*(`{3,}|~{3,})(.*)\n?$', line)
        if fence:
            output.append(line)
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
            continue
        if marker:
            fence = marker[1]
            info = marker[2].strip()
            title = re.search(r'\btitle="([^"]+)"', info)
            if title:
                output.append('\nFile: `' + title[1] + '`\n\n')
            info = re.sub(r'\s*(?:title|hl_lines)="[^"]*"', '', info)
            if not re.fullmatch(r'[\w+-]*', info):
                raise ValueError('Unknown fence metadata: ' + info)
            output.append(marker[1] + info + '\n')
            continue
        stripped = line.strip()
        if stripped == "import VersionCompatibility from '@cachix/site-kit/ui/VersionCompatibility.astro';":
            continue
        if stripped == "import { Tabs, TabItem } from '@astrojs/starlight/components';":
            continue
        if stripped == '<Tabs>':
            if tabs:
                raise ValueError('Nested tabs are unsupported')
            tabs = True
            continue
        match = re.fullmatch(r'<TabItem label="([^"<>]+)">', stripped)
        if match:
            if not tabs or tab:
                raise ValueError('Malformed TabItem')
            tab = True
            output.append('\n### ' + match[1] + '\n\n')
            continue
        if stripped == '</TabItem>':
            if not tab:
                raise ValueError('Unmatched TabItem')
            tab = False
            continue
        if stripped == '</Tabs>':
            if not tabs or tab:
                raise ValueError('Unmatched Tabs')
            tabs = False
            continue
        match = re.fullmatch(r':::(note|tip|caution|danger)(?:\[([^\]]+)\])?', stripped)
        if match:
            label = {'caution': 'Warning', 'danger': 'Danger', 'note': 'Note', 'tip': 'Tip'}[match[1]]
            stack.append(label)
            output.append('\n**' + label + (': ' + match[2] if match[2] else '') + '**\n\n')
            continue
        if stripped == ':::':
            if not stack:
                raise ValueError('Unmatched admonition')
            output.append('\n**End ' + stack.pop().lower() + '.**\n\n')
            continue
        line = re.sub(r'<small class="added-in">Added in <code>([\d.]+)</code></small>',
                      r'**Added in version \1.**', line)
        # Support only the explicit single-version form; other props need review.
        line = re.sub(r'<VersionCompatibility version="([\d.]+)"\s*/>',
                      r'**Requires version \1 or later.**', line)
        if re.fullmatch(r'\s*<!--[^\n]*-->\s*', line):
            continue
        protected = re.sub(r'(`+).*?\1', '', line)
        protected = re.sub(r'\]\([^\s)]+\)', '', protected)
        if re.search(r'<[/A-Za-z]|(?<!\\)[{}]|^\s*(?:import\b|export\b|:::)|\]\[|^\s*\[[^\]]+\]:', protected):
            raise ValueError('Unsupported MDX in ' + path + ': ' + line.strip())
        def link(match):
            target = match[1]
            if target.startswith('<'):
                raise ValueError('Unsupported angle-delimited link')
            if target.startswith('//'):
                raise ValueError('Protocol-relative link')
            if urlsplit(target).scheme:
                return match[0]
            target = re.sub(r'\.mdx?(?=#|$)', '/', target)
            resolved = urljoin(base, target)
            if not resolved.startswith('https://devenv.sh/'):
                raise ValueError('Ambiguous documentation link')
            return '](' + resolved + ')'
        parts = re.split(r'(`+.*?`+)', line)
        line = ''.join(part if i % 2 else re.sub(r'\]\(([^\s)]+)\)', link, part)
                       for i, part in enumerate(parts))
        output.append(line.rstrip() + '\n')
    if fence or stack or tab or tabs:
        raise ValueError('Unclosed MDX wrapper or code fence')
    return ''.join(output).strip() + '\n'


def generate(old, release, revision, source):
    inputs = {}
    def read(path):
        file = source / path
        if not file.resolve().is_relative_to(source.resolve()):
            raise ValueError('Source path escapes checkout')
        data = file.read_bytes()
        inputs[path] = digest(data)
        return data.decode()
    header = (f'devenv {release}; upstream revision `{revision}`.\n\n'
              'Modified excerpts from the devenv contributors; see [LICENSE](../LICENSE). '
              'Source citations are pinned; devenv.sh links follow the moving public site.\n\n')
    documents = {}
    for name in ['configuration', 'workflows', 'options']:
        selected = [s for s in old['selection']['sections'] if s['reference'] == name]
        content = '# ' + name.title() + '\n\n' + header
        for i, item in enumerate(selected, 1):
            content += f"- [{item['path']}: {item['heading']}](#section-{i})\n"
        if name == 'options':
            content += '- [Selected option records](#selected-options)\n'
        content += '\n'
        for i, item in enumerate(selected, 1):
            path = DOCS + item['path']
            content += (f'<a id="section-{i}"></a>\n\n'
                        f'[Upstream source]({UPSTREAM}/blob/{revision}/{path})\n\n'
                        + convert(excerpt(read(path), item['heading']), item['path']) + '\n')
        documents[name] = content
    data = json.loads(read('docs/src/data/options.json'))
    options = '\n<a id="selected-options"></a>\n\n## Selected option records\n\n'
    examples = ['languages.python.enable', 'languages.javascript.enable', 'languages.rust.enable',
                'languages.go.enable', 'services.postgres.enable']
    options += 'Minimal enablement examples (choose those needed by the project):\n\n```nix\n{ ... }: {\n'
    for name in examples:
        if name not in old['selection']['options'] or name not in data or data[name].get('example') != {'_type': 'literalExpression', 'text': 'true'}:
            raise ValueError('Enablement example changed: ' + name)
        options += '  ' + name + ' = true;\n'
    options += '}\n```\n\n'
    options += (f'[Committed upstream data]({UPSTREAM}/blob/{revision}/docs/src/data/options.json). '
                'Rendered from this artifact, not rebuilt. Foreign declaration links retain their origin '
                'and may move independently.\n\n')
    option_hashes = {}
    for i, name in enumerate(old['selection']['options'], 1):
        if name not in data:
            raise ValueError('Missing option: ' + name)
        options += f'- [`{name}`](#option-{i})\n'
    for i, name in enumerate(old['selection']['options'], 1):
        record = data[name]
        option_hashes[name] = digest(encoded(record))
        options += f'\n<a id="option-{i}"></a>\n\n### `{name}`\n\n'
        options += convert(record['description'], 'reference/options.md') + '\n'
        options += 'Type: `' + record['type'] + '`\n\n'
        for field in ['default', 'example']:
            if field not in record:
                continue
            value = record[field]
            if isinstance(value, dict) and value.get('_type') == 'literalExpression':
                options += field.title() + ':\n\n```nix\n' + value['text'] + '\n```\n\n'
            else:
                raise ValueError('Unsupported option value encoding: ' + name)
        for declaration in record['declarations']:
            url = declaration['url']
            prefix = UPSTREAM + '/blob/main/'
            if url.startswith(prefix):
                target = url[len(prefix):]
                if not (source / target).exists() or not (source / target).resolve().is_relative_to(source.resolve()):
                    raise ValueError('Missing declaration: ' + target)
                url = UPSTREAM + '/blob/' + revision + '/' + target
            options += '[Declaration](' + url + ')\n\n'
    documents['options'] += options
    for path in old['selection']['provenance']:
        read(path)
    read(SETUP)
    def pin_declarations(line):
        def pin(match):
            target = match[1]
            if not (source / target).exists() or not (source / target).resolve().is_relative_to(source.resolve()):
                raise ValueError('Missing declaration: ' + target)
            return UPSTREAM + '/blob/' + revision + '/' + target
        return re.sub(re.escape(UPSTREAM + '/blob/main/') + r'([^\s)<>\]]+)', pin, line)
    files = {'references/' + name + '.md': (prose(content, pin_declarations).rstrip() + '\n').encode()
             for name, content in documents.items()}
    if (source / 'NOTICE').exists():
        raise ValueError('Upstream added NOTICE; review package notice selection and allowlist')
    files['LICENSE'] = read('LICENSE').encode()
    coverage = {str(p.relative_to(source)): digest(p.read_bytes())
                for p in sorted((source / DOCS).rglob('*')) if p.suffix in {'.md', '.mdx'}}
    coverage[SETUP] = inputs[SETUP]
    manifest = {'upstream': UPSTREAM, 'release': release, 'revision': revision,
                'devenv_version': version(release), 'selection': old['selection'], 'inputs': inputs,
                'documentation_inputs': coverage, 'option_inputs': option_hashes,
                'outputs': {name: digest(value) for name, value in sorted(files.items())}}
    files['sources.json'] = encoded(manifest)
    return files, manifest


def report(old, new):
    rows = [f"Update devenv references from {old['release']} ({old['revision']}) "
            f"to {new['release']} ({new['revision']}).", '']
    for field in ['inputs', 'option_inputs', 'documentation_inputs']:
        before, after = old.get(field, {}), new[field]
        changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
        rows += [field + ' changes:', '']
        rows += ['- `' + p + '`' + (' (outside selection — review coverage)' if
                 field == 'documentation_inputs' and p not in new['inputs'] else '') for p in changed]
        if not changed:
            rows.append('None.')
        rows.append('')
    rows.append('Upstream setup skill changes require review; authored SKILL.md is never replaced.')
    return '\n'.join(rows) + '\n'


def main(args):
    old = json.loads((PACKAGE / 'sources.json').read_text())
    requested = api('releases/latest')['tag_name'] if args.latest else args.release or old['release']
    revision = resolve_release(old, requested)
    if args.latest and revision == old['revision']:
        print('Already at newest stable devenv release; no update')
        return
    source, cli = pinned_tools(revision, requested)
    files, new = generate(old, requested, revision, source)
    check_external([v.decode() for k, v in files.items() if k.endswith('.md')], 'https://devenv.sh/')
    from check_devenv import runtime_check
    runtime_check(source, cli, revision)
    if args.check:
        changed = [name for name, content in files.items() if (PACKAGE / name).read_bytes() != content]
        if changed:
            raise ValueError('Regeneration differs: ' + repr(changed))
        print('Devenv reproducibility, links, and runtime checks passed')
    else:
        publish(files, PACKAGE, skill='devenv-project')
        (ROOT / '.update-report.md').write_text(report(old, new))
        print('Generated devenv ' + requested + ' references at ' + revision)
