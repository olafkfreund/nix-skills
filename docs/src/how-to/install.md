# Install the skills

Every skill is a complete, self-contained folder. Install whole folders:
`SKILL.md` needs its `references/`, `sources.json` and licence file.

## Declaratively with Home Manager (recommended)

Add `inputs.nix-skills.url = "github:olafkfreund/nix-skills";` to your
flake, import `inputs.nix-skills.homeManagerModules.default` for your user,
and set `programs.nix-skills`:

```nix
programs.nix-skills = {
  enable = true;
  agents = [ "claude" "codex" ];
  # skills = [ "nix-language" "nixos-operations" ];  # omit for all skills
};
```

The module links each selected skill directory, read-only from the Nix
store, into each agent's skill directory. Existing files keep Home Manager's
normal collision protection. All options are listed in
[Home Manager module options](../reference/options.md).

When Home Manager is a NixOS module, rebuild with `nixos-rebuild`. Never run
`home-manager switch` in that setup.

## Agents and directories

| Agent | `agents` value | Skill directory | Call a skill |
| --- | --- | --- | --- |
| [Claude Code](https://code.claude.com/docs/en/skills) | `"claude"` | `~/.claude/skills` | `/nixos-coding-agents` |
| [Codex](https://learn.chatgpt.com/docs/build-skills) | `"codex"` | `~/.agents/skills` | `$nixos-coding-agents` |
| [OpenCode](https://opencode.ai/docs/skills) | `"opencode"` | `~/.config/opencode/skills` | Name the skill in your prompt |
| [Antigravity](https://www.antigravity.google/docs/migration/workflows-to-skills/) | `"antigravity"` | `~/.gemini/config/skills` | `/nixos-coding-agents` |

List the installed skills with `/skills` in Claude Code and Codex; in OpenCode
and Antigravity, ask the agent which skills it has.

All four also pick a skill automatically when a request matches its
description. Directories and syntax were checked against each agent's
documentation on 2026-09-23. OpenCode also reads `~/.claude/skills` and `~/.agents/skills`
and needs unique skill names: if you already selected `"claude"` or
`"codex"`, do not add `"opencode"`.

For one shared or custom location, set `directory` instead of `agents`, for
example `directory = ".agents/skills";`. Do not combine the two.

## Without Home Manager

The collection is also a data package. It exposes `share/nix-skills/<name>`
but creates no links:

```nix
environment.systemPackages = [
  inputs.nix-skills.packages.${pkgs.stdenv.hostPlatform.system}.nix-skills
];
```

Or clone a reviewed commit and link folders by hand:

```sh
git clone https://github.com/olafkfreund/nix-skills.git
cd nix-skills
git checkout --detach <reviewed-commit-sha>
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/nix-workflow" ~/.agents/skills/nix-workflow
```

Repeat the link for each skill you want, using your agent's directory from
the table. For an agent without native skill discovery, ask it to read the
chosen `SKILL.md` and its linked references before the task.

## Module and package details

Copy or link the **whole** desired skill directory into your agent's supported skill directory.
Keep `references/`, `sources.json`, and its license (`COPYING` for Nix/Nixpkgs/wiki, `LICENSE` for devenv/Home Manager/microvm.nix) with `SKILL.md`.
If your configuration manages agent files declaratively, declare that link or copy in your configuration instead.
No installation is performed by this repository's checks or update workflow.

For an agent without native skill discovery, explicitly ask it to read the chosen `SKILL.md` and the relevant linked references before the task.
Portability of the files does not imply native discovery has been tested in every agent.

This links complete immutable skill directories, including resources and
licenses, under the user's home. Existing files retain Home Manager's normal
collision protection; links are never forced. Disabling the module adds no
installation effects. Unknown or duplicate names and absolute/traversing
destinations are rejected. The module builds data with your existing `pkgs`;
it does not replace your host's Nixpkgs input or install an agent.

To install the complete collection for all supported agents, select their
native user skill directories:

```nix
programs.nix-skills = {
  enable = true;
  agents = [ "claude" "codex" "opencode" "antigravity" ];
};
```

The agent destinations are `.claude/skills`, `.agents/skills`,
`.config/opencode/skills`, and `.gemini/config/skills`, respectively. Set
`skills` alongside `agents` to install only a subset. The existing `directory`
option remains the compatibility path for one shared or custom destination;
do not combine a custom `directory` with `agents`. This installs skill bundles,
not the agents themselves or their plugin configuration.

Validate and rebuild through your existing **NixOS** workflow. Do not run
`home-manager switch` when Home Manager is a NixOS module. The default path and
symlink support follow [Codex's documented discovery locations](https://learn.chatgpt.com/docs/build-skills).
For another agent, select its documented relative directory; native discovery
in other agents is not claimed by package/module checks.

Without Home Manager, the collection is also a data package:

```nix
environment.systemPackages = [
  inputs.nix-skills.packages.${pkgs.stdenv.hostPlatform.system}.nix-skills
];
```

This exposes `share/nix-skills/<name>` in the package; it does not create user
discovery links. Declare those separately in your own configuration. Individual
outputs, for example `packages.x86_64-linux.nix-language`, contain the same
complete directory. `default` contains all registered skills. Packages are
exported for x86_64-linux and aarch64-linux; our validation distinguishes native
x86_64 builds from aarch64 evaluation.

Codex also reads a project's `.agents/skills/`, and symlinked skill directories are supported
([Codex skill discovery documentation](https://learn.chatgpt.com/docs/build-skills)).
Repository builds and checks never activate a home or host.
