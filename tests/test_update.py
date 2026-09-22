import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check
import update


class UpdateTests(unittest.TestCase):
    def test_section_and_code_preservation(self):
        source = '# Page\nintro\n## Chosen\n```nix\n## example comment\n```\nbody\n## Other\nno\n'
        excerpt = update.section(source, 'Chosen')
        self.assertIn('## example comment', excerpt)
        self.assertNotIn('## Other', excerpt)
        with self.assertRaises(ValueError):
            update.section(source, 'Absent')
        with self.assertRaises(ValueError):
            update.section(source + '\n## Chosen\nagain\n', 'Chosen')

    def test_render_links_without_changing_examples(self):
        source = ('# Example\n[other][target] and [target].\n'
                  '[target]: ../glossary.md#term\n'
                  '`[A-Z][a-z]`\n```nix\n"[target](file.md)"\n```\n')
        manual = 'https://nix.dev/manual/nix/2.35/'
        first = update.render(source, source, 'language/example.md', manual)
        self.assertEqual(first, update.render(source, source, 'language/example.md', manual))
        self.assertIn('[other](' + manual + 'glossary.html#term)', first)
        self.assertIn('`[A-Z][a-z]`', first)
        self.assertIn('"[target](file.md)"', first)
        for bad in ['{{#include missing.md}}', '[bad](../../../escape.md)']:
            with self.assertRaises(ValueError):
                update.render(bad, bad, 'language/example.md', manual)

    def test_moved_or_missing_tags_fail(self):
        old = {'release': '2.35.2', 'revision': 'a' * 40}
        for available in [{}, {'2.35.2': 'b' * 40}]:
            with self.assertRaises(ValueError):
                update.resolve_release(old, available, '2.35.2')
        self.assertEqual(update.resolve_release(old, {'2.35.2': 'a' * 40}, '2.35.2'), 'a' * 40)

    def test_failed_publish_preserves_previous_package(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'nix-language'
            shutil.copytree(update.PACKAGE, package)
            files = {name: (package / name).read_bytes() for name in update.GENERATED}
            original = dict(files)
            files['references/language.md'] += b'changed\n'
            with self.assertRaises(ValueError):
                update.publish(files, package)
            self.assertEqual(original, {name: (package / name).read_bytes() for name in files})
            manifest = json.loads(files['sources.json'])
            manifest['outputs']['references/language.md'] = update.digest(files['references/language.md'])
            files['sources.json'] = update.encoded(manifest)
            replace = update.os.replace
            calls = 0

            def fail_second(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError('simulated replacement failure')
                return replace(source, target)

            with patch.object(update.os, 'replace', side_effect=fail_second):
                with self.assertRaises(OSError):
                    update.publish(files, package)
            self.assertEqual(original, {name: (package / name).read_bytes() for name in files})

    def test_external_html_anchor_entities(self):
        from io import BytesIO
        response = BytesIO(b'<dt id="builtins-foldl&#39;">')
        response.url = 'https://nix.dev/manual/nix/2.35/language/builtins.html'
        with patch.object(update, 'urlopen', return_value=response):
            update.check_external([response.url + "#builtins-foldl'"], 'https://nix.dev/manual/nix/2.35/')

    def test_automatic_update_cannot_change_selection(self):
        old = json.loads((update.PACKAGE / 'sources.json').read_text())
        new = json.loads(json.dumps(old))
        new['selection']['builtins'].append('not-reviewed')
        with patch.object(check, 'run', side_effect=['skills/nix-language/sources.json', json.dumps(old)]):
            with patch.object(check, 'validate', return_value=new):
                with self.assertRaises(ValueError):
                    check.boundary('trusted-commit')

    def test_report_surfaces_unselected_changes(self):
        new = {'release': '2.35.2', 'revision': 'a' * 40,
               'language_inputs': {'doc/manual/source/language/new.md': 'changed'},
               'selection': {'sections': []}, 'inputs': {'generated:language.json': 'changed'}}
        report = update.report({}, new)
        self.assertIn('outside selection', report)
        self.assertIn('new.md', report)


if __name__ == '__main__':
    unittest.main()
