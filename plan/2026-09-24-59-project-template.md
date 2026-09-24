---
status: draft
issue: 59
spec: spec/2026-09-24-59-project-template.md
---

# Plan: agents and skills for a single project

## Approved decisions

These come from the approved spec. The plan can be followed without opening
the intent or spec.

**Verified facts** (devenv 2.3.1, 2026-09-24):
- `files."<dir>/<skill>".source = <skill folder>` symlinks a whole folder
  into the project on shell entry, with no `devenv allow` needed;
- an existing file or directory at that path is left alone (devenv only
  warns);
- a module imported as `imports: [ nix-skills/devenv ]` resolves
  `../skills/<name>` relative to itself.

**Module: `devenv/devenv.nix`** (new; the root `devenv.nix` and
`devenv.yaml` are unrelated and unchanged).
- Signature `{ config, lib, ... }:`.
- **Options** under `nix-skills`:
  - `enable`, a bool, default `true`;
  - `skills`, a list of `types.enum` over the names in `../skills.json`,
    default `[ "nix-workflow" "nix-language" "devenv-project" ]`;
  - `directories`, a list of strings, default
    `[ ".claude/skills" ".agents/skills" ]`.
- **When enabled:**
  - `files."${dir}/${skill}".source = ../skills + "/${skill}";` for every
    pair;
  - `enterShell` appends a POSIX snippet. Inside a Git work tree, for each
    managed path, `git check-ignore -q "$path"` or print
    `nix-skills: add <path> to .gitignore (it links into /nix/store)`.
    It never exits non-zero.

**Template: `templates/project/`.**
- **`devenv.yaml`:**

  ```yaml
  inputs:
    nixpkgs:
      url: github:cachix/devenv-nixpkgs/rolling
    nix-skills:
      url: github:olafkfreund/nix-skills
      flake: false
    # llm-agents:
    #   url: github:numtide/llm-agents.nix
  imports:
    - nix-skills/devenv
  ```

- **`devenv.nix`:**
  - `{ pkgs, inputs, ... }:`;
  - `nix-skills.skills` with the three defaults, and a comment listing all
    ten names and the catalog URL;
  - a commented `packages = [ inputs.llm-agents.packages.${pkgs.stdenv.hostPlatform.system}.claude-code ];`;
  - a commented `languages.python.enable = true;` placeholder.
- **`.gitignore`:** `.claude/skills/{nix-workflow,nix-language,devenv-project}`
  and `.agents/skills/{…}`, written as six explicit lines, plus `.devenv*`,
  `devenv.local.nix` and `.direnv`.
- **`README.md`:**
  - what it does;
  - adding or removing a skill: edit the list and `.gitignore`;
  - adding an agent;
  - the per-agent directories and the symlink note;
  - the `copyMode = "copy"` escape hatch for agents that don't follow
    links, using devenv's `files."<path>".copyMode`;
  - updating with `devenv update nix-skills`.
- **Main flake:** `templates.project = { path = ./templates/project;
  description = "Project with nix-skills linked for its coding agents
  (devenv)"; welcomeText = …; }`, with no new inputs. `welcomeText`
  covers: run `devenv shell`, check with `/skills`, and edit the list in
  `devenv.nix`.

**Offline check (`nix/checks.nix`):**
- evaluate `lib.evalModules { modules = [ stub ../devenv/devenv.nix … ]; }`,
  where `stub` declares
  `options.files = attrsOf (submodule { options.source = mkOption { }; })`
  and `options.enterShell = lines`;
- assert that the default configuration has exactly these six `files`
  keys:

  ```text
  .claude/skills/nix-workflow
  .claude/skills/nix-language
  .claude/skills/devenv-project
  .agents/skills/nix-workflow
  .agents/skills/nix-language
  .agents/skills/devenv-project
  ```

  and that each source's base name is the skill name;
- assert that `skills = [ "not-a-skill" ]` fails
  (`builtins.tryEval … .success == false`).

The check is exposed as `checks.<system>.devenv-module`, a `runCommand`
that exists only if the assertions hold, so it runs in `nix flake check`
and the required `distribution` job.

**End-to-end CI:** a new job `project-template` in `demo.yml`.
- The path filters gain `devenv/**` and `templates/**` (already present).
- **Steps:**
  1. checkout;
  2. install Nix (pinned action);
  3. `tmp=$(mktemp -d)`, then
     `cd "$tmp" && nix flake init -t "$GITHUB_WORKSPACE#project"`;
  4. `sed -i "s|url: github:olafkfreund/nix-skills|url: path:$GITHUB_WORKSPACE|" devenv.yaml`;
  5. `git init -q && git add -A`;
  6. `nix run nixpkgs#devenv -- shell -- sh -c '<checks>'`, where the
     checks are: `test -f` on `SKILL.md` through each of the six links;
     `git check-ignore -q` on each of the six; and no `nix-skills: add`
     reminder in the shell output.
- It is not a required check.

**Documentation.**
- **`docs/src/how-to/project.md`** ("Add agents and skills to a project"),
  in `SUMMARY.md` after "Set up your own machine". It covers new and
  existing projects, the options table, the per-agent directories and the
  symlink note, the `copyMode` escape hatch, updating, and what the module
  never does.
- **AGENTS.md:** a `devenv/` line, and `templates/` mentioning both
  templates.
- **CONTRIBUTING.md:** one line saying `demo.yml` also checks the project
  template.

## Steps

1. **`devenv/devenv.nix` and the offline check in `nix/checks.nix`.**
   → Verify: `nix flake check` passes, and a temporary unknown default
   makes it fail. Revert it.
2. **`templates/project/`, and the `templates.project` output.**
   → Verify: `nix flake check` validates the templates, and
   `nix flake init -t .#project` into a scratch directory prints the
   welcome text.
3. **Local end-to-end run,** in the scratch directory, pointed at the
   checkout.
   → Verify:
   - `devenv shell` creates the six links, and `SKILL.md` is readable
     through each;
   - after `git init`, `git check-ignore` covers all six and no reminder
     prints;
   - adding `nix-skills.skills = [ … "home-manager" ]` without ignoring it
     prints exactly the two reminders, and the shell still starts;
   - delete the scratch directory afterwards.
4. **The `demo.yml` job.**
   → Verify: `actionlint` is clean.
5. **Documentation:** the page, `SUMMARY.md`, AGENTS.md and
   CONTRIBUTING.md.
   → Verify: `nix build .#docs` (links, style, table limits) and
   `check_collection.py` pass.
6. **Full checks:** unit tests, `check-fast`, `nix flake check` and
   `actionlint`. Commit in logical groups, push, and open a PR with
   `Closes #59`.
   → Verify: CI is green, including the new job, and the PR is `CLEAN`.
   Do not merge without approval.

## Tests

```sh
nix flake check
d=$(mktemp -d); (cd "$d" && nix flake init -t "$OLDPWD#project")
# local end-to-end: edit devenv.yaml to path:<repo>, git init, devenv shell -- <checks>
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_collection.py
devenv shell check-fast
nix build .#docs
actionlint
```

## Rollback

- **Before merge:** close the PR and delete the branch.
- **After merge:** `git revert` the commits. That removes `devenv/`, the
  template, the check, the CI job and the page. Projects that already
  import `nix-skills/devenv` keep working at their locked revision until
  they update.
