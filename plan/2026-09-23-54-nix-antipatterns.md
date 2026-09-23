---
status: approved
issue: 54
spec: spec/2026-09-23-54-nix-antipatterns.md
---

# Plan: stop two common LLM mistakes in Nix

## Approved decisions

These come from the approved spec. The plan can be followed without opening
the intent or spec.

**Rules.**
- Never search or hard-code `/nix/store`.
- Never quote an attribute name that is a valid identifier, meaning it fully
  matches `[A-Za-z_][A-Za-z0-9_'-]*` and is not one of the keywords `assert
  else if in inherit let or rec then with` (Nix manual, identifiers).
- Quotes are required for other names, for keywords, and for
  interpolation.

**Guidance.** The following section is added, identical, to all ten
`skills/*/SKILL.md`: before `## References` where one exists, otherwise at
the end.

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

No `SKILL.md` is a generated output; each skill's `sources.json` `outputs`
lists only references and licences. Editing a provider `SKILL.md` was tested
with `check.py --skill home-manager` and passes.

**Check: `scripts/nix_style.py`,** a pure module that executes no package
content.

- **`findings(text)`** scans fenced code blocks in Markdown and returns
  `(kind, line)` pairs:
  - **`quoted-name`**, in `nix` blocks only. A string literal `"NAME"`
    containing no `\`, `"` or `${`, where:
    - it comes right after `.`; or
    - it comes after the line start, `{` or `;` and is followed by `=` (not
      `==`) or `.`;

    and `NAME` is an identifier that is not a keyword.
  - **`store-search`**, in any block. A line matching
    `\b(find|ls|fd|locate)\b.*?/nix/store`, or containing `/nix/store/*`.
  - **`store-path`**, in any block. A line containing
    `/nix/store/[0-9a-df-np-sv-z]{32}-`.
  - **The marker.** A block whose opening fence is immediately preceded by
    the line `<!-- nix-style: counterexample -->` is skipped.
- **`check_collection.validate(root)`:**
  - it checks each authored `*.md` in each package (not in that skill's
    `sources.json` `outputs`) and the root `README.md`;
  - the first finding raises
    `ValueError(f"Nix style ({kind}): {path}: {line}")`;
  - `validate`'s return value is unchanged.
- **`generated_findings(root)`** returns counts by kind for the generated
  outputs. When the total is above zero, the main block prints
  `Nix style in generated references (not failing): <counts>`.
- **Marker placement.** The marker is added once, on the line before the
  `find` fence in `skills/nix-workflow/references/finding-things.md`.

**Tests** (`tests/test_collection.py`):
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
  - quoted names in an `sh` block;
  - a store search in a block with the marker.
- **Through `validate`:** in a temporary package, an authored reference with
  `pkgs."foo-bar"` fails. The same file listed in `sources.json` `outputs`
  passes, and `generated_findings` counts it.

**CONTRIBUTING.md**, "Add a skill": one sentence saying that authored
Markdown must not quote valid identifiers or search or hard-code
`/nix/store`, that `check_collection.py` enforces this, and that the rare
deliberate counterexample needs the marker.

### Deviation during implementation

- **Step 2's expected report was incomplete.** It said "9 quoted-name", but
  the actual report is `9 quoted-name, 20 store-path`.
- **The 20 store paths are legitimate upstream example output, not
  advice:**
  - `home-manager/references/rollbacks.md` (10): `--list-generations`
    output;
  - `nix-language/references/language.md` (6) and `builtins.md` (1):
    `builtins.getContext` and `storePath` examples;
  - `nixpkgs-development/references/helpers.md` (2): build error messages;
  - `nixos-operations/references/operations.md` (1): `systemctl status`
    output.
- **No behaviour changes.** Generated references are reported, never
  failed, as the spec says.
- **Required quotes are left alone.** `{ "/nix/store/…-a.drv" = …; }` in
  `builtins.md` is not counted as `quoted-name`: a store path is not an
  identifier, so its quotes are required.

## Steps

1. **`scripts/nix_style.py` and its tests.** Write the module and the
   `findings` unit tests.
   → Verify: `python3 -m unittest discover -s tests -p 'test_*.py'` passes.
2. **`scripts/check_collection.py`.** Wire the module into `validate`, add
   `generated_findings`, and print the count. Add the marker to
   `finding-things.md`. Add the `validate` integration test.
   → Verify:
   - `python3 scripts/check_collection.py` passes and prints the
     generated-reference count (9 quoted-name expected);
   - the unit tests pass;
   - the manual negative check: temporarily add `pkgs."foo-bar"` to an
     authored reference, confirm the check fails with `quoted-name`, then
     revert.
3. **The ten `SKILL.md` files.** Add the "Nix style" section.
   → Verify: `check_collection.py` passes, and `grep -c '^## Nix style'
   skills/*/SKILL.md` shows one per skill. For each provider skill,
   `python3 scripts/check.py --skill <name>` passes; this needs no network.
4. **`CONTRIBUTING.md`.** Add the sentence.
   → Verify: `check_collection.py` passes.
5. **Full checks.** `devenv shell check-fast`, `nix flake check`,
   `nix build .#nix-skills --no-link`. Commit (steps 1–2, then 3–4), push,
   and open a PR with `Closes #54` linking the intent, spec and plan.
   → Verify that CI is green and the PR is `CLEAN` under branch protection.
   Do not merge without approval.

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_collection.py
for s in devenv-project home-manager microvm-nix nix-darwin nix-language nixos-operations nixos-wiki nixpkgs-development; do python3 scripts/check.py --skill "$s"; done
devenv shell check-fast
nix flake check
nix build .#nix-skills --no-link
```

## Rollback

- Before merge: close the PR and delete the branch.
- After merge: `git revert` the implementation commits. The check, the ten
  sections, the marker and the CONTRIBUTING sentence are all removed. No
  generated files or state outside the repository are touched.
