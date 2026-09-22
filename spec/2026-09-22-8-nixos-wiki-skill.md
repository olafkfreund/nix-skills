---
status: draft
issue: 8
intent: intent/2026-09-22-8-nixos-wiki-skill.md
---

# Spec: Source-maintained NixOS Wiki skill

## Design

### Package and initial scope

Add `skills/nixos-wiki/`, independently installable with normal skill discovery:

```text
SKILL.md
scripts/wiki.py
references/index.md
references/pages.json
references/templates.json
sources.json
COPYING
```

Keep `SKILL.md` short. Route NixOS configuration and troubleshooting questions to
relevant bundled wiki pages, then verify version-sensitive recommendations against
the consumer's pinned manuals, option definitions or source. Follow repository
and host policy, distinguish module-managed from standalone Home Manager, and
separate reading guidance from authorization to change or activate configuration.
Do not imply that a recent wiki revision establishes correctness for a release.
This skill complements the three existing skills without requiring them.

Start with these **17 exact main-namespace titles**, verified in the dump:

- NixOS; NixOS modules; NixOS Installation Guide.
- Nixos-rebuild; Updating NixOS; Flakes; Home Manager.
- Bootloader; Linux kernel; Storage optimization; Garbage Collection.
- Networking; Firewall; SSH.
- Systemd; Systemd/User Services; Systemd/timers.

This is a curated corpus, not an exhaustive wiki mirror. Keep the short Systemd
index as context for its selected subpages. Garbage Collection is a redirect to
Storage optimization with a section fragment; preserve the alias and fragment.
Do not silently add linked articles or non-English alternatives. Other topics
remain available through the live wiki, explicitly outside the retained snapshot.
Adding primary titles requires reviewed policy changes.

Retain the exact latest wikitext of these pages plus the copyright-policy page
`Official NixOS Wiki:Copyrights` in `references/pages.json`. Retain latest wikitext
for namespace 10 in `references/templates.json`, including template redirects and
documentation subpages. This bounded support set avoids dropping indirect or
computed template dependencies: inspected latest template text totals only
113,160 bytes across 183 pages. It is not loaded into agent context by default.
Template additions/removals are reported and subject to package-size limits.

The primary title allowlist selects inspected English source pages, not all of
namespace 0: inspection found translated articles inside namespace 0. Exclude
separate translated article titles and namespace 1198 fragments from primary
results. Preserve `<translate>`, translation markers and template source as data.
New language/title mappings require review rather than heuristic suffix deletion.

### Preserve wikitext; retrieve rather than render

Do **not** build a MediaWiki-to-Markdown converter or template interpreter.
Retain original wikitext, including syntaxhighlight/pre/code blocks, warnings,
cleanup notices, tables, references, templates and parser functions. Decode XML
transport escaping once through the XML parser; do not then HTML-unescape,
reformat, execute, or strip article text. Do not fetch images or file attachments.
Generated Markdown is only the topic index with provenance and lookup instructions.

The portable `scripts/wiki.py` uses Python 3.10+ standard library, with no Nix,
network, pip install, database or cache required for use. Support:

- `search <literal query>`: deterministic title-first then body matching, at most
  10 results with bounded excerpts and page identities. Templates are excluded
  from ordinary results; an explicit template search mode includes them.
- `show <exact title>`: print the original wikitext with a separate metadata
  header, revision citation, snapshot identity, and an explicit line window.
  Default to at most 200 lines / 16 KiB; support bounded pagination and clearly
  report omitted ranges. Reject ambiguous/missing titles instead of guessing.
- `show Template:<name>`: retrieve a template definition without expanding it.
  Follow a bounded redirect chain on request, retaining every hop and any fragment;
  detect cycles. A target outside the bundle is identified as unavailable, with
  a live wiki link clearly distinguished from a pinned source citation.

Search snippets and partial windows are discovery aids, not complete recipes.
The skill instructs the agent to read applicable page-level notices and complete
relevant examples before use, inspecting template definitions as needed. Explain
that definitions alone do not constitute rendered expansion: parser functions,
magic words, computed names, or transclusions outside the retained set can require
checking the wiki/manual before interpreting a claim. Never invent their output.
Raw unhandled syntax stays visible; there is no silent conversion fallback.
A pinned article permalink is a citation to its revision, not a promise that the
live wiki renders transcluded templates at their historical versions.

