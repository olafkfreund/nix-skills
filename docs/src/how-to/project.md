# Add agents and skills to a project

Give one repository its own skills, pinned with the project, so every
contributor's agent gets the same skills there. Nothing is installed outside
the project directory, and no Home Manager or NixOS is needed: only Nix and
[devenv](https://devenv.sh/).

The project imports the `nix-skills/devenv` module. On `devenv shell` it
links whole skill folders (with their references and licences) into the
project's agent skill directories:

| Directory | Read by |
| --- | --- |
| `.claude/skills` | Claude Code, OpenCode |
| `.agents/skills` | Codex, Antigravity, OpenCode |

## A new project

```sh
mkdir my-project && cd my-project
nix flake init -t github:olafkfreund/nix-skills#project
devenv shell
```

The template adds `devenv.yaml`, `devenv.nix`, a `.gitignore` for the links
and a README. Start your agent in the project and check the skills with
`/skills`.

## An existing devenv project

Add the input and the import to `devenv.yaml`:

```yaml
inputs:
  nix-skills:
    url: github:olafkfreund/nix-skills
    flake: false
imports:
  - nix-skills/devenv
```

Choose skills in `devenv.nix`:

```nix
{
  nix-skills.skills = [ "nix-workflow" "nix-language" "devenv-project" ];
}
```

Add one `.gitignore` line per skill and directory, for example
`.claude/skills/nix-workflow` and `.agents/skills/nix-workflow`. The links
point into `/nix/store`; the shell prints a reminder for any link that is
not ignored.

## Options

| Option | Default | Effect |
| --- | --- | --- |
| `nix-skills.enable` | `true` | Link the skills |
| `nix-skills.skills` | `nix-workflow`, `nix-language`, `devenv-project` | Skills to link, by catalog name |
| `nix-skills.directories` | `.claude/skills`, `.agents/skills` | Where to link them |

Skill names are checked against the [skill catalog](../reference/catalog.md);
a typo fails with the list of valid names.

## Pin an agent in the project

Add the llm-agents.nix input to `devenv.yaml`:

```yaml
inputs:
  llm-agents:
    url: github:numtide/llm-agents.nix
```

and the agent to `devenv.nix`:

```nix
{ pkgs, inputs, ... }:
{
  packages = [ inputs.llm-agents.packages.${pkgs.stdenv.hostPlatform.system}.claude-code ];
}
```

## Agent support

Claude Code and Codex document support for linked skill directories.
OpenCode and Antigravity do not; check that the agent lists the skills. If
one does not follow the links, copy that skill instead:

```nix
{
  files.".agents/skills/nix-workflow".copyMode = "copy";
}
```

## Update

```sh
devenv update nix-skills
```

Review the `devenv.lock` change, then enter the shell again. Removed skills'
links are cleaned up automatically.

## What the module never does

- It writes nothing outside the listed project directories and devenv's own
  state.
- It never replaces an existing file or directory at a link's path: devenv
  only warns, so a project's own skills are left alone.
- It installs no agent unless you add one as above.
