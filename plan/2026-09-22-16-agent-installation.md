---
status: draft
issue: 16
spec: spec/2026-09-22-16-agent-installation.md
---

# Plan: Declarative installation for multiple coding agents

Implement the approved extension of the existing Home Manager module. Keep
`skills/<name>/` and the existing package outputs unchanged. Add an optional
`programs.nix-skills.agents` list with these mappings:

- `claude` → `.claude/skills`
- `codex` → `.agents/skills`
- `opencode` → `.config/opencode/skills`
- `antigravity` → `.gemini/config/skills`

The existing `directory` mode remains compatible. A non-default custom
directory cannot be combined with `agents`; Home Manager continues to create
non-forced links to the complete immutable skill directories.

## Steps

1. `nix/home-manager.nix`: add the supported-agent mapping, the typed
   `agents` option, duplicate/unknown-agent validation, and generated
   `home.file` entries for each selected agent and skill → verify with the
   disposable Home Manager checks.
2. `nix/checks.nix`: extend the module assertions for one agent, all agents,
   legacy custom-directory mode, duplicate/unknown agents, and conflicting
   `directory` plus `agents` settings → verify evaluation fails or succeeds as
   intended.
3. `README.md`: document the all-agent and single-agent configurations, native
   destinations, compatibility behavior, and the fact that this installs
   skill bundles only → verify links and examples match the module.
4. Run the repository validation and inspect the final diff → verify all
   required checks pass and no agent is activated or installed by tests.

## Tests

```sh
python3 scripts/check_collection.py
python3 -m unittest discover -s tests -p 'test_*.py'
nix flake check --no-update-lock-file
nix build .#nix-skills --no-link --no-update-lock-file
nix eval .#packages.aarch64-linux.nix-skills.drvPath --raw --no-update-lock-file
```

The Home Manager flake check must prove that each selected skill appears under
each selected agent path, that the legacy path remains unchanged, and that
invalid or ambiguous configurations fail evaluation.

## Rollback

Revert the implementation commit(s), or restore the previous `nix-skills`
flake input revision and rebuild the consumer's NixOS generation. Existing
users who do not set `agents` retain the previous module behavior.
