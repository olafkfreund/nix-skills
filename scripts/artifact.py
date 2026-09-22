"""Package and accept only one skill's generated files across CI permission boundaries."""

import argparse
import json
from pathlib import Path
import tarfile

from check import boundary, immutable_policy
from update import ROOT, encoded, generated_files, run


def pack(skill, directory):
    package = ROOT / 'skills' / skill
    base = run('git', 'rev-parse', 'HEAD')
    boundary(base, package, skill=skill)
    changed = bool(run('git', 'diff', '--name-only', base))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'metadata.json').write_bytes(encoded({'base': base, 'skill': skill, 'changed': changed}))
    report = ROOT / '.update-report.md'
    (directory / 'report.md').write_text(report.read_text() if changed else 'No upstream change.\n')
    with tarfile.open(directory / 'references.tar', 'w') as tar:
        for name in sorted(generated_files(skill)):
            tar.add(package / name, arcname=f'skills/{skill}/{name}', recursive=False)


def accept(skill, directory):
    for name, limit in [('metadata.json', 4096), ('report.md', 1_000_000), ('references.tar', 12_000_000)]:
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
            raise ValueError('Unsupported artifact: ' + name)
    metadata = json.loads((directory / 'metadata.json').read_text())
    if metadata['skill'] != skill or metadata['base'] != run('git', 'rev-parse', 'HEAD'):
        raise ValueError('Artifact skill/base mismatch')
    if type(metadata['changed']) is not bool:
        raise ValueError('Invalid change flag')
    expected = {f'skills/{skill}/{name}' for name in generated_files(skill)}
    with tarfile.open(directory / 'references.tar') as tar:
        members = tar.getmembers()
        if len(members) != len(expected) or {m.name for m in members} != expected:
            raise ValueError('Unexpected artifact file list')
        if any(not m.isfile() or m.size > 2_000_000 for m in members):
            raise ValueError('Unsupported artifact entry')
        files = {m.name: tar.extractfile(m).read() for m in members}
    # Validate the whole package and immutable selection before any working-tree writes.
    import tempfile
    import shutil
    from check import validate
    package = ROOT / 'skills' / skill
    old = validate(package, skill=skill)
    with tempfile.TemporaryDirectory() as temporary:
        staged = Path(temporary) / 'skill'
        shutil.copytree(package, staged)
        prefix = f'skills/{skill}/'
        for name, content in files.items():
            (staged / name.removeprefix(prefix)).write_bytes(content)
        new = validate(staged, skill=skill)
        immutable_policy(old, new, skill)
    differs = any((ROOT / name).read_bytes() != content for name, content in files.items())
    if differs != metadata['changed']:
        raise ValueError('Artifact change flag disagrees with contents')
    if differs:
        from update import publish
        publish({name.removeprefix(prefix): data for name, data in files.items()}, package, skill=skill)
    boundary(metadata['base'], package, skill=skill)
    return differs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['pack', 'accept'])
    parser.add_argument('--skill', choices=['nix-language', 'devenv-project', 'nixpkgs-development', 'nixos-wiki'], required=True)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    if args.mode == 'pack':
        pack(args.skill, args.directory)
    else:
        print('changed=' + str(accept(args.skill, args.directory)).lower())
