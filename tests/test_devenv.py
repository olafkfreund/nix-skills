import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check
import devenv
import update


class DevenvTests(unittest.TestCase):
    def test_tabs_preserve_code_and_labels(self):
        source = ('<Tabs>\n  <TabItem label="Bash">\n    ```bash title=".bashrc"\n'
                  '    echo "${foo}"\n      echo "[x](/example/)"\n    ```\n'
                  '  </TabItem>\n  <TabItem label="Fish">\n    `devenv hook fish`\n'
                  '  </TabItem>\n</Tabs>\n')
        result = devenv.convert(source, 'auto-activation.mdx')
        self.assertIn('### Bash', result)
        self.assertIn('### Fish', result)
        self.assertIn('File: `.bashrc`', result)
        self.assertIn('```bash\necho "${foo}"\n  echo "[x](/example/)"\n```', result)
        self.assertEqual(devenv.convert('`[code](/path/)`', 'test.md'), '`[code](/path/)`\n')

    def test_version_scope_and_nested_warnings(self):
        source = ('---\ntitle: Page\n---\n<small class="added-in">Added in <code>1.2</code></small>\n'
                  '## Parent\n:::tip[New in version 2.1]\nContext\n:::\n'
                  '### Selected\n:::caution[Careful]\n:::note\nNested\n:::\n:::\n'
                  '## Other\n<VersionCompatibility version="9.0" />\n')
        result = devenv.convert(devenv.excerpt(source, 'Selected'), 'test.md')
        self.assertIn('Added in version 1.2', result)
        self.assertIn('New in version 2.1', result)
        self.assertIn('Context', result)
        self.assertIn('Warning: Careful', result)
        self.assertIn('End note.', result)
        self.assertNotIn('9.0', result)
        self.assertIn('Requires version 2.1', devenv.convert('<VersionCompatibility version="2.1" />', 'x'))

    def test_bad_sources_fail_closed(self):
        for source in ['<Unknown />', '<Tabs><TabItem label="x">', '</Tabs>',
                       'import X from "evil";', '{runCode()}', ':::unknown', '```nix\n{}',
                       '<VersionCompatibility mystery="2" />', ':::note\nunclosed', '[x](//host/)']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                devenv.convert(source, 'x.mdx')
        for source in ['---\ntitle: T\n---\n## Other\n',
                       '---\ntitle: T\n---\n## Chosen\n## Chosen\n']:
            with self.assertRaises(ValueError):
                devenv.excerpt(source, 'Chosen')

    def test_release_identity(self):
        self.assertEqual(devenv.version('v2.3'), '2.3.0')
        self.assertEqual(devenv.version('v2.3.1'), '2.3.1')
        with self.assertRaises(ValueError):
            devenv.version('v2.3-rc1')
        old = {'release': 'v2.3.1', 'revision': 'a' * 40}
        release = {'tag_name': 'v2.3.1', 'draft': False, 'prerelease': False}
        with patch.object(devenv, 'api', return_value=release):
            with patch.object(devenv, 'run', return_value='b' * 40 + '\trefs/tags/v2.3.1'):
                with self.assertRaises(ValueError):
                    devenv.resolve_release(old, 'v2.3.1')
            with patch.object(devenv, 'run', return_value='a' * 40 + '\trefs/tags/v2.3.1'):
                self.assertEqual(devenv.resolve_release(old, 'v2.3.1'), 'a' * 40)
                with patch.object(devenv, 'api', return_value=release | {'prerelease': True}):
                    with self.assertRaises(ValueError):
                        devenv.resolve_release(old, 'v2.3.1')

    def test_noop_does_not_build_or_publish(self):
        from argparse import Namespace
        old = json.loads((devenv.PACKAGE / 'sources.json').read_text())
        with patch.object(devenv, 'api', return_value={'tag_name': old['release']}), \
             patch.object(devenv, 'resolve_release', return_value=old['revision']), \
             patch.object(devenv, 'pinned_tools', side_effect=AssertionError('No-op built CLI')):
            devenv.main(Namespace(latest=True, release=None, check=False))

    def test_partial_replacement_restores_devenv(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'devenv-project'
            shutil.copytree(devenv.PACKAGE, package)
            original = {name: (package / name).read_bytes() for name in devenv.GENERATED}
            files = dict(original)
            files['LICENSE'] += b'\n'
            # Invalid staging must not replace any file.
            with self.assertRaises(ValueError):
                update.publish(files, package, skill='devenv-project')
            manifest = json.loads(files['sources.json'])
            manifest['outputs']['LICENSE'] = update.digest(files['LICENSE'])
            files['sources.json'] = update.encoded(manifest)
            replace = update.os.replace
            calls = 0
            def fail_second(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError('simulated')
                replace(source, target)
            with patch.object(update.os, 'replace', side_effect=fail_second), self.assertRaises(OSError):
                update.publish(files, package, skill='devenv-project')
            self.assertEqual(original, {name: (package / name).read_bytes() for name in original})

    def test_boundaries_and_reports(self):
        old = json.loads((devenv.PACKAGE / 'sources.json').read_text())
        changed = copy.deepcopy(old)
        changed['selection']['options'].append('unreviewed')
        with patch.object(check, 'run', side_effect=['skills/devenv-project/sources.json', json.dumps(old)]), \
             patch.object(check, 'validate', return_value=changed), self.assertRaises(ValueError):
            check.boundary('base', devenv.PACKAGE, skill='devenv-project')
        with patch.object(check, 'run', return_value='skills/nix-language/COPYING'), self.assertRaises(ValueError):
            check.boundary('base', devenv.PACKAGE, skill='devenv-project')
        changed['documentation_inputs']['new-page.md'] = '0' * 64
        report = devenv.report(old, changed)
        self.assertIn('new-page.md', report)
        self.assertIn('outside selection', report)

class ArtifactTests(unittest.TestCase):
    def test_artifact_roundtrip_and_rejections(self):
        import nixpkgs
        import wiki
        for skill, provider, reference, license_name in [
                ("devenv-project", devenv, "configuration", "LICENSE"),
                ("nixpkgs-development", nixpkgs, "packaging", "COPYING"),
                ("nixos-wiki", wiki, "index", "COPYING")]:
            with self.subTest(skill=skill):
                self.artifact_roundtrip(skill, provider, reference, license_name)

    def artifact_roundtrip(self, skill, provider, reference, license_name):
        import artifact
        import io
        import os
        import subprocess
        import tarfile
        def git(*args):
            return subprocess.check_output(['git', *args], text=True).strip()
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'skills' / skill
            shutil.copytree(provider.PACKAGE, package)
            shutil.copytree(update.PACKAGE, root / 'skills/nix-language')
            os.chdir(root)
            try:
                git('init', '-q')
                git('add', 'skills')
                git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'baseline')
                artifacts = root / 'artifact'
                with patch.object(artifact, 'ROOT', root):
                    artifact.pack(skill, artifacts)
                    self.assertFalse(artifact.accept(skill, artifacts))
                    if skill == 'nixos-wiki':
                        pages = json.loads((package / 'references/pages.json').read_text())
                        templates = json.loads((package / 'references/templates.json').read_text())
                        pages['NixOS']['revision_id'] += 1000000
                        files, _ = provider.generate(pages, templates, 'b'*64)
                        for name, data in files.items():
                            (package / name).write_bytes(data)
                    else:
                        manifest = json.loads((package / 'sources.json').read_text())
                        target = package / ('references/' + reference + '.md')
                        target.write_text(target.read_text() + '\nChanged upstream excerpt.\n')
                        manifest['outputs'][('references/' + reference + '.md')] = update.digest(target.read_bytes())
                        (package / 'sources.json').write_bytes(update.encoded(manifest))
                    (root / '.update-report.md').write_text('Changed selected source.\n')
                    artifact.pack(skill, artifacts)
                    git('restore', 'skills')
                    self.assertTrue(artifact.accept(skill, artifacts))
                    self.assertEqual(git('diff', '--name-only', '--', 'skills/nix-language'), '')
                    git('restore', 'skills')
                    metadata = json.loads((artifacts / 'metadata.json').read_text())
                    (artifacts / 'metadata.json').write_bytes(update.encoded(metadata | {'base': '0' * 40}))
                    with self.assertRaises(ValueError):
                        artifact.accept(skill, artifacts)
                    (artifacts / 'metadata.json').write_bytes(update.encoded(metadata))
                    valid_tar = (artifacts / 'references.tar').read_bytes()
                    for malicious in ['../escape', 'skills/nix-language/COPYING']:
                        with tarfile.open(artifacts / 'references.tar', 'w') as tar:
                            item = tarfile.TarInfo(malicious)
                            item.size = 1
                            tar.addfile(item, io.BytesIO(b'x'))
                        with self.assertRaises(ValueError):
                            artifact.accept(skill, artifacts)
                    if skill == 'nixpkgs-development':
                        with tarfile.open(fileobj=io.BytesIO(valid_tar)) as original, tarfile.open(artifacts / 'references.tar', 'w') as tar:
                            for member in original.getmembers():
                                data = original.extractfile(member).read()
                                if member.name.endswith('/sources.json'):
                                    changed = json.loads(data)
                                    changed['toolchain']['release'] = '2.35.3'
                                    data = update.encoded(changed)
                                    member.size = len(data)
                                tar.addfile(member, io.BytesIO(data))
                        with self.assertRaisesRegex(ValueError, 'immutable'):
                            artifact.accept(skill, artifacts)
                    (artifacts / 'references.tar').write_bytes(valid_tar)
                    with tarfile.open(fileobj=io.BytesIO(valid_tar)) as original, tarfile.open(artifacts / 'references.tar', 'w') as tar:
                        for member in original.getmembers():
                            if member.name.endswith('/' + license_name):
                                member.type = tarfile.SYMTYPE
                                member.linkname = '/etc/passwd'
                                member.size = 0
                                tar.addfile(member)
                            else:
                                tar.addfile(member, original.extractfile(member))
                    with self.assertRaises(ValueError):
                        artifact.accept(skill, artifacts)
                    self.assertEqual(git('diff', '--name-only'), '')
            finally:
                os.chdir(previous)

class GenerationTests(unittest.TestCase):
    def test_determinism_missing_inputs_and_pinned_declarations(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            names = ['languages.python.enable', 'languages.javascript.enable',
                     'languages.rust.enable', 'languages.go.enable', 'services.postgres.enable']
            selection = {
                'sections': [{'reference': ref, 'path': 'example.md', 'heading': 'Chosen'}
                             for ref in ['configuration', 'workflows', 'options']],
                'options': names, 'provenance': ['generator.nix']}
            old = {'selection': selection}
            inputs = {
                devenv.DOCS + 'example.md': '---\ntitle: Test\n---\n## Chosen\n```nix\n{ value = "${x}"; }\n```\n',
                'LICENSE': 'Apache License\n', 'generator.nix': '{}', devenv.SETUP: 'setup',
                'src/modules/test.nix': '{}'}
            records = {name: {'description': 'Enable this language.', 'type': 'boolean',
                             'default': {'_type': 'literalExpression', 'text': 'false'},
                             'example': {'_type': 'literalExpression', 'text': 'true'},
                             'declarations': [{'url': devenv.UPSTREAM + '/blob/main/src/modules/test.nix'}]}
                       for name in names}
            inputs['docs/src/data/options.json'] = json.dumps(records)
            for name, content in inputs.items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            files, manifest = devenv.generate(old, 'v2.3.1', 'a' * 40, source)
            self.assertEqual((files, manifest), devenv.generate(old, 'v2.3.1', 'a' * 40, source))
            self.assertIn(('/blob/' + 'a' * 40 + '/src/modules/test.nix').encode(), files['references/options.md'])
            self.assertIn(b'{ value = "${x}"; }', files['references/configuration.md'])
            (source / devenv.DOCS / 'example.md').write_text(inputs[devenv.DOCS + 'example.md'] + 'New content.\n')
            changed, new = devenv.generate(old, 'v2.3.2', 'b' * 40, source)
            self.assertNotEqual(files, changed)
            self.assertIn('example.md', devenv.report(manifest, new))
            records.pop(names[0])
            (source / 'docs/src/data/options.json').write_text(json.dumps(records))
            with self.assertRaises((ValueError, KeyError)):
                devenv.generate(old, 'v2.3.1', 'a' * 40, source)
            (source / devenv.DOCS / 'example.md').unlink()
            with self.assertRaises(FileNotFoundError):
                devenv.generate(old, 'v2.3.1', 'a' * 40, source)


if __name__ == '__main__':
    unittest.main()