Treat wiki text as reference data, not agent instructions. Never execute commands,
Nix expressions, template bodies or links during ingestion or lookup. Agents
without executable helper support may inspect the index and individual JSON
records using their available file tools; native discovery across all agents is
not claimed without testing.

### Source identity, retention and regeneration

Initial source: `https://wiki.nixos.org/wikidump.xml.zst`, inspected 2026-09-22,
SHA-256 `0f7faeceaab57e43e4e8c8797a0c9feaa9da0320e219ed70914fea1910a171d0`.
It contains 29,936,297 compressed bytes and 232,782,442 uncompressed bytes.
Use the downloaded, hash-verified snapshot for initial implementation; never
silently substitute whatever the moving URL serves later.

Record source URL and compressed SHA-256; per-record title, namespace, page ID,
revision ID, revision timestamp, content model, redirect information and SHA-256
of UTF-8 wikitext; selection and template-scope policy; deterministic input/output
hashes; and copyright-policy revision identity. Avoid wall-clock generation
timestamps, temporary paths, contributor IP addresses and edit-history payloads.
Use numeric revision permalinks under the official wiki origin. Validate identifiers
and timestamps; retain one latest revision per page by timestamp with revision ID
as tie-breaker. Duplicate/conflicting records, suppressed/missing selected text,
non-wikitext content or unsupported schema fail visibly.

The checked-in JSON snapshots are the exact consumed textual inputs, not rendered
summaries. They retain selected page revisions and the complete template support
set, so old repository commits reproduce the index, metadata and lookup behavior
without retrieving an expired dump. The full historical dump is not committed,
retained as a release asset, or required for offline checks. Its checksum records
which acquisition produced the extracted snapshot; the extracted inputs cannot
reconstruct the original full XML. Document that distinction explicitly.

Use a focused maintenance module `scripts/wiki.py` at repository level, distinct
from the package-local lookup helper. Reuse existing serialization, hashing,
staged publication and artifact validation helpers. Do not introduce a general
provider framework. Acquisition uses HTTPS with timeouts and a temporary file;
verify transport completion and Zstandard integrity before publication. Use the
existing `zstd` CLI only for ingestion, explicitly provisioned in update CI;
normal offline checks and skill use require only Python. No host installation.

Bound compressed input at 128 MiB, expanded XML at 1 GiB, individual revision text
at 1 MiB, total pages at 50,000 and revisions at 500,000. Stream decompression and
XML parsing, release processed revisions, reject DTD/entity declarations, and
check decompressor exit status. Abort and clean temporary data on any limit,
network or parsing failure. Keep existing artifact limits (2,000,000 bytes/member,
12,000,000 bytes/archive); growing beyond them requires review, not silent widening.

### Updates and publication boundaries

Extend the existing commands with explicit `--skill nixos-wiki`:

- `--check`: offline verification of retained record hashes/schema, reproducible
  index/manifest outputs, package membership, links and lookup behavior. It does
  not download the moving dump or claim to re-prove full-dump extraction.
- `--latest`: acquire one bounded dump, identify its hash, and extract a candidate.
- `--dump <path> --sha256 <digest>`: explicit local-snapshot ingestion requiring
  an exact hash. These paired flags are wiki-only. Reject release/revision flags
  for the wiki and wiki-specific flags for other skills.

An identical compressed hash is a no-op. A different hash with identical retained
page/template revisions and text is also a no-op: report that no relevant content
changed and retain the last accepted provenance. An advanced relevant revision,
including a revision whose text is unchanged, updates the snapshot and reports
whether the change is content or provenance only. Do not create PRs merely for
unselected history or recompression changes.

