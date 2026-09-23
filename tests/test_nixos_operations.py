import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import nixos_operations

M = 'nixos/doc/manual/'
TOOLCHAIN = dict(upstream='https://github.com/NixOS/nix', revision='b' * 40, release='2.34.8')
FILES = {
    '.version': '26.11\n', 'COPYING': 'MIT\n',
    'doc/manpage-urls.json': json.dumps({'systemd.special(7)': 'https://example.org/systemd.special.html'}),
    'doc/other.md': '# Other {#sec-other}\ntext\n',
    M + 'config.chapter.md': '# Configuration {#ch-configuration}\nchapter\n',
    M + 'gc.chapter.md': '# Cleaning {#sec-nix-gc}\nClean.\n',
    M + 'ops.chapter.md': ('# Operations {#sec-ops}\n'
                           'See [config](#ch-configuration), [gc](#sec-nix-gc), [local](#sect-local),\n'
                           '[units](#opt-systemd.packages) and {manpage}`systemd.special(7)`.\n\n'
                           '::: {.warning}\nRun as root.\n:::\n\n'
                           '## Local {#sect-local}\n```\n[raw](#opt-left.alone)\n```\n'),
    'nixos/modules/system/boot/systemd.nix': '{ }\n',
}
DECLARATIONS = {'systemd.packages': ['nixos/modules/system/boot/systemd.nix']}


def section(path, anchor, heading, **extra):
    return dict(path=M + path, anchor=anchor, heading=heading, children=True) | extra


class NixosOperationsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.source = Path(self.directory.name)
        for name, content in FILES.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.sections = [section('ops.chapter.md', 'sec-ops', 'Operations',
                                 option_links={'opt-systemd.packages': 'systemd.packages'}),
                         section('gc.chapter.md', 'sec-nix-gc', 'Cleaning')]

    def tearDown(self):
        self.directory.cleanup()

    def generate(self, sections=None, declarations=DECLARATIONS):
        old = dict(toolchain=TOOLCHAIN, selection=dict(sections=sections or self.sections))
        return nixos_operations.generate(old, 'a' * 40, self.source, declarations)

    def test_selection_links_and_manifest(self):
        files, manifest = self.generate()
        out = files['references/operations.md'].decode()
        blob = f'{nixos_operations.UPSTREAM}/blob/{"a" * 40}/'
        self.assertIn('- [Operations](#sec-ops)', out)
        self.assertIn('[gc](operations.md#sec-nix-gc)', out)                 # bundled chapter
        self.assertIn('[local](operations.md#sect-local)', out)              # same-file child section
        self.assertIn(f'[config]({blob}{M}config.chapter.md) (source section: Configuration)', out)
        self.assertIn(f'[units]({blob}nixos/modules/system/boot/systemd.nix) (source section: systemd.packages)', out)
        self.assertIn('[`systemd.special(7)`](https://example.org/systemd.special.html)', out)
        self.assertIn('**Warning**', out)
        self.assertIn('[raw](#opt-left.alone)', out)                         # fenced code untouched
        self.assertIn('nixos/modules/system/boot/systemd.nix', manifest['inputs'])
        nixos_operations.validate_manifest(manifest)
        self.assertEqual(files, self.generate()[0])                          # deterministic

    def test_option_link_failures(self):
        ops = self.sections[0]
        for sections, declarations, error in [
                ([ops | {'option_links': {}}, self.sections[1]], DECLARATIONS, 'Unmapped option link'),
                (self.sections, {}, 'no in-tree declaration'),
                ([ops | {'option_links': ops['option_links'] | {'opt-unused': 'systemd.packages'}}, self.sections[1]],
                 DECLARATIONS, 'Unused option link mapping'),
                ([ops | {'option_links': {'opt-systemd.packages': 'systemd.packages', 'sec-nix-gc': 'systemd.packages'}},
                  self.sections[1]], DECLARATIONS, 'collides')]:
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                self.generate(sections, declarations)
        with self.assertRaisesRegex(ValueError, 'Missing or ambiguous section'):
            self.generate([section('ops.chapter.md', 'sec-missing', 'Operations')])

    def test_manifest_schema(self):
        _, manifest = self.generate()
        for mutate in [lambda s: s.update(path='doc/other.md'), lambda s: s.update(children='yes'),
                       lambda s: s.update(anchor='bad anchor'), lambda s: s.update(extra=True),
                       lambda s: s.update(option_links={'sec-ops': 'x'}), lambda s: s.update(option_links={'opt-x': ''}),
                       lambda s: s.update(anchor='sec-nix-gc')]:
            broken = copy.deepcopy(manifest)
            mutate(broken['selection']['sections'][0])
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                nixos_operations.validate_manifest(broken)
        for field, value in [('branch', 'release-26.05'), ('toolchain', TOOLCHAIN | {'upstream': 'x'})]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                nixos_operations.validate_manifest(manifest | {field: value})
        broken = copy.deepcopy(manifest)
        broken['inputs']['../escape'] = 'a' * 64
        with self.assertRaises(ValueError):
            nixos_operations.validate_manifest(broken)


if __name__ == '__main__':
    unittest.main()
