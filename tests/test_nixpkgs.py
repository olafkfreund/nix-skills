import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check
import nixpkgs


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
        with patch.object(nixpkgs, 'run', return_value='a'*40+'\trefs/heads/master'), patch.object(nixpkgs, 'urlopen') as api:
            self.assertEqual(nixpkgs.resolve_revision(old), old['revision'])
            api.assert_not_called()
        for status in ['ahead', 'behind', 'diverged']:
            response = dict(status=status, behind_by=0, merge_base_commit={'sha':old['revision']})
            with patch.object(nixpkgs, 'run', return_value='b'*40+'\trefs/heads/master'), patch.object(nixpkgs, 'urlopen'), patch.object(nixpkgs.json, 'load', return_value=response):
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


if __name__ == '__main__':
    unittest.main()
