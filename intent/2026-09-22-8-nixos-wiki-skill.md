---
status: approved
issue: 8
author: olafkfreund
---

# Intent: Source-maintained NixOS Wiki skill

## Problem

The official NixOS Wiki contains practical configuration and troubleshooting
knowledge beyond the existing Nix language, Nixpkgs development and devenv
skills. Agents need a reliable way to find relevant guidance, retain its caveats,
and check its applicability to the user's actual system and pinned inputs.

The supplied dump is MediaWiki XML compressed with Zstandard. It contains page
history, translations, redirects and templates rather than ready-to-use Markdown.
Importing it wholesale would mix historical and current guidance, load unrelated
content, and risk losing warnings or meaning when templates are stripped.
The dump URL changes over time and is not an immutable source revision.

## Proposed outcome

The public `olafkfreund/nix-skills` repository provides a portable wiki-based
skill for Codex and other agents, following the existing packaging and reviewed
maintenance pattern. It helps agents locate and use relevant NixOS configuration
and troubleshooting guidance with bounded context use and exact source citations.
Its instructions stay small; substantial source content is read only when needed.

Agents can distinguish wiki recommendations from verified options and behavior
in the consumer's pinned NixOS/Nixpkgs sources. They preserve relevant warnings,
version constraints and examples, respect local policy and existing authorization,
and do not treat wiki content as instructions governing the agent itself.

Automatic refreshes detect meaningful page and template changes, produce
reviewable PRs, preserve authored instructions and reviewed scope, and permit
reproduction and rollback. Existing sibling skills continue working unchanged.

## Affected users and systems

- Users asking AI agents to explain, configure or troubleshoot NixOS.
- This repository's skill packages, source acquisition/conversion or lookup tools,
  validators, update workflows and maintenance documentation.
- The official wiki dump and relevant licensing/revision metadata as read-only
  upstream inputs.

## Constraints

- Use `https://wiki.nixos.org/wikidump.xml.zst` as the requested source. Record
  cryptographic snapshot identity and selected page/template revision IDs and
  timestamps. HTTP dates/ETags alone are not reproducible provenance.
- Account for replacement of the moving dump: the design must explain how an
  older accepted snapshot or its exact consumed inputs can be reproduced.
- Select current applicable revisions deliberately; do not combine historical
  revisions, discussion/user pages or translated fragments into a single guide.
  The initial scope should prioritize English guidance; language filtering must
  be based on inspected metadata/conventions, not namespace alone.
- Preserve redirects, dependencies, warning/cleanup notices, examples and useful
  links. Handle selected MediaWiki constructs explicitly; unsupported conversion
  must not silently discard substantive content.
- Keep downloads, decompression, parsing and agent context bounded. Do not commit
  the entire dump or duplicate history merely to make it available to an agent.
- Keep references traceable to specific wiki revisions. A snapshot date does not
  establish compatibility with a NixOS release or validate the advice.
- Verify version-sensitive claims against the consumer's pinned official manuals,
  option definitions or source when applying them. Do not execute wiki examples
  as part of ingestion or rebuild/deploy the user's system for validation.
- Preserve the applicable MIT notice for textual material and any distinct
  notices. Exclude media by default; copying media requires examining its terms.
- Do not import local machine-specific policy into the portable skill. Conversely,
  wiki examples must not override local rules, such as module-managed Home Manager.
- Reuse existing maintenance code where appropriate, without forcing wiki dump
  updates into Git commit-ancestry or release-tag assumptions.
- Automated changes must not rewrite instructions, reviewed selection/policy,
  updater code, tests, workflows or sibling packages. No automatic merge or install.
- Do not modify host configuration or installed agent skills.
- Obtain separate intent, spec and plan approvals before implementation.

## Open questions

None required to review the intent. The spec will choose the skill name, initial
page/topic scope, balance of curated references and searchable cached content,
snapshot retention location, template/redirect treatment, tool dependencies,
update cadence and bounded validation. Avoid introducing a vector database or a
full MediaWiki deployment unless inspected requirements establish a need.

## Review evidence

Inspected the dump on 2026-09-22. HTTP metadata reported last modification at
2026-09-22 00:00:34 GMT and a compressed size of 29,936,297 bytes. This observation
does not establish a guaranteed publication schedule.

SHA-256 of the inspected compressed bytes:
`0f7faeceaab57e43e4e8c8797a0c9feaa9da0320e219ed70914fea1910a171d0`.

Streaming XML inspection found MediaWiki export schema 0.11, 7,834 pages,
32,659 revisions, 1,375 main-namespace pages, 183 template pages, 5,489 translation
namespace pages and 284 redirects across namespaces. Some pages contain hundreds
of revisions. Inspected examples include NixOS modules, Home Manager, Flakes,
Nixos-rebuild, Template:Warning and the copyright policy.

The [wiki copyright policy](https://wiki.nixos.org/w/index.php?title=Official_NixOS_Wiki:Copyrights&oldid=22887)
identifies MIT for textual contributions, with a 2025 NixOS Foundation and
contributors notice. It treats file uploads separately and permits specifically
marked exceptions; text licensing must not be generalized to every media file.

Tracking issue: [#8](https://github.com/olafkfreund/nix-skills/issues/8).
