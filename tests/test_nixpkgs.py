import json
import copy
import shutil
import tempfile
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check
import nixpkgs
import update


class NixpkgsTests(unittest.TestCase):
    def test_conversion_preserves_code_and_context(self):
        source = ('# Parent {#parent}\n::: {.warning}\nCompatibility caveat.\n:::\n'
                  '## Child {#child}\nterm\n: definition\n'
                  '::: {.example #example}\n# Example title\n'
                  '```nix\n# not a section\n"&amp; ${value} {#literal}"\n```\n:::\n'
                  '[](#example) and {command}`echo` and `&amp;`\n## Other {#other}\n')
        selection = dict(anchor='child', heading='Child', children=False)
        text = nixpkgs.excerpt(source, selection)
        self.assertIn('Compatibility caveat.', text)
        self.assertNotIn('## Other', text)
        anchors = {}
        nixpkgs.index_anchors(source, 'doc/test.md', anchors)
        self.assertEqual(anchors['example'], {('doc/test.md', 'Example title')})
        output = nixpkgs.convert(text, 'doc/test.md', 'a'*40, anchors,
                                 {'example': 'packaging.md'}, {})
        self.assertIn('"&amp; ${value} {#literal}"', output)
        self.assertIn('`&amp;`', output)
        self.assertIn('[Example title](packaging.md#example)', output)
        self.assertIn('Definition: definition', output)
        for bad in ['::: {.unknown}\ntext\n:::\n', '[](#missing)', '{unknown}`x`', '```nix\nx']:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                nixpkgs.convert(bad, 'doc/test.md', 'a'*40, anchors, {}, {})

    def test_include_boundaries(self):
        source = '```{=include=} sections\nchild.md\n```\n'
        self.assertEqual(nixpkgs.expand_includes(source, 'doc/main.md', lambda p: '# Child\n'), '# Child\n')
        for name in ['../escape.md', '/escape.md', 'main.md']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                nixpkgs.expand_includes(source.replace('child.md', name), 'doc/main.md', lambda p: source)

    def test_automatic_revision_ancestry(self):
        old = dict(upstream=nixpkgs.UPSTREAM, branch='master', revision='a'*40)
        with patch.object(nixpkgs, 'run', return_value='a'*40+'\trefs/heads/master'), patch.object(nixpkgs, 'github_json') as api:
            self.assertEqual(nixpkgs.resolve_revision(old), old['revision'])
            api.assert_not_called()
        for status in ['ahead', 'behind', 'diverged']:
            response = dict(status=status, behind_by=0, merge_base_commit={'sha':old['revision']})
            with patch.object(nixpkgs, 'run', return_value='b'*40+'\trefs/heads/master'), patch.object(nixpkgs, 'github_json', return_value=response):
                if status == 'ahead':
                    self.assertEqual(nixpkgs.resolve_revision(old), 'b'*40)
                else:
                    with self.assertRaises(ValueError):
                        nixpkgs.resolve_revision(old)
        with self.assertRaises(ValueError):
            nixpkgs.resolve_revision(old, 'master')

    def test_package_hashes_and_links(self):
        package = nixpkgs.PACKAGE.resolve()
        manifest = json.loads((package/'sources.json').read_text())
        self.assertEqual(set(manifest['outputs']), nixpkgs.GENERATED - {'sources.json'})
        for name, expected in manifest['outputs'].items():
            self.assertEqual(nixpkgs.digest((package/name).read_bytes()), expected)
        for path in package.rglob('*.md'):
            for link in check.links(path.read_text()):
                parsed = urlsplit(link)
                if parsed.scheme:
                    self.assertIn(parsed.scheme, {'http','https'})
                    continue
                target = (path.parent/unquote(parsed.path)).resolve() if parsed.path else path
                self.assertTrue(target.is_relative_to(package) and target.is_file(), link)
                if parsed.fragment:
                    self.assertIn(unquote(parsed.fragment), check.anchors(target.read_text()), link)


    def test_policy_and_replacement_boundaries(self):
        old = json.loads((nixpkgs.PACKAGE / 'sources.json').read_text())
        for field, value in [('branch', 'other'), ('toolchain', {}), ('selection', {})]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                check.immutable_policy(old, old | {field: value}, 'nixpkgs-development')
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'nixpkgs-development'
            shutil.copytree(nixpkgs.PACKAGE, package)
            original = {name: (package/name).read_bytes() for name in nixpkgs.GENERATED}
            files = dict(original)
            files['COPYING'] += b'\n'
            with self.assertRaises(ValueError):
                update.publish(files, package, skill='nixpkgs-development')
            manifest = json.loads(files['sources.json'])
            manifest['outputs']['COPYING'] = update.digest(files['COPYING'])
            files['sources.json'] = update.encoded(manifest)
            replace, calls = update.os.replace, []
            def fail_second(source, target):
                calls.append(target)
                if len(calls) == 2:
                    raise OSError('simulated partial replacement')
                replace(source, target)
            with patch.object(update.os, 'replace', side_effect=fail_second), self.assertRaises(OSError):
                update.publish(files, package, skill='nixpkgs-development')
            self.assertEqual(original, {name: (package/name).read_bytes() for name in original})

    def test_schema_and_missing_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source/'lib').mkdir()
            (source/'lib/test.nix').write_text('x: x\n')
            record = dict(id='lib.test', attrPath='lib.test', description='Example',
                          source=dict(file='lib/test.nix', line=1))
            document = dict(schemaVersion=1, groups=[], entries=[record])
            self.assertIn('lib.test', nixpkgs.parse_library(json.dumps(document), source)[1])
            for invalid in [document | {'schemaVersion': 2},
                            document | {'entries': [record, record]},
                            document | {'entries': [record | {'source': dict(file='../escape', line=1)}]}]:
                with self.assertRaises(ValueError):
                    nixpkgs.parse_library(json.dumps(invalid), source)
            for name, content in {
                    'doc/test.md': '# Selected {#selected}\nPinned prose.\n',
                    'doc/function-catalog.json': '{"sources": []}',
                    'doc/manpage-urls.json': '{}', '.version': '26.11', 'COPYING': 'MIT',
                    'doc/README.md': '# Syntax\n', 'doc/nav.json': '{}',
                    'doc/doc-support/lib-function-docs.nix': '{}',
                    'doc/doc-support/package.nix': '{}',
                    'pkgs/by-name/ni/nixdoc/package.nix': '{}',
                    'pkgs/by-name/ni/nixos-render-docs/src/nixos_render_docs/nixdoc.py': '# renderer',
            }.items():
                path = source/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            old = dict(toolchain={}, selection=dict(apis=['lib.test'], sections=[dict(
                reference='packaging', path='doc/test.md', anchor='selected', heading='Selected', children=False)]))
            generated = nixpkgs.generate(old, 'a'*40, source, json.dumps(document).encode())
            self.assertEqual(generated, nixpkgs.generate(old, 'a'*40, source, json.dumps(document).encode()))
            (source/'doc/test.md').write_text('# Selected {#selected}\nChanged prose.\n')
            self.assertNotEqual(generated, nixpkgs.generate(old, 'b'*40, source, json.dumps(document).encode()))
            old = dict(selection=dict(apis=['lib.missing'], sections=[]))
            with self.assertRaisesRegex(ValueError, 'Missing selected API'):
                nixpkgs.generate(old, 'a'*40, source, json.dumps(document).encode())

    def test_noop_and_provenance_report(self):
        from argparse import Namespace
        old = json.loads((nixpkgs.PACKAGE/'sources.json').read_text())
        with patch.object(nixpkgs, 'resolve_revision', return_value=old['revision']), \
             patch.object(nixpkgs, 'pinned_inputs', side_effect=AssertionError('No-op built tools')):
            nixpkgs.main(Namespace(latest=True, check=False, revision=None))
        changed = copy.deepcopy(old)
        changed['revision'] = 'b'*40
        self.assertIn('provenance-only', nixpkgs.report(old, changed))
        changed['coverage_inputs']['doc/new.md'] = '0'*64
        self.assertIn('outside selection', nixpkgs.report(old, changed))


if __name__ == '__main__':
    unittest.main()
