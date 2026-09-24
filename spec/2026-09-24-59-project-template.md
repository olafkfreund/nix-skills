---
status: draft
issue: 59
intent: intent/2026-09-24-59-project-template.md
---

# Spec: agents and skills for a single project

## Facts

Checked on 2026-09-24, with devenv 2.3.1, in scratch projects outside the
repository (deleted afterwards).

- **(a) devenv links whole directories.**
  `files.".claude/skills/nix-workflow".source = "${inputs.nix-skills}/skills/nix-workflow";`
  created `.claude/skills/nix-workflow -> /nix/store/…/skills/nix-workflow`
  on shell entry (task `devenv:files`). `SKILL.md` and `references/` were
  readable through the link, and no `devenv allow` was needed.
- **(b) devenv never overwrites.** From
  [`src/modules/files.nix`](https://github.com/cachix/devenv/blob/main/src/modules/files.nix):
  - an existing real file prints "Conflicting file …";
  - an existing directory prints "Conflicting non-file …";
  - neither is touched. Only devenv's own links into `/nix/store` are
    updated;
  - links dropped from the configuration are cleaned up (`devenv:files:cleanup`).
- **(c) Imported modules can use relative paths.** With
  `inputs.nix-skills` (`flake: false`) and `imports: [ nix-skills/devenv ]`,
  devenv loads `<input>/devenv/devenv.nix`. A path relative to that file,
  `../skills/nix-language`, became a store path and was linked into the
  project (`.agents/skills/nix-language -> /nix/store/…-nix-language`).
- **Project skill directories.** Claude Code reads `.claude/skills`, Codex
  and Antigravity read `.agents/skills`, and OpenCode reads both. Symlinked
  skill directories are documented as supported only for Claude Code and
  Codex.
- **devenv's `claude.code.skills`** takes inline text only, so it cannot
  install skill folders.

## Design

### Default answers to the intent's open questions

The intent was approved without answers. These defaults apply unless the spec
review changes them:

1. **devenv only.** A plain-flake variant can follow if requested.
2. **Default skills:** `nix-workflow`, `nix-language` and `devenv-project`,
   as a list the project edits.
3. **The agent in the project shell is opt-in.** The template shows it,
   commented out.
4. **Both** a reusable devenv module and a `nix flake init` template that
   uses it.

### Reusable module: `devenv/devenv.nix` in this repository

It is imported by projects as `imports: [ nix-skills/devenv ]`, with an
input named `nix-skills` (`url: github:olafkfreund/nix-skills`,
`flake: false`).

**Options,** under `nix-skills`:

| Option | Default | Effect |
| --- | --- | --- |
| `enable` | `true` once imported | Links the skills |
| `skills` | `[ "nix-workflow" "nix-language" "devenv-project" ]` | Skill folders to link; each must be a name in `skills.json` |
| `directories` | `[ ".claude/skills" ".agents/skills" ]` | Project directories to link into; the default covers Claude Code, Codex, Antigravity and OpenCode |

**Behaviour:**
- For each skill and each directory, it sets
  `files."<directory>/<skill>".source = ../skills/<skill>;`, the whole
  folder, relative to the module and so resolved from the input.
- **Skill names are checked** against `../skills.json`, read by the
  module, so a typo fails evaluation with the list of valid names.
- **Ignore reminder:** an `enterShell` line runs `git check-ignore -q` for
  each managed link, and prints a one-line reminder for any that is not
  ignored. It never fails the shell, and it is quiet outside a Git
  repository.
- **Nothing else:** it doesn't touch agents, packages, languages or files
  outside the listed paths. Conflicting existing files are left alone,
  because devenv only warns.

The repository's own development environment (`devenv.nix` and
`devenv.yaml` at the root) is unrelated and unchanged. Only the new
`devenv/` directory is imported by projects.

### Template: `templates/project/` → main flake `templates.project`

- **`devenv.yaml`:**
  - `nixpkgs` from `github:cachix/devenv-nixpkgs/rolling`;
  - `nix-skills` from `github:olafkfreund/nix-skills`, with `flake: false`;
  - commented: `llm-agents` from `github:numtide/llm-agents.nix`;
  - `imports: [ nix-skills/devenv ]`.
