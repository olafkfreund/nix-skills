---
status: draft
issue: 54
intent: intent/2026-09-23-54-nix-antipatterns.md
---

# Spec: stop two common LLM mistakes in Nix

## Facts

Checked on 2026-09-23.

- **The identifier grammar**, from the
  [Nix manual](https://nix.dev/manual/nix/2.35/language/identifiers.html), is
  `[A-Za-z_][A-Za-z0-9_'-]*`, and the keywords are `assert else if in inherit
  let or rec then with`. A *name* is an identifier or a string literal, and
  both forms are equivalent for the same characters.
- **Generated versus authored files.** Generated files are exactly the keys
  of `outputs` in each skill's `sources.json`: references and licence files.
  No `SKILL.md` is ever an output, so all ten `SKILL.md` files are authored.
  The `nix-workflow` and `nixos-coding-agents` skills have no
  `sources.json`, so they are wholly authored.
- **Store paths in authored code blocks.** The only `/nix/store` occurrence
  is the deliberate counterexample in
  `skills/nix-workflow/references/finding-things.md`, in its "Why not search
  the store" section.
- **Unnecessary quotes in generated references:** 9 instances, in
  `devenv-project/references/configuration.md`,
  `home-manager/references/modular-services.md`,
  `microvm-nix/references/simple-network.md` and
  `nix-darwin/references/readme.md`. There are none in authored content.
- **`scripts/check_collection.py`** is an offline `validate(root)` that
  raises `ValueError` on the first problem. It already walks every `*.md` in
  each package. It is tested in `tests/test_collection.py` and runs in
  `check-fast` and in CI's `collection` job.
- **`SKILL.md` layouts vary.**
  - `nix-workflow` and `nixos-coding-agents` have `## Rules` sections.
  - `devenv-project`, `microvm-nix`, `nixos-wiki` and `nixpkgs-development`
    have no `##` sections.
  - The others have topic sections.

## Design

### Default answers to the intent's open questions

The intent was approved without answers. These defaults apply unless the spec
review changes them:

1. **Where the rules live.** In every `SKILL.md`, as one identical short
   section, because skills are installed independently. No cross-skill
   links.
2. **Store-search scope.** Both patterns are flagged:
   - shell searches of the store (`find`, `ls`, `fd` or `locate` with
     `/nix/store`, or a `/nix/store/*` glob);
   - hard-coded hashed store paths (`/nix/store/<32-char hash>-…`) in any
     code block.
3. **Generated references.** Report their unnecessary quotes as information
   when the check runs, without failing it.

### Guidance: one section in all ten `SKILL.md` files

Append this identical section to each `SKILL.md`, before `## References`
where one exists, otherwise at the end:

```markdown
## Nix style

- Never search `/nix/store` (for example `find /nix/store/*foo-* -name libfoo.so`)
  and never copy a literal store path. Find the providing package with
  `nix-locate`, and refer to it through Nix: `${pkgs.foo}/lib` or
  `lib.makeLibraryPath [ pkgs.foo ]`.
- Do not quote attribute names that are valid identifiers
  (`[A-Za-z_][A-Za-z0-9_'-]*`, dashes included). Write `pkgs.foo-bar` and
  `packages.x86_64-linux`, not `pkgs."foo-bar"`. Quote only other names
  (`".config/foo"`, `"2.0"`), the keywords
  `assert else if in inherit let or rec then with`, and interpolations
  (`"${name}"`). Upstream examples in references sometimes quote needlessly;
  do not copy that style.
```

- `nix-workflow` rule 1 already states the store rule at more length; its
  section is still added, so the quoting rule is present.
- The last sentence covers the upstream examples, so no per-skill wording
  is needed.

### Check: `scripts/nix_style.py`, called from `validate`

A small pure module with no execution of package content:

- **`findings(text)`** returns a list of `(kind, line)` for fenced code
  blocks in Markdown text:
  - **`quoted-name`**, only in ```` ```nix ```` blocks. A string literal
    `"NAME"` with no `\`, `"` or `${` inside, used as a name, meaning:
    - it comes right after `.`; or
    - it comes at the start of a binding, after the line start, `{` or `;`,
      and is followed by `=` (not `==`) or by `.`;

    and `NAME` fully matches `[A-Za-z_][A-Za-z0-9_'-]*` and is not a
    keyword.
  - **`store-search`**, in any fenced block. A line matching
    `\b(find|ls|fd|locate)\b.*?/nix/store` or containing `/nix/store/*`.
  - **`store-path`**, in any fenced block. A line containing
    `/nix/store/[0-9a-df-np-sv-z]{32}-`, the Nix base-32 hash alphabet.
- **Allowed counterexample.** A fenced block immediately preceded by the
  line `<!-- nix-style: counterexample -->` is skipped. This marker is added
  once, before the `find` block in `finding-things.md`. It is an HTML
  comment, invisible when rendered.
- **`validate(root)`** in `check_collection.py`:
  - it checks each authored `*.md` in each package, meaning everything not
    listed in that skill's `sources.json` `outputs`, plus the root
    `README.md`;
  - it raises `ValueError(f"Nix style ({kind}): {path}: {line}")` for the
    first finding.
- **Generated references** are scanned too, but only counted.
  `check_collection.py`'s main prints
  `Nix style in generated references (not failing): N quoted-name, …`
  when N > 0. The count is exposed through a small `generated_findings(root)`
  helper, so `validate`'s return value stays unchanged.

### Tests: `tests/test_collection.py`

A new test covers `nix_style.findings`:

- **Flagged:**
  - `pkgs."foo-bar"`, `packages."x86_64-linux".default`,
    `"foo-bar" = 1;` and `{ "a_b" = 1; }`;
  - `find /nix/store/*foo-* -name x`, `ls /nix/store | grep foo` and
    `ls /nix/store/*-openssl*/lib`;
  - `/nix/store/0123456789abcdfghijklmnpqrsvwxyz-foo`.
- **Not flagged:**
  - `".config/foo" = x;`, `"2.0" = x;`, `"a.b" = 1;`, `"with" = 1;`,
    `"or" = 1;` and `"${name}" = 1;`;
  - `description = "foo-bar";`, `x = "a" == "b";` and `[ "foo-bar" ]`;
  - quoted names in a non-nix block;
  - the store search in a block with the counterexample marker.
- **Through `validate`:** in a temporary package, an authored reference with
  a bad quote fails. The same content listed in `sources.json` `outputs`
  passes, and is counted by `generated_findings`.

### Documentation

`CONTRIBUTING.md`, "Add a skill": add one sentence. It says that authored
Markdown must not quote valid identifiers or search or hard-code
`/nix/store`, that `check_collection.py` enforces this, and that it names
the counterexample marker.

## Alternatives rejected

- **One shared reference that other skills link to.** A skill installed on
  its own could not resolve a link to another skill, which breaks
  portability.
- **Rewriting the upstream examples.** That breaks provenance hashes and the
  verbatim copying the licences are based on. Providers regenerate the
  files anyway.
- **Failing on generated references.** Every upstream refresh could fail for
  style the collection does not own, which blocks updates.
- **Running a Nix parser or formatter (`nixfmt`, `nix-instantiate`) on
  blocks.** Formatters do not remove unnecessary quotes, and parsing needs
  fragments wrapped and is slower. Metadata validation must also stay
  dependency-free and offline. The regular-expression check is narrow and
  covered by tests.
- **Checking agent output.** Out of reach for this repository. The skills
  shape agent behaviour; the check keeps the skills themselves exemplary.

## Risks

- **False positives** on unusual but valid code: mitigated by the tests of
  required quotes, the narrow name contexts (after `.`, or a binding
  left-hand side), and fixture examples.
- **False negatives,** for example a quoted name after `?` (`a ? "foo-bar"`)
  or inside `inherit (x) "foo"`. These are accepted as rare; the guidance
  still covers them.
- **Duplicated text in ten files** could drift. It is identical and short.
  A future change edits all ten, and review sees the duplication.
- **Longer entrypoints:** about 11 lines are added to each `SKILL.md`, which
  keeps them well within "short".
- **Upstream copies an explicit store search into a generated reference.**
  It is only counted, never failing, and is visible in update runs.

## Verification

- `python3 scripts/check_collection.py` passes on the repository, and prints
  the generated-reference count (currently 9 quoted-name).
- `python3 -m unittest discover -s tests -p 'test_*.py'` passes, including
  the new cases.
- `devenv shell check-fast`, `nix flake check` and
  `nix build .#nix-skills --no-link` pass.
- `check.py --skill <name>` passes for each provider skill whose `SKILL.md`
  changed, confirming that the edited `SKILL.md` files are outside
  provenance hashes. CI's provider jobs run this too.
- **Manual negative check:** temporarily add `pkgs."foo-bar"` to an authored
  reference and confirm `check_collection.py` fails with a `quoted-name`
  message. Revert before committing.
