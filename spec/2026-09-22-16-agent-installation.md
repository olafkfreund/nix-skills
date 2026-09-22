---
status: approved
issue: 16
intent: intent/2026-09-22-16-agent-installation.md
---

# Spec: Declarative installation for multiple coding agents

## Design

Extend the existing `programs.nix-skills` Home Manager module rather than
adding a separate installer or duplicating skill packages. Keep the current
`directory` option unchanged for compatibility, and add an `agents` option
whose values are explicit supported agent names:

```nix
programs.nix-skills = {
  enable = true;
  skills = [ "home-manager" "microvm-nix" ];
  agents = [ "claude" "codex" "opencode" "antigravity" ];
};
```

The module maps user-level agent names to their documented native discovery
directories:

| Agent | Home-relative destination |
| --- | --- |
| `claude` | `.claude/skills` |
| `codex` | `.agents/skills` |
| `opencode` | `.config/opencode/skills` |
| `antigravity` | `.gemini/config/skills` |

Each selected skill is emitted as a normal `home.file` entry in every selected
destination. Home Manager therefore retains collision protection, while every
agent receives the same complete package from the existing Nix package output.
The existing `directory` mode remains the compatibility path for shared or
custom discovery directories; `agents` is an additional mode and cannot be
combined with a non-default `directory`.

The module will validate duplicate agent names, reject unknown agents, and
continue validating skill names and destinations. The package outputs remain
unchanged: `default`, `nix-skills`, and per-skill outputs still expose complete
portable directories.

Documentation will show one configuration for all four agents and explain that
the repository installs skill bundles, not agent binaries or configuration.
Project-local installation and native plugin bundles are not part of this
change. They can be added later as separate exporters if an agent requires
plugin-only capabilities beyond `SKILL.md` discovery.

References:

- [Claude Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [OpenCode Skills](https://opencode.ai/v2/docs/skills)
- [Antigravity skills migration](https://www.antigravity.google/docs/migration/workflows-to-skills/)

## Alternatives rejected

- **A universal plugin format:** Claude, OpenCode, and Antigravity do not share
  one plugin manifest or lifecycle. It would duplicate metadata and create a
  new abstraction without improving basic skill discovery.
- **A new standalone installer CLI:** The repository already exports a Nix
  package and Home Manager module, and the user manages the system
  declaratively. A second imperative installer would bypass that workflow.
- **Four copies of every skill:** This would increase storage and drift risk;
  one Nix source package can safely populate multiple Home Manager links.
- **Replacing `directory`:** Existing consumers would need unnecessary
  migration. The new agent selector can coexist with the current custom/shared
  destination mode.

## Risks

- Agent discovery paths can change upstream; keep the mapping centralized and
  document the versions/URLs used for verification.
- Installing all four destinations increases the number of Home Manager file
  entries, though each remains a link to the same immutable source.
- Users may select both `agents` and a custom `directory`; an assertion must
  reject that ambiguous configuration.

## Verification

- Extend the Nix Home Manager check with one selected-agent configuration and an
  all-agent configuration.
- Assert that every selected agent produces every selected skill at the mapped
  path and that the legacy `directory` mode remains unchanged.
- Assert failures for unknown/duplicate agents and conflicting options.
- Run `python3 scripts/check_collection.py`, the Python unit tests,
  `nix flake check --no-update-lock-file`, and the package build.
- Review the generated Home Manager file map; do not activate a user home or
  install an agent during validation.
