"""Bounded MediaWiki snapshot ingestion and offline regeneration; no wiki execution."""

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.request import Request, urlopen
from xml.parsers import expat

from update import ROOT, digest, encoded

PACKAGE = ROOT / 'skills/nixos-wiki'
UPSTREAM = 'https://wiki.nixos.org/wikidump.xml.zst'
ORIGIN = 'https://wiki.nixos.org'
XMLNS = 'http://www.mediawiki.org/xml/export-0.11/'
COPYRIGHT = 'Official NixOS Wiki:Copyrights'
TITLES = ['NixOS', 'NixOS modules', 'NixOS Installation Guide', 'Nixos-rebuild',
          'Updating NixOS', 'Flakes', 'Home Manager', 'Bootloader', 'Linux kernel',
          'Storage optimization', 'Garbage Collection', 'Networking', 'Firewall',
          'SSH', 'Systemd', 'Systemd/User Services', 'Systemd/timers']
LIMITS = dict(compressed=128*1024**2, expanded=1024**3, text=1024**2, pages=50000, revisions=500000)
POLICY = dict(titles=TITLES, template_namespace=10, copyright_title=COPYRIGHT,
              copyright_revision=22887, xml_namespace=XMLNS, limits=LIMITS)
GENERATED = {'references/index.md', 'references/pages.json', 'references/templates.json', 'sources.json', 'COPYING'}
HASH = re.compile(r'[0-9a-f]{64}')


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', value):
        raise ValueError('Invalid wiki timestamp')
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')


def identity(value):
    if not isinstance(value, str) or not re.fullmatch(r'[1-9][0-9]*', value):
        raise ValueError('Invalid wiki numeric identity')
    return int(value)


def citation(record):
    return ORIGIN + '/w/index.php?oldid=' + str(record['revision_id'])


def redirect(text):
    match = re.match(r'^\s*#redirect\s*\[\[([^\]\n]+)\]\]', text, re.I)
    if not match:
        return None
    target, _, fragment = match[1].partition('#')
    if not target.strip() or '|' in match[1]:
        raise ValueError('Invalid redirect target')
    return {'title': target.strip().replace('_', ' '), 'fragment': fragment}


