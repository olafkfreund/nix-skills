# Project with nix-skills for its coding agents

This devenv setup links [nix-skills](https://olafkfreund.github.io/nix-skills/) into the project's agent skill
directories, so every contributor's agent gets the same skills in this repository, pinned by `devenv.lock`.

```sh
devenv shell
```

Entering the shell links each skill in `devenv.nix` into:

| Directory | Read by |
| --- | --- |
| `.claude/skills` | Claude Code, OpenCode |
| `.agents/skills` | Codex, Antigravity, OpenCode |

The links point into `/nix/store` and are git-ignored. Claude Code and Codex document support for linked skill
directories; for OpenCode and Antigravity, check that the agent lists the skills. If an agent does not follow
the links, set `files."<directory>/<skill>".copyMode = "copy";` in `devenv.nix` to copy that skill instead.

## Change the skills

Edit `nix-skills.skills` in `devenv.nix`, and add or remove the matching lines in `.gitignore`. The shell
prints a reminder for any link that is not ignored. devenv never replaces an existing file or directory at a
link's path; your own skills in these directories are left alone.

## Pin an agent

Uncomment the `llm-agents` input in `devenv.yaml` and the `packages` line in `devenv.nix`.

## Update

```sh
devenv update nix-skills
```

Review the `devenv.lock` change, then enter the shell again.
