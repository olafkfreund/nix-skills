---
status: draft
issue: 41
intent: intent/2026-09-23-41-readme-onboarding.md
---

# Spec: README onboarding for new users

## Facts

Checked on 2026-09-23 against each agent's current documentation (the links
are the same as in `spec/2026-09-22-16-agent-installation.md`) and this
repository.

| Agent | User skill directory (module destination) | Explicit invocation | Automatic selection | List skills | Symlinked skill folders |
|---|---|---|---|---|---|
| Claude Code | `~/.claude/skills` | `/<name>` | Yes, by description | `/skills` | Documented as supported |
| Codex | `~/.agents/skills` | `$<name>`; `/skills` opens a picker | Yes, by description | `/skills` | Documented as supported |
| OpenCode | `~/.config/opencode/skills` | None; the agent calls its `skill` tool | Yes; names and descriptions are listed in the tool | Ask the agent | Not documented |
| Antigravity | `~/.gemini/config/skills` | `/<name>` | Yes, by semantic match on description | Not documented | Not documented |

Sources:
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenCode skills](https://opencode.ai/docs/skills)
- [Antigravity workflows to skills](https://www.antigravity.google/docs/migration/workflows-to-skills/)

Other facts:

- **OpenCode also searches `~/.claude/skills` and `~/.agents/skills`,** and
  its troubleshooting asks for skill names to be unique across all locations.
  A user who installs for Claude or Codex already has the skills in OpenCode.
  Adding `"opencode"` to `agents` as well would give duplicate names.
- **The module installs each skill as a symlink.** `nix/home-manager.nix`
  links each skill directory as one `home.file` entry pointing into
  `/nix/store`. It does not use `recursive`, so each skill directory is a
  symlink.
- **The README today** (475 lines):
  - `# nix-skills`, a one-line description, then the skill table;
  - `## Use`, which covers manual clone-and-symlink for Codex only, and whose
    `ln -s` list is missing `nixos-coding-agents`;
  - `## Maintain`, which contains the user-facing
    `### Declarative installation on NixOS`, including the
    `agents = [ … ]` option;
  - development and per-skill maintenance sections, `## Automatic updates`,
    and `## Sources and licensing`.
- **Internal anchors.** Only `CONTRIBUTING.md` links into the README, to
  `#automatic-updates`, which does not move.

## Design

### Default answers to the intent's open questions

The intent was approved without answers. These defaults apply unless the spec
review changes them:

1. **Placement.** A new `## Getting started` section goes directly after the
   one-line description, before the skill table. `## Use` stays as the
   manual reference.
2. **Start line.** One generic start prompt that works in every agent,
   followed by a small table of explicit per-agent invocations.
3. **Antigravity.** It is a first-class example: its path and `/<name>`
   invocation are documented. For both Antigravity and OpenCode, the
   onboarding includes a check that the agent actually lists the skills,
   because discovery through symlinks is not documented for them.
4. **Maintainer sections.** They stay in the README. Only
   `### Declarative installation on NixOS` moves, from `## Maintain` into
   `## Use`, with its heading text unchanged so its anchor stays stable.

### New README structure

```
# nix-skills
<one-line description, unchanged>

## Getting started            ← new
### What this is for
### 1. Install the skills for your agent
### 2. Check that the agent sees them
### 3. Start with this prompt
### Examples
### User story: start coding with agents on NixOS

<skill table and notes, unchanged>

## Use                        ← kept; manual reference
  <clone and pin, ln -s list (+ nixos-coding-agents), invocation>
### Declarative installation on NixOS   ← moved here from Maintain, text unchanged
## Maintain                   ← minus the moved subsection
  … unchanged …
```

### Section contents

**What this is for** (about 5 lines). AI coding agents often give Nix advice
that is out of date, meant for another distribution, or imperative:
`nix-env -i`, editing generated files, `curl | sh`. These skills give the
agent current, source-backed guidance for Nix, NixOS, Home Manager,
nix-darwin, devenv, Nixpkgs and AI coding agents on NixOS. Each skill is
pinned and version-checked, so the agent proposes declarative, reversible
changes. The collection installs skills, not agents.

**1. Install the skills for your agent.**

- **Recommended: declarative, on NixOS with Home Manager as a module.** The
  input, `programs.nix-skills = { enable = true; agents = [ "claude" ]; };`,
  and a table mapping each agent to its `agents` value and directory. Rebuild
  with `nixos-rebuild` (never `home-manager switch`). Link to
  [Declarative installation on NixOS](#declarative-installation-on-nixos)
  for the options (`skills`, `directory`, and the data package).
- **OpenCode note.** OpenCode also reads `~/.claude/skills` and
  `~/.agents/skills`. If Claude or Codex is already selected, do not add
  `"opencode"` as well, or skill names are duplicated.
- **Manual fallback.** Clone at a reviewed commit, then
  `ln -s "$PWD/skills/<name>" <agent-dir>/<name>`. Link to `## Use`.

**2. Check that the agent sees them.**

- `ls ~/.claude/skills` (or the agent's directory) shows the skill names.
- In the agent, run the check from the Facts table: `/skills` in Claude
  Code and Codex; for OpenCode and Antigravity, ask "Which skills do you have
  available?"
- If a skill is missing in OpenCode or Antigravity, the likely cause is
  symlink discovery, which those agents do not document. Say so, and point to
  the issue tracker.

**3. Start with this prompt.** One code block:

```text
Use the nix-skills skills. I'm on NixOS and want to set up this machine for
agentic coding. Read my system configuration first, tell me what you found,
and propose changes as a diff. Do not rebuild, install or run containers
until I approve.
```

Followed by the explicit invocation per agent: `/nixos-coding-agents`
(Claude Code, Antigravity), `$nixos-coding-agents` (Codex), and for OpenCode,
"name the skill in your prompt".

**Examples.** A table of about six prompts, each mapped to the skill it
should trigger:

| You ask | Skill |
|---|---|
| "My rebuild fails with 'The option … does not exist'. What changed?" | `nixos-operations`, `nixos-wiki` |
| "Add a devenv shell with Python 3.12 and Postgres to this repo." | `devenv-project` |
| "Which package provides `libssl.so`, and how do I reference it?" | `nix-workflow` |
| "Move my shell and git config into Home Manager." | `home-manager` |
| "Package this Go CLI with `buildGoModule`." | `nixpkgs-development` |
| "Run Claude Code on this repo so it cannot read `~/.ssh`." | `nixos-coding-agents` |

**User story: start coding with agents on NixOS.** "As a NixOS user with no
AI agent yet, I want a coding agent set up declaratively, and optionally
sandboxed, so that I can start agentic coding without breaking my system or
exposing my secrets." Five numbered steps, each with a **Check**:

1. **Run an agent once, without installing it.**
   `nix run github:numtide/llm-agents.nix#claude-code`, or `#codex`,
   `#opencode`, `#antigravity-cli`. Check: it starts.
2. **Install the skills for that agent** (step 1 above) and rebuild. Check:
   step 2 above.
3. **Ask the agent with the start prompt,** from the system configuration
   repository. Check: the agent reads the configuration and proposes a diff
   without applying it. Typically the diff adds:
   - the llm-agents.nix input and the chosen agent;
   - the Numtide cache;
   - optionally `virtualisation.podman.enable` for sandboxing.
4. **Review, then build and switch yourself.** `nixos-rebuild build`, then
   `switch`. Check: the agent is on `PATH` and `nix run` is no longer needed.
   Undo: roll back the generation.
5. **Per project.** In a code repository, ask for a devenv shell
   (`devenv-project`). For untrusted repositories, run the agent in a
   container or an agent-box worktree (`nixos-coding-agents`, stories 3 and
   4). Check: the devenv shell activates, and the sandbox check from that
   story passes.

The detail lives in
[`nixos-coding-agents` user stories](skills/nixos-coding-agents/references/user-stories.md),
which the README links to rather than copies.

### Other edits

- `## Use`: add `nixos-coding-agents` to the `ln -s` list. Retitle the Codex
  paragraph as the manual fallback for any agent. The invocation line refers
  to the per-agent table in Getting started.
- `skills/nixos-coding-agents/references/user-stories.md`: no change.
  Stories 1 and 2 already match steps 1 and 4, so there is nothing to
  diverge.

## Alternatives rejected

- **Replacing `## Use` entirely.** It is the only manual,
  non-Home-Manager path and is still correct. Keep it as the reference.
- **Moving maintainer sections to `CONTRIBUTING.md` now.** It would double
  the diff and change anchors that users and automation may link to. That is
  a separate change.
- **A separate `docs/getting-started.md`.** The repository has no `docs/`,
  and people land on the README. One extra file would be read less.
- **Per-agent onboarding sections.** Four near-identical copies would drift.
  One flow with a small per-agent table is enough.
- **Installing an agent from this repository's module.** Out of scope. The
  collection ships skills, not agents; llm-agents.nix already provides the
  agents.

## Risks

- **Agent documentation changes.** Directories and invocation syntax may
  change. Mitigation: a "checked 2026-09-23" note on the per-agent table,
  with links to each agent's documentation.
- **Overclaiming discovery.** For OpenCode and Antigravity, symlinked skill
  directories are undocumented. The check step and its wording make this
  explicit rather than implying it is tested.
- **Duplicate skills in OpenCode.** Mitigated by the explicit note.
- **Moving the declarative section.** Its heading text is unchanged, so the
  anchor `#declarative-installation-on-nixos` still resolves.
- **The prompt as a promise.** The start prompt asks the agent to propose and
  wait. Agents may still act. The story's steps put rebuilding in the user's
  hands.

## Verification

- `python3 scripts/check_collection.py`, `devenv shell check-fast`,
  `nix flake check`, `nix build .#nix-skills --no-link`.
- All relative links and in-page anchors in `README.md` resolve, checked with
  `scripts/check.py`'s `links` and `anchors` helpers in a one-off script.
- Nix snippets parse (`nix-instantiate --parse`, with fragments wrapped).
- `README.md` diff review:
  - the moved section's text is unchanged, apart from its position;
  - no maintainer content is lost;
  - `## Automatic updates` keeps its anchor.
- Every `agents` value and directory in Getting started matches
  `nix/agent-directories.nix`.