def extract(stream, limits=LIMITS):
    """Expat callbacks bound text as it arrives and retain only one revision per page."""
    parser = expat.ParserCreate(namespace_separator='}')
    stack, fields, chunks = [], {}, {}
    page_ids, revision_ids, titles = set(), set(), set()
    pages, templates = {}, {}
    page = best = None
    counts = dict(pages=0, revisions=0, expanded=0)
    text_bytes = 0

    def reject(*args):
        raise ValueError('DTD/entity declarations are not supported')

    def start(name, attrs):
        nonlocal page, best, fields, chunks, text_bytes
        if not name.startswith(XMLNS + '}'):
            raise ValueError('Unsupported XML namespace')
        local = name.split('}', 1)[1]
        stack.append(local)
        if len(stack) > 4 and stack[:3] == ['mediawiki', 'page', 'revision'] and stack[3] in {'id', 'timestamp', 'model', 'text'}:
            raise ValueError('Nested markup in XML scalar field')
        if len(stack) > 32:
            raise ValueError('XML nesting limit exceeded')
        if len(stack) == 1 and (local != 'mediawiki' or attrs.get('version') != '0.11'):
            raise ValueError('Unsupported export schema')
        if stack == ['mediawiki', 'page']:
            counts['pages'] += 1
            if counts['pages'] > limits['pages']:
                raise ValueError('Page count limit exceeded')
            page, best = {}, None
        elif stack == ['mediawiki', 'page', 'revision']:
            counts['revisions'] += 1
            if counts['revisions'] > limits['revisions']:
                raise ValueError('Revision count limit exceeded')
            fields, chunks, text_bytes = {}, {}, 0
        elif stack == ['mediawiki', 'page', 'redirect']:
            if not attrs.get('title'):
                raise ValueError('Redirect without title')
            page['redirect_title'] = attrs['title']
        elif len(stack) == 3 and stack[:2] == ['mediawiki', 'page'] and local in {'title', 'ns', 'id'}:
            if local in page:
                raise ValueError('Duplicate page metadata')
            page[local] = ''
        elif len(stack) == 4 and stack[:3] == ['mediawiki', 'page', 'revision'] and local in {'id', 'timestamp', 'model', 'text'}:
            if local in chunks:
                raise ValueError('Duplicate revision field')
            chunks[local] = []
            if local == 'text':
                fields['suppressed'] = 'deleted' in attrs or 'suppressed' in attrs

    def characters(data):
        nonlocal text_bytes
        if len(stack) == 3 and stack[:2] == ['mediawiki', 'page'] and stack[-1] in {'title', 'ns', 'id'}:
            page[stack[-1]] += data
            if len(page[stack[-1]]) > 4096:
                raise ValueError('Page metadata too long')
        elif len(stack) == 4 and stack[:3] == ['mediawiki', 'page', 'revision'] and stack[-1] in chunks:
            if stack[-1] == 'text':
                text_bytes += len(data.encode())
                if text_bytes > limits['text']:
                    raise ValueError('Revision text limit exceeded')
            elif sum(map(len, chunks[stack[-1]])) + len(data) > 4096:
                raise ValueError('Revision metadata too long')
            chunks[stack[-1]].append(data)

    def end(name):
        nonlocal best, fields, chunks
        if stack == ['mediawiki', 'page', 'revision']:
            fields.update({key: ''.join(value) for key, value in chunks.items()})
            revision_id = identity(fields.get('id'))
            if revision_id in revision_ids:
                raise ValueError('Duplicate revision ID')
            revision_ids.add(revision_id)
            order = (timestamp(fields.get('timestamp')), revision_id)
            if best is None or order > best[0]:
                best = (order, fields)
            fields, chunks = {}, {}
        elif stack == ['mediawiki', 'page']:
            page_id = identity(page.get('id'))
            title = page.get('title')
            if not title or title in titles or page_id in page_ids or best is None:
                raise ValueError('Missing/duplicate page identity or revision')
            titles.add(title)
            page_ids.add(page_id)
            namespace = int(page['ns'])
            wanted = title in TITLES or title == COPYRIGHT or namespace == 10
            if wanted:
                current = best[1]
                if current.get('suppressed') or 'text' not in current or current.get('model') != 'wikitext':
                    raise ValueError('Missing/suppressed/non-wikitext content: ' + title)
                record = dict(title=title, namespace=namespace, page_id=page_id,
                              revision_id=identity(current['id']), timestamp=current['timestamp'],
                              model=current['model'], text=current['text'], sha256=digest(current['text'].encode()),
                              redirect=redirect(current['text']))
                target = record['redirect']['title'] if record['redirect'] else None
                if page.get('redirect_title', '').replace('_', ' ') != (target or ''):
                    raise ValueError('Redirect metadata disagrees with latest text: ' + title)
                (templates if namespace == 10 else pages)[title] = record
            best = None
        stack.pop()

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = characters
    parser.StartDoctypeDeclHandler = reject
    parser.EntityDeclHandler = reject
    parser.ExternalEntityRefHandler = reject
    for chunk in iter(lambda: stream.read(65536), b''):
        counts['expanded'] += len(chunk)
        if counts['expanded'] > limits['expanded']:
            raise ValueError('Expanded input limit exceeded')
        parser.Parse(chunk, False)
    parser.Parse(b'', True)
    validate_records(pages, templates)
    return pages, templates


def hash_file(path):
    hasher, size = hashlib.sha256(), 0
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            size += len(chunk)
            if size > LIMITS['compressed']:
                raise ValueError('Compressed input limit exceeded')
            hasher.update(chunk)
    return hasher.hexdigest()


def read_dump(path, expected):
    if not HASH.fullmatch(expected) or hash_file(path) != expected:
        raise ValueError('Dump SHA-256 mismatch')
    with tempfile.TemporaryFile() as errors:
        proc = subprocess.Popen(['zstd', '-dc', '--', str(path)], stdout=subprocess.PIPE, stderr=errors)
        try:
            result = extract(proc.stdout)
            if proc.wait(timeout=30) != 0:
                raise ValueError('Zstandard integrity/decompression failure')
            return result
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            proc.stdout.close()


def download(path):
    with urlopen(Request(UPSTREAM, headers={'User-Agent': 'nix-skills-wiki'}), timeout=30) as response:
        if response.geturl() != UPSTREAM:
            raise ValueError('Unexpected wiki download redirect')
        length = response.headers.get('Content-Length')
        if length is not None and int(length) > LIMITS['compressed']:
            raise ValueError('Compressed input limit exceeded')
        total = 0
        with path.open('wb') as output:
            for data in iter(lambda: response.read(65536), b''):
                total += len(data)
                if total > LIMITS['compressed']:
                    raise ValueError('Compressed input limit exceeded')
                output.write(data)
        if length is not None and total != int(length):
            raise ValueError('Truncated download')
    return hash_file(path)