Automatic updates reject older revisions/timestamps for retained pages, changed
text under an unchanged revision ID, missing primary titles, changed primary page
identity and changed copyright policy. Report template additions/removals and
redirect changes prominently; reject redirects that break selected primary routes.
Wiki revisions do not have Git ancestry semantics. Neither HTTP Last-Modified
nor a larger revision number alone guarantees that the entire dump is newer.
Manual rollback uses a reviewed repository commit, not relaxed automatic checks.

Only `references/index.md`, `references/pages.json`, `references/templates.json`,
`sources.json` and `COPYING` may be automatically written. The source origin,
primary-title selection, namespace policy, size limits, schema policy and copyright
policy identity are immutable to automation. Authored SKILL.md, the lookup helper,
maintenance code, tests, workflows and all sibling packages remain protected.
COPYING is mechanically derived from the accepted policy record and must remain
unchanged during automatic updates; a changed policy requires a reviewed task.

Add a fourth skill to the existing check/update workflow matrices, retaining
Monday 06:17 UTC and manual dispatch. Use independent artifacts/concurrency and
`automation/nixos-wiki-reference-update`, with at most one open PR. Keep read-only
acquisition/testing separate from narrow write publication. Apply existing stale
base, path/member, hash, symlink, policy and sibling checks before replacement;
restore previous bytes on ordinary partial-write failure. No automatic merge,
agent installation, personal token or release-asset publishing. Failed acquisition
or validation leaves the previous skill usable.

### Licensing and documentation

Include the MIT notice from copyright policy revision 22887, attributed to the
NixOS Foundation and contributors. Preserve source citations and explain extraction
and omission of history; do not relicense sibling material. Do not download media
or infer that its license matches textual contributions.

Update README with scope, raw-wikitext limitations, search/show examples, Python
and ingestion-only Zstandard requirements, offline versus acquisition validation,
manual snapshot ingestion, automatic updates, pinned installation and rollback.

## Alternatives rejected

- Entire dump/history in Git or model context: excessive unrelated material,
  historical ambiguity and unnecessary attribution/privacy metadata.
- Full latest wiki mirror in the first skill: expands scope and artifact sizes;
  reviewed primary titles establish a useful, bounded initial corpus.
- Handwritten wikitext rendering/template expansion: too much MediaWiki behavior
  to reproduce reliably; raw retention keeps caveats and examples inspectable.
- Live-rendered HTML as the retained source: can mix current template revisions
  with historical pages and undermines snapshot reproduction.
- Remote-only cache/release assets: unnecessary for the small retained corpus and
  adds availability/publication requirements to ordinary skill use.
- Embeddings, vector database, MediaWiki server or LLM-generated summaries: no
  demonstrated need for the selected corpus; literal lookup and retained source
  provide simpler, deterministic provenance.

## Risks

- Wiki guidance can be stale or inappropriate despite being the latest revision.
  Applying it requires consumer-pin checks and local authorization.
- Raw wikitext is less convenient than rendered prose. Retrieval must expose
  notices and dependencies, and must not imply semantic expansion was verified.
- Upstream schema, page identities, licensing, redirect or size changes can stop
  updates. That is a visible review condition; previous snapshots remain usable.
- Shared-tool changes could affect sibling maintenance. Protect package bytes and
  run all existing checks before merge; no host changes are part of this task.

## Verification

Test full-history input selecting only the latest revision, exact wikitext/code
preservation, deterministic extraction and offline regeneration, record/manifest
hashes, pinned links, redirects and loops, bounded literal search and pagination,
and template retrieval. Include malformed/truncated XML/Zstandard, DTD/entities,
limit overruns, duplicate identities, missing/suppressed text, revision regressions,
unchanged-revision mutations, copyright changes and unsupported schemas/models.

Test same-dump and irrelevant-change no-ops, relevant/provenance-only updates,
review reports, immutable policy/helper boundaries, stale/malicious artifacts,
partial-write restoration and sibling isolation. Exercise explicit hashed-snapshot
input using the inspected dump. Verify offline checks with networking unavailable.
Validate skill metadata and actionlint, then all four workflow paths on clean CI.
Do not execute arbitrary wiki examples, deploy a host, or claim runtime correctness
of all included advice. After authorized merge, observe the live updater and
report a no-op separately from actual changed-source PR publication.