- **`devenv.nix`:**
  - `nix-skills.skills = [ … ];` with a comment listing all skill names and
    linking the catalog;
  - a commented example that adds an agent to the project shell from
    llm-agents.nix: `packages = [ inputs.llm-agents.packages.${pkgs.stdenv.hostPlatform.system}.claude-code ];`;
  - a placeholder for the project's own languages.
- **`.gitignore`:** the six default links (three skills in two
  directories), plus `.devenv*` and `devenv.local.nix`.
- **`README.md`:** what the template does, how to add or remove a skill
  (edit the list and the `.gitignore`), how to add an agent, and the note on
  agent support.
- **Main flake:** `templates.project = { path = ./templates/project;
  description; welcomeText; }`. `welcomeText` gives the next steps. There
  are no new inputs.

### Documentation: `docs/src/how-to/project.md`, "Add agents and skills to a project"

It is listed in `SUMMARY.md` after "Set up your own machine". It covers:
- a new project, with `nix flake init -t github:olafkfreund/nix-skills#project`;
- an existing devenv project: the two `devenv.yaml` additions and the
  `.gitignore` lines;
- the options table;
- the per-agent note: which directory each agent reads, and that symlink
  discovery is documented for Claude Code and Codex only, so check with
  `/skills` or by asking the agent;
- updating: `devenv update nix-skills`, or the whole lock;
- what the module never does.

AGENTS.md gains a `devenv/` line and a `templates/project` mention.

### Tests

- **Offline evaluation,** in the main flake's `nix/checks.nix`: evaluate
  `devenv/devenv.nix` with a minimal stub of devenv's `files` option. Check
  that:
  - the default configuration produces the six `files` keys, with sources
    ending in `/skills/<name>`;
  - an unknown skill name fails evaluation.

  This runs in the required `distribution` job, so the module can't break
  unnoticed.
- **End to end in CI,** a new job in `demo.yml` (non-blocking, with the
  path filter gaining `devenv/**` and `templates/project/**`):
  1. `nix flake init -t "$GITHUB_WORKSPACE#project"` in a temporary
     directory;
  2. point the `nix-skills` input at the checkout (`path:$GITHUB_WORKSPACE`);
  3. run `nix run nixpkgs#devenv -- shell -- test -f
     .claude/skills/nix-workflow/SKILL.md`, and the same for
     `.agents/skills`;
  4. `git init` and check that `git check-ignore` covers the six links.

## Alternatives rejected

- **devenv's `claude.code.skills`.** It is inline text only, and Claude
  Code only.
- **A plain-flake `shellHook` that runs `ln -s`.** It is imperative and
  has no cleanup. devenv's `files` already has conflict handling and
  cleanup.
- **Ignoring the whole `.claude/skills/` directory in the template.** That
  would hide a project's own committed skills. Per-link entries plus the
  shell reminder are safer.
- **All ten skills by default.** It clutters every project. A short list
  that the project edits is clearer.
- **Pinning an agent by default.** Contributors choose their own agent. A
  project that wants one uncomments one line.
- **A `copy` or `seed` mode instead of symlinks.** Copies go stale on
  update and invite local edits. Symlinks always match the lock.

## Risks

- **An agent doesn't follow symlinked skill directories** (OpenCode and
  Antigravity are undocumented). The docs say so. The `copyMode = "copy"`
  escape hatch is documented as a manual override for affected users.
- **A forgotten `.gitignore` entry** after adding a skill means the link is
  committed. Mitigated by the shell reminder and the docs. A committed link
  is harmless but noisy.
- **devenv option changes upstream.** `files.<name>.source` is tested end
  to end in CI with current devenv from nixpkgs.
- **`flake: false` input fetching** differs between devenv versions.
  Covered by the end-to-end job.

## Verification

- **Module evaluation check,** locally: `nix flake check` passes, including
  the new six-key and unknown-skill checks.
- **End to end, locally,** as in the CI job:
  1. initialise the template in a scratch directory;
  2. point it at the checkout;
  3. enter the shell once: the six links exist, `SKILL.md` is readable
     through each, and `git check-ignore` covers them;
  4. add a seventh skill without ignoring it: the shell prints one reminder
     and still starts.
- `nix build .#docs` passes with the new page. `check_collection.py`,
  `check-fast` and `actionlint` pass.
- **CI:** the new `demo.yml` job passes on the pull request.