def validate_records(pages, templates):
    if set(pages) != set(TITLES) | {COPYRIGHT} or not templates:
        raise ValueError('Missing/unexpected retained pages or empty templates')
    ids, revisions = set(), set()
    for title, record in (pages | templates).items():
        required = {'title', 'namespace', 'page_id', 'revision_id', 'timestamp', 'model', 'text', 'sha256', 'redirect'}
        if set(record) != required or record['title'] != title or len(title) > 4096:
            raise ValueError('Invalid record schema')
        expected_ns = 10 if title in templates else 4 if title == COPYRIGHT else 0
        if type(record['namespace']) is not int or record['namespace'] != expected_ns or (expected_ns == 10 and not title.startswith('Template:')):
            raise ValueError('Unexpected retained namespace')
        for key, seen in [('page_id', ids), ('revision_id', revisions)]:
            value = record[key]
            if type(value) is not int or value <= 0 or value in seen:
                raise ValueError('Invalid/duplicate retained identity')
            seen.add(value)
        timestamp(record['timestamp'])
        if (record['model'] != 'wikitext' or not isinstance(record['text'], str) or
                len(record['text'].encode()) > LIMITS['text'] or digest(record['text'].encode()) != record['sha256'] or
                record['redirect'] != redirect(record['text'])):
            raise ValueError('Invalid retained text/hash/redirect')
    if set(pages) & set(templates) or pages[COPYRIGHT]['revision_id'] != POLICY['copyright_revision']:
        raise ValueError('Copyright policy or namespace overlap requires review')
    for title in TITLES:
        seen = set()
        while pages[title]['redirect']:
            if title in seen or len(seen) >= 16:
                raise ValueError('Primary redirect cycle/limit')
            seen.add(title)
            title = pages[title]['redirect']['title']
            if title not in TITLES:
                raise ValueError('Primary redirect target unavailable')


def generate(pages, templates, snapshot):
    validate_records(pages, templates)
    if not HASH.fullmatch(snapshot):
        raise ValueError('Invalid dump hash')
    license_blocks = re.findall(r'<pre>\s*(MIT License\n.*?)</pre>', pages[COPYRIGHT]['text'], re.S)
    if len(license_blocks) != 1 or 'Copyright (c) 2025 NixOS Foundation and contributors' not in license_blocks[0]:
        raise ValueError('Unsupported copyright notice')
    files = {'references/pages.json': encoded(pages), 'references/templates.json': encoded(templates),
             'COPYING': (license_blocks[0].strip() + '\n').encode()}
    lines = ['# NixOS Wiki snapshot', '', 'Curated raw wikitext; templates are retained, not expanded.', '',
             'Dump SHA-256: `' + snapshot + '`.', '',
             'Use `python3 scripts/wiki.py search QUERY` or `show TITLE` from this skill directory.',
             'Read page-level notices and complete relevant examples before applying advice.', '',
             '## Topics', '']
    for title in TITLES:
        record = pages[title]
        lines.append(f'- [{title}]({citation(record)}) — revision {record["revision_id"]}, {record["timestamp"]}.')
    lines += ['', '## Retained inputs', '', '[Page records](pages.json) and [template records](templates.json) retain original wikitext.',
              'The helper reads individual records; do not load the whole corpus into context.',
              'Other topics and unbundled transclusions require checking the live wiki or official source.',
              'Article revision links can render with newer templates on the live website.', '',
              'Text by the NixOS Foundation and contributors; see [COPYING](../COPYING).',
              'History, contributors’ metadata and media are omitted. Wikitext is not rewritten.', '']
    files['references/index.md'] = '\n'.join(lines).encode()
    manifest = dict(upstream=UPSTREAM, snapshot_sha256=snapshot, policy=POLICY,
                    inputs={title: digest(encoded(record)) for title, record in sorted((pages | templates).items())},
                    records={title: {k: v for k, v in record.items() if k != 'text'}
                             for title, record in sorted((pages | templates).items())},
                    outputs={name: digest(data) for name, data in sorted(files.items())})
    files['sources.json'] = encoded(manifest)
    if any(len(data) > 2_000_000 for data in files.values()):
        raise ValueError('Generated file exceeds artifact limit')
    return files, manifest


