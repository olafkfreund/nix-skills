---
status: draft
issue: 59
author: olafkfreund
---

# Intent: agents and skills for a single project

## Problem

Every way of getting these skills today works for a **user** or a
**machine**:

- the Home Manager module installs them into the user's home (#16);
- `nixosModules.agentic` installs agents and skills for one user on a
  machine (#58);
- the demo VM is a whole throwaway system (#57).

Nothing works for a **project**, the unit people actually collaborate on:

- **Teams can't share a setup.** A repository cannot say "work on this
  project with these skills and this agent". Each contributor must
  configure their own home or machine, and gets whatever versions they
  happened to install.
- **The skills can't follow the project's pins.** A project that pins its
  own tools with devenv, or a project flake, has no way to pin the skills
  and the agent next to them, or to update them with the project's other
  dependencies.
- **Non-NixOS and non-Home-Manager users are left out.** Someone on another
  Linux distribution or on macOS with Nix and devenv, but no Home Manager
  or NixOS, has only the manual `ln -s` route.
- **The obvious devenv feature doesn't fit.** devenv's Claude Code
  integration has `claude.code.skills`, but it takes a skill's text inline
  (`description`, `content`, …). It cannot install these skills, which are
  whole folders with `references/`, `sources.json` and licence files. It
  also covers Claude Code only.

What makes a project-level answer possible:
- **Agents read project skill directories.** Claude Code reads
  `.claude/skills`, and Codex and Antigravity read `.agents/skills` in the
  workspace. OpenCode reads both.
- **devenv has a general `files` option** that places a file from the Nix
  store into the project, by default as a symlink, so skill folders could
  be linked into those directories.

## Proposed outcome

- **A project gets the skills from its own configuration.** Its devenv
  setup, committed with the project, links the chosen skills into the
  project's agent skill directories, so every contributor's agent sees the
  same skills when working in that repository.
- **Optionally, the agent too.** The same configuration can put a chosen
  agent from llm-agents.nix on the project shell's `PATH`, pinned with the
  project.
- **Easy to start:** a template (for example
  `nix flake init -t github:olafkfreund/nix-skills#project`, or a devenv
  equivalent) creates the files. Existing devenv projects can add a few
  lines instead.
- **Updated with the project.** Updating the project's lock updates the
  skills. Nothing is installed outside the project directory.
- **Documented** with a how-to page, "Add agents and skills to a project",
  covering what it does for each agent and what to add to `.gitignore`.
- **Tested.** CI proves that the template creates a working setup, with
  skill links in the expected directories, so it can't silently break.

## Affected users and systems

- Teams and individual contributors who want a project-scoped agent setup,
  including users of Nix and devenv without Home Manager or NixOS.
- Likely files:
  - a template directory and a `templates` output;
  - possibly a small reusable devenv module;
  - a docs page, `SUMMARY.md`, and AGENTS.md and CONTRIBUTING.md;
  - a CI check.
- No change to skills, the Home Manager module, `nixosModules.agentic` or
  the demo. Skill users are unaffected.

## Constraints

- **Project-scoped only.** Nothing is written outside the project directory
  and devenv's own state. No home-directory or system changes.
- **Whole skill folders,** never extracts: `SKILL.md` with its
  `references/`, `sources.json` and licence, as everywhere else.
- **Generated links stay out of version control.** The linked directories
  point into the Nix store. The design must keep them out of commits, and
  must not overwrite a project's own hand-written skills in the same
  directories.
- **The main flake gains no inputs.** Anything needing llm-agents.nix
  follows the #58 pattern and lives outside the main flake's inputs.
- **Pinned and reviewable.** Skills and agent versions come from the
  project's lock file and change only when the project updates it.
- **Honest about agent support:**
  - project skill directories are documented for Claude Code, Codex,
    OpenCode and Antigravity;
  - symlink discovery is documented only for Claude Code and Codex, as the
    rest of the site already says;
  - the page must not overclaim.
- **Existing rules still apply:** the Nix style rules, the documentation
  table limits, CI green, and the intent → spec → plan gates.

## Open questions

- **devenv only, or also a plain flake `devShell`?** devenv's `files`
  option links folders declaratively. A plain flake needs a `shellHook`,
  which is simpler for flake users but more fragile.
- **Which skills by default?** All ten, or a small default set (for example
  `nix-workflow`, `nix-language` and `devenv-project`), with a list the
  project edits?
- **The agent in the project shell.** Included by default (Claude Code), or
  opt-in, leaving agent choice to each contributor's own machine?
- **How to publish it.** A `nix flake init` template, a reusable devenv
  module imported through `devenv.yaml`, or both?
