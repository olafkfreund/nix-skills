# Nix style rules

Every `SKILL.md` in the collection carries these two rules, and
`scripts/check_collection.py` enforces them in hand-written Markdown.

## Never search or hard-code the store

Searching `/nix/store` only finds what happens to be on this machine, cannot
tell which path belongs to your pin, and a copied store path breaks on the
next update. Instead:

- find the package that provides a file with `nix-locate`;
- refer to it through Nix: `${pkgs.foo}/lib`, or
  `lib.makeLibraryPath [ pkgs.foo ]`.

## Do not quote names that need no quotes

An attribute name can be written without quotes when it is a valid
identifier ([Nix manual](https://nix.dev/manual/nix/2.35/language/identifiers.html)):
it matches `[A-Za-z_][A-Za-z0-9_'-]*` and is not a keyword. Dashes are
allowed, so `pkgs.foo-bar` and `packages.x86_64-linux` need no quotes.

Quotes are needed only for:

- names outside that grammar: `".config/foo"`, `"2.0"`, `"a.b"`;
- the keywords `assert else if in inherit let or rec then with`;
- interpolation: `"${name}"`.

## What the check does

| Finding | Where | Example that fails |
| --- | --- | --- |
| `quoted-name` | `nix` code blocks | `pkgs."foo-bar"`, `"foo-bar" = 1;` |
| `store-search` | any code block | `find` or `ls` of the store, a store glob |
| `store-path` | any code block | a hard-coded hashed store path |

- Hand-written files fail the check; generated upstream references are only
  reported, because they are verbatim copies.
- A deliberate counterexample needs the line
  `<!-- nix-style: counterexample -->` directly before its code fence.
- This site's pages are checked the same way when the site is built.