def validate_snapshot(package):
    for name in GENERATED:
        path = package / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
            raise ValueError('Invalid/oversize snapshot file')
    old = json.loads((package / 'sources.json').read_text())
    if old['upstream'] != UPSTREAM or old['policy'] != POLICY:
        raise ValueError('Unexpected wiki policy/origin')
    pages = json.loads((package / 'references/pages.json').read_text())
    templates = json.loads((package / 'references/templates.json').read_text())
    files, manifest = generate(pages, templates, old['snapshot_sha256'])
    if old != manifest or any((package / name).read_bytes() != data for name, data in files.items()):
        raise ValueError('Wiki offline regeneration/hash mismatch')
    return old


def changes(old_pages, old_templates, pages, templates):
    validate_records(pages, templates)
    return transition(old_pages | old_templates, pages | templates)


def transition(before, after):
    if before[COPYRIGHT] != after[COPYRIGHT]:
        raise ValueError('Copyright policy changed; reviewed task required')
    report = []
    for title in sorted(before.keys() | after.keys()):
        old, new = before.get(title), after.get(title)
        if old == new:
            continue
        if old is None or new is None:
            report.append(f'- Template {"added" if old is None else "removed"}: {title}')
            continue
        if new['page_id'] != old['page_id']:
            raise ValueError('Page identity changed: ' + title)
        if new['revision_id'] < old['revision_id'] or timestamp(new['timestamp']) < timestamp(old['timestamp']):
            raise ValueError('Revision regression: ' + title)
        if new['revision_id'] == old['revision_id']:
            raise ValueError('Unchanged revision identity mutated: ' + title)
        kind = 'content' if old['sha256'] != new['sha256'] else 'provenance-only'
        extra = '; redirect changed' if old['redirect'] != new['redirect'] else ''
        report.append(f'- {title}: {old["revision_id"]} → {new["revision_id"]} ({kind}{extra})')
    return report


def main(args):
    from check import validate
    from update import publish
    old = validate(PACKAGE, skill='nixos-wiki')
    if args.check:
        lookup_check(PACKAGE)
        print('Wiki offline hashes, retained-source regeneration, and package checks passed')
        return
    with tempfile.TemporaryDirectory(prefix='nixos-wiki-') as directory:
        path = Path(args.dump) if args.dump else Path(directory) / 'dump.xml.zst'
        snapshot = args.sha256 if args.dump else download(path)
        if args.dump and hash_file(path) != snapshot:
            raise ValueError('Dump SHA-256 mismatch')
        if snapshot == old['snapshot_sha256']:
            print('Already at this dump snapshot; no update')
            return
        pages, templates = read_dump(path, snapshot)
        old_pages = json.loads((PACKAGE / 'references/pages.json').read_text())
        old_templates = json.loads((PACKAGE / 'references/templates.json').read_text())
        report = changes(old_pages, old_templates, pages, templates)
        if not report:
            print('No retained page/template changes; keeping accepted provenance')
            return
        files, _ = generate(pages, templates, snapshot)
        lookup_check(PACKAGE, pages | templates)
        publish(files, PACKAGE, skill='nixos-wiki')
        (ROOT / '.update-report.md').write_text(
            f'Wiki snapshot `{old["snapshot_sha256"]}` → `{snapshot}`.\n\n' + '\n'.join(report) + '\n')
        print('Updated retained wiki records; see .update-report.md')


def lookup_check(package, records=None):
    from runpy import run_path
    helper = run_path(str(package / 'scripts/wiki.py'))
    if records is None:
        _, records = helper['load'](package)
    if not helper['search'](records, 'rebuild'):
        raise ValueError('Lookup search returned no expected result')
    # Exercise whichever redirects the snapshot retains; upstream may add or drop them.
    for title, source in records.items():
        if source['namespace'] != 0 or not source['redirect']:
            continue
        hops, record, missing = helper['route'](records, title, True)
        if missing or not hops or record['title'] != hops[-1]['redirect']['title']:
            raise ValueError('Bundled redirect lookup failed: ' + title)
    body, _, _ = helper['window'](records['NixOS modules']['text'])
    if not body or len(body.encode()) > 16384:
        raise ValueError('Lookup window bound failed')
