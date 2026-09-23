---
status: approved
issue: 41
spec: spec/2026-09-23-41-readme-onboarding.md
---

# Plan: README onboarding for new users

## Approved decisions

These come from the approved spec. The plan can be followed without opening
the intent or spec.

**Scope.** Only `README.md` changes. No skill, module, package, provider,
automation or host changes. `skills/nixos-coding-agents/references/user-stories.md`
is unchanged; the README links to it.

**Structure.**
- A new `## Getting started` section goes directly after the one-line
  description and before the skill table. It has these subsections, in
  order:
  1. `### What this is for`
  2. `### 1. Install the skills for your agent`
  3. `### 2. Check that the agent sees them`
  4. `### 3. Start with this prompt`
  5. `### Examples`
  6. `### User story: start coding with agents on NixOS`
- The skill table and its notes are unchanged, and come after Getting
  started.
- `## Use` stays as the manual reference.
- `### Declarative installation on NixOS` moves, text unchanged, from
  `## Maintain` to the end of `## Use`. Its heading text stays the same, so
  the anchor `#declarative-installation-on-nixos` is stable.
- Everything else in `## Maintain`, `## Automatic updates` and
  `## Sources and licensing` is unchanged.

**Per-agent facts.** Checked on 2026-09-23 against each agent's
documentation. The directories match `nix/agent-directories.nix`.

| Agent | `agents` value | Directory | Call a skill | List skills |
|---|---|---|---|---|
| Claude Code | `"claude"` | `~/.claude/skills` | `/nixos-coding-agents` | `/skills` |
| Codex | `"codex"` | `~/.agents/skills` | `$nixos-coding-agents` | `/skills` |
| OpenCode | `"opencode"` | `~/.config/opencode/skills` | Name the skill in the prompt; it loads through its `skill` tool | Ask the agent |
| Antigravity | `"antigravity"` | `~/.gemini/config/skills` | `/nixos-coding-agents` | Ask the agent |

All four also select skills automatically from their descriptions.

- **OpenCode.** OpenCode also reads `~/.claude/skills` and
  `~/.agents/skills`, and needs skill names to be unique. If `"claude"` or
  `"codex"` is already selected, do not add `"opencode"`.
- **Symlinks.** The module installs each skill as a symlink into
  `/nix/store`. Symlinked skills are documented as supported only for
  Claude Code and Codex. For OpenCode and Antigravity, the check step asks
  the agent to list its skills, and says a missing skill most likely means
  symlink discovery, which should be reported as an issue.

