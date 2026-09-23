---
status: approved
issue: 41
author: olafkfreund
---

# Intent: README onboarding for new users

## Problem

A newcomer landing on the README cannot quickly answer three questions: what
is this for, how do I install it in my agent, and what do I type first.

- **No purpose statement.** The README opens with a one-line description and
  a table of ten skills. It never says what problem the collection solves
  (agents give out-of-date or non-NixOS advice for Nix work) or who it is for.
- **The install path is hidden or incomplete.**
  - The declarative Home Manager module, which already supports
    `agents = [ "claude" "codex" "opencode" "antigravity" ]`, is buried under
    **Maintain** → "Declarative installation on NixOS", where users do not
    look.
  - **Use** covers only Codex, with manual symlinks. Its `ln -s` list is
    missing `nixos-coding-agents`.
- **No first step inside the agent.**
  - Nothing shows how each agent picks up or invokes a skill. The README only
    mentions Codex's `$name`.
  - Nothing gives an example prompt or shows what a good answer looks like.
- **No path for starting agentic coding on NixOS.** A user who has neither an
  agent nor the skills has a chicken-and-egg problem: they need an agent to
  use the skills, and the skills are what explain how to install an agent the
  NixOS way. `nixos-coding-agents` covers the second half, but the README
  never connects the two.

## Proposed outcome

A new user reads the top of the README and, within a few minutes, can do the
following:

1. **Understand the purpose.** The skills give their AI coding agent
   current, source-backed Nix, NixOS, Home Manager and devenv knowledge, so
   that it proposes declarative, reversible changes instead of imperative
   guesses.
2. **Install for their agent.** Claude, Codex, OpenCode or Antigravity, with
   one recommended declarative path (the existing Home Manager module) and
   one manual fallback, each with a check that the agent sees the skills.
3. **Know the first prompt.** A start line to paste into the agent, plus a
   few short examples of usage showing which skill each one triggers.
4. **Follow one end-to-end user story.** "I have NixOS and nothing else, and
   I want to start coding with an AI agent":
   - run an agent once from llm-agents.nix;
   - install the skills for it;
   - ask it to set up an agentic-coding environment on this machine, with
     the agent declared in the system configuration, optionally sandboxed,
     and a devenv project shell.

   Each step has a check, and the agent proposes changes instead of applying
   them.

The existing maintainer material keeps its content and moves below the
onboarding.

## Affected users and systems

- New users of the collection, especially NixOS users new to AI coding
  agents.
- Existing users. Anchors to moved sections may change, which affects
  bookmarks and links.
- `README.md`. Possibly a small cross-link from
  `skills/nixos-coding-agents/references/user-stories.md` to the new story,
  so the two do not diverge.
- No change to skills, modules, packages, providers or automation. No host is
  changed.

## Constraints

- **Accurate for each agent.**
  - The skill directory and invocation for each agent must match that
    agent's current documentation, or the module's existing
    `.claude/skills`, `.agents/skills`, `.config/opencode/skills` and
    `.gemini/config/skills` destinations.
  - Any claim not checked against an agent's documentation is marked as such.
  - The README currently says "native discovery in other agents is not
    claimed". The onboarding must not overclaim either.
- **Safe defaults.**
  - The user story never tells the user to run `home-manager switch` when
    Home Manager is a NixOS module.
  - It never pipes a vendor installer to a shell, and never passes secrets
    into containers by default.
  - The agent is asked to propose changes and wait for approval before
    rebuilding.
- **Not duplicated.**
  - The README links to `nixos-coding-agents` for agent choice and
    sandboxing rather than repeating it.
  - It reuses the existing module documentation rather than writing a second
    copy.
- **Reviewed pin.** Onboarding still recommends pinning a reviewed commit or
  locked flake input, consistent with **Use**.
- **Still valid.** `scripts/check_collection.py` and the existing checks keep
  passing. Relative links in the README resolve.

## Open questions

- **Placement.** Should onboarding replace the current **Use** section at the
  top, or be a new "Getting started" section above it, with **Use** kept as
  the manual reference?
- **Start line.** Should it be one generic prompt, such as "Using the
  nix-skills skills, help me set up this NixOS machine for agentic coding.
  Propose changes; do not apply them.", or a named invocation per agent,
  such as `/nixos-coding-agents` in Claude and `$nixos-coding-agents` in
  Codex?
- **Antigravity.** Is it a first-class example alongside Claude, Codex and
  OpenCode, or listed as supported through the module's destination only,
  until its skill discovery is verified?
- **Maintainer sections.** Should they move to CONTRIBUTING, to shorten the
  README, or stay under **Maintain**?
