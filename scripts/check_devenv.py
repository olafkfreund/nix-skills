"""Exercise only a disposable, pinned project; never grant directory trust."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from update import ROOT


def runtime_check(source, cli, revision):
    fixture = ROOT / 'tests/devenv'
    recorded = json.loads((fixture / 'devenv.lock').read_text())
    original_revision = recorded['nodes']['devenv']['locked']['rev']
    options = json.loads((source / 'docs/src/data/options.json').read_text())
    defaults = ['languages.python.enable', 'languages.python.venv.enable',
                'languages.javascript.enable', 'languages.javascript.npm.enable',
                'languages.rust.enable', 'languages.go.enable', 'services.postgres.enable']
    with tempfile.TemporaryDirectory(prefix='nix-skills-devenv-') as directory:
        root = Path(directory)
        project = root / 'project'
        shutil.copytree(fixture, project)
        yaml = project / 'devenv.yaml'
        yaml.write_text(yaml.read_text().replace(original_revision, revision))
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(('DEVENV_', 'DIRENV_', 'NIX_PATH'))}
        for key in ['XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_CACHE_HOME', 'XDG_RUNTIME_DIR']:
            target = root / key.lower()
            target.mkdir(mode=0o700)
            env[key] = str(target)
        user_config = root / 'config.yaml'
        user_config.write_text('version: 1\n')
        def command(*args):
            result = subprocess.run([str(cli), '--user-config', str(user_config), '--no-tui',
                                     '--no-eval-cache', *args], cwd=project, env=env,
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode:
                raise RuntimeError('devenv ' + ' '.join(args) + '\n' + result.stdout + result.stderr)
            return result.stdout
        # Update only the candidate module input; compare every auxiliary pin below.
        if revision != original_revision:
            command('update', 'devenv')
        evaluated = json.loads(command('eval', 'env.SKILL_TEST', *defaults))
        if evaluated['env.SKILL_TEST'] != 'devenv-skill-ok':
            raise ValueError('Fixture environment value mismatch')
        for name in defaults:
            expected = options[name]['default']
            if expected != {'_type': 'literalExpression', 'text': 'false'} or evaluated[name] is not False:
                raise ValueError('Option data and module default disagree: ' + name)
        # Evaluate enabled language/service configuration without building or starting it.
        flags = []
        for name in ['languages.python.enable', 'languages.javascript.enable',
                     'languages.rust.enable', 'languages.go.enable', 'services.postgres.enable']:
            flags += ['--option', name + ':bool', 'true']
        enabled = json.loads(command(*flags, 'eval', *defaults))
        if any(enabled[flags[i].removesuffix(':bool')] is not True for i in range(1, len(flags), 3)):
            raise ValueError('Language/service enablement failed')
        if command('shell', '--', 'skill-check').strip() != 'devenv-skill-ok':
            raise ValueError('Shell/script output mismatch')
        command('tasks', 'run', 'skill:check')
        if (project / 'task-result').read_text() != 'task-ok':
            raise ValueError('Task did not complete')
        command('test')
        if (project / 'test-result').read_text() != 'test-ok':
            raise ValueError('enterTest did not complete')
        locked = json.loads((project / 'devenv.lock').read_text())
        if locked['nodes']['devenv']['locked']['rev'] != revision:
            raise ValueError('Fixture modules differ from CLI source')
        for name in recorded['nodes'].keys() | locked['nodes'].keys():
            if name != 'devenv' and recorded['nodes'].get(name) != locked['nodes'].get(name):
                raise ValueError('Unrelated fixture input changed: ' + name)
        if locked['nodes']['devenv']['locked'].get('dir') != 'src/modules':
            raise ValueError('Fixture does not use the devenv module flake')
    print('Pinned devenv defaults, language/service evaluation, shell, task, and enterTest passed')
