---
status: draft
issue: 30
author: olafkfreund
---

# Intent: NixOS system operations skill

## Problem

User feedback named NixOS administrators as one of three typical entry points
into Nix, and said they "mostly use the rebuild command". No skill in the
collection covers operating a NixOS system:

- rebuild modes (switch, boot, test, build) and when each is appropriate;
- generations and rollback;
- deliberate upgrades of channels or flake inputs;
- cleaning the store safely;
- recovering from boot problems;
- managing services.

`nixos-wiki` has 17 wiki topics, but not the NixOS manual's authoritative
text. #27 split this work out of the darwin task. The `nix-workflow` routing
table currently sends NixOS administrators to the wiki and the upstream
manual only.

At the pinned Nixpkgs revision (`9c0ece3d…`), the relevant NixOS manual
chapters are small, about 22 KB in total:

| File (`nixos/doc/manual/…`) | Bytes |
|---|---|
| `installation/changing-config.chapter.md` | 3,654 |
| `installation/upgrading.chapter.md` | 5,314 |
| `administration/rollback.section.md` | 1,276 |
| `administration/cleaning-store.chapter.md` | 1,875 |
| `administration/boot-problems.section.md` | 3,282 |
| `administration/service-mgmt.chapter.md` | 6,924 |

They use the NixOS manual markup that the `nixpkgs` updater already converts:
`{#id}` anchors, `::: {.warning}` admonitions and the `{manpage}` role.

## Proposed outcome

An agent helping a NixOS administrator:

- explains and chooses the right rebuild mode;
- lists generations and proposes a rollback;
- upgrades deliberately;
- cleans the store safely, without deleting what the user still needs;
- diagnoses boot and service problems.

All of this comes from pinned NixOS manual excerpts that regenerate weekly
like the rest of the collection. Every state-changing action is presented as
a proposal that needs the user's authorization. The `nix-workflow` routing
row for NixOS administrators points to the new skill.

## Affected users and systems

- NixOS administrators and their agents, through the collection.
- A new maintained skill, `nixos-operations`, and its provider code. The
  `nixpkgs` provider is written for the `nixpkgs-development` package, so the
  spec decides whether to generalise it or add a sibling provider.
- Registration: check, update, artifact, workflows, `devenv.nix`,
  `skills.json` and the README. A weekly updater enrollment is a reviewed
  decision.
- The routing row in `nix-workflow`.

## Constraints

- **Pinned, attributed excerpts:** Nixpkgs, including the NixOS manual, is
  MIT. Provenance, hashing, reproducible `--check` and a reviewed selection,
  as for the other providers.
- **Links must be resolved safely, not dropped or left broken.** The six
  chapters contain five links to NixOS option anchors (`#opt-…`) and two
  cross-references to other manual sections (`#sec-…` / `#ch-…`). The
  `nixpkgs` provider indexes anchors only under `doc/`, not
  `nixos/doc/manual/`, so these fail closed today. The option anchors are
  generated from the options at build time, not written in the Markdown.
- **Existing output unchanged:** any change to shared provider code must
  leave the existing `nixpkgs-development` output byte-identical.
- **No state changes without authorization:**
  - rebuilding, switching, rolling back, collecting garbage, deleting
    generations, changing boot entries and restarting services are only
    proposed;
  - the manual's commands are reference material, not instructions to run;
  - the text is also not a reason to switch a user between channel-based
    and flake-based setups.
- **Excerpts stay loadable:** about 22 KB.

## Open questions

- **Provider shape:** generalise the `nixpkgs` provider so one updater
  produces two packages from one pinned Nixpkgs checkout, or add a small
  sibling provider that reuses its manual-format functions? The
  recommendation is a sibling provider that imports `excerpt`, `convert` and
  friends. That keeps `nixpkgs-development` untouched and gives each package
  its own manifest and pin.
- **Resolving option links:** candidates are
  - a pinned link to the option's declaration in the Nixpkgs source, found
    by evaluating the NixOS options at the pin;
  - an unpinned search.nixos.org link;
  - a reviewed per-link map, like `anchor_fixes` in #26.

  The recommendation is the reviewed map, since there are only five links. It
  fails closed when upstream adds a new option link, and a reviewer maps it.
  The spec should compare it with declaration lookup.
- **Which pin:** share the `nixpkgs-development` master pin, or track a
  stable release branch, since administrators usually run a release? The
  recommendation is master, like `nixpkgs-development`, with SKILL.md telling
  the agent to check the user's actual release.