The section links to the four documentation sources:
- [Claude Code](https://code.claude.com/docs/en/skills)
- [Codex](https://learn.chatgpt.com/docs/build-skills)
- [OpenCode](https://opencode.ai/docs/skills)
- [Antigravity](https://www.antigravity.google/docs/migration/workflows-to-skills/)

**What this is for** (about 5 lines):
- AI agents often give Nix advice that is out of date, meant for another
  distribution, or imperative (`nix-env -i`, editing generated files,
  `curl | sh`).
- These skills give the agent current, source-backed guidance for Nix,
  NixOS, Home Manager, nix-darwin, devenv, Nixpkgs, and running AI coding
  agents on NixOS.
- They are pinned and version-checked, so the agent proposes declarative,
  reversible changes.
- The collection installs skills, not agents.

**Install.**
- **Recommended path.** The flake input
  `inputs.nix-skills.url = "github:olafkfreund/nix-skills";` (commit the
  lock), and
  `programs.nix-skills = { enable = true; agents = [ "claude" ]; };` inside
  `home-manager.users.<you>`, with the module imported. Rebuild with
  `nixos-rebuild`, never `home-manager switch`. Then the per-agent table,
  the OpenCode note, and a link to
  [Declarative installation on NixOS](#declarative-installation-on-nixos)
  for `skills`, `directory` and the data package.
- **Manual fallback.** Clone at a reviewed commit, then
  `ln -s "$PWD/skills/<name>" <agent directory>/<name>`, and link to
  [Use](#use).

**Check.**
- `ls` the agent's directory to see the skill names.
- In the agent, use `/skills` (Claude Code, Codex), or ask "Which skills do
  you have available?" (OpenCode, Antigravity).
- The symlink note for OpenCode and Antigravity.

**Start prompt** (exact text, in a `text` block):

```text
Use the nix-skills skills. I'm on NixOS and want to set up this machine for
agentic coding. Read my system configuration first, tell me what you found,
and propose changes as a diff. Do not rebuild, install or run containers
until I approve.
```

After the block, one line on calling a skill explicitly, as in the table.

**Examples table** (exact rows):

| You ask | Skill |
|---|---|
| "My rebuild fails with 'The option … does not exist'. What changed?" | `nixos-operations`, `nixos-wiki` |
| "Add a devenv shell with Python 3.12 and Postgres to this repo." | `devenv-project` |
| "Which package provides `libssl.so`, and how do I reference it?" | `nix-workflow` |
| "Move my shell and git config into Home Manager." | `home-manager` |
| "Package this Go CLI with `buildGoModule`." | `nixpkgs-development` |
| "Run Claude Code on this repo so it cannot read `~/.ssh`." | `nixos-coding-agents` |

**User story.** "As a NixOS user with no AI agent yet, I want a coding agent
set up declaratively, and optionally sandboxed, so that I can start agentic
coding without breaking my system or exposing my secrets." Five steps, each
with a **Check**:
1. **Run an agent once.**
   `nix run github:numtide/llm-agents.nix#claude-code` (or `#codex`,
   `#opencode`, `#antigravity-cli`). Check: it starts, and nothing is
   installed.
2. **Install the skills** for that agent (Install above) and rebuild.
   Check: as in Check above.
3. **From your system configuration repository, give the start prompt.**
   Check: the agent reads the configuration and proposes a diff without
   applying it. Typically the diff adds:
   - the llm-agents.nix input and the chosen agent;
   - the Numtide cache;
   - optionally `virtualisation.podman.enable` for sandboxing.
4. **Review the diff, then build and switch yourself.**
   `nixos-rebuild build`, then `switch`. Check: the agent is on `PATH`
   without `nix run`. Undo: roll back to the previous generation.
5. **Per project.** In a code repository, ask for a devenv shell
   (`devenv-project`). For untrusted repositories, run the agent in a
   container or an agent-box worktree. Check: the devenv shell activates,
   and the sandbox check from
   [`nixos-coding-agents` stories 3 and 4](skills/nixos-coding-agents/references/user-stories.md)
   passes.

**Other edits in `## Use`:**
- Add `ln -s "$PWD/skills/nixos-coding-agents" …` to the list.
- Frame the paragraph as the manual route for any agent, with Codex's
  directory as the example.
- The invocation line points to the per-agent table in Getting started.

## Steps

1. **`README.md`: insert `## Getting started`** after line 3 (the one-line
   description), with the six subsections above.
   → Verify by rendering or reading the section. Every fact matches the
   per-agent table and `nix/agent-directories.nix`.
2. **`README.md`: move `### Declarative installation on NixOS`** from
   `## Maintain` to the end of `## Use`, byte for byte.
   → Verify that the section text is identical before and after, for
   example by extracting it from both versions and running `diff`.
3. **`README.md`: edit `## Use`** as listed in "Other edits".
   → Verify that the `ln -s` list covers every entry in `skills.json`.
4. **Validate** (see Tests), commit, push, and open a PR with `Closes #41`
   linking the intent, spec and plan.
   → Verify that CI is green. Do not merge without approval.

## Tests

```sh
python3 scripts/check_collection.py
devenv shell check-fast
nix flake check
nix build .#nix-skills --no-link
```

One-off checks, with nothing committed:
- **Links and anchors.** Using `scripts/check.py`'s `links` and `anchors`,
  every relative link in `README.md` points to an existing file, and every
  `#fragment` resolves in its target. That includes
  `#declarative-installation-on-nixos`, `#use` and CONTRIBUTING's
  `#automatic-updates`.
- **Nix snippets.** Every `nix` block in `README.md` parses with
  `nix-instantiate --parse`, with fragments wrapped in `{ … }`.
- **Completeness.** A script confirms that every name in `skills.json`
  appears in the `ln -s` list and in the Home Manager `skills = [ … ]`
  example.
- **Nothing lost.** The count of `##` and `###` headings from the old
  README is preserved; only additions and the one moved subsection differ.

## Rollback

- Before merge: close the PR and delete the branch.
- After merge: `git revert` the README commit. It is documentation only,
  with no state elsewhere.
