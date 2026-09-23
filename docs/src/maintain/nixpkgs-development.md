# Nixpkgs maintenance

```sh
python3 scripts/check.py --skill nixpkgs-development
python3 scripts/update.py --skill nixpkgs-development --check
python3 scripts/update.py --skill nixpkgs-development --revision 7561e7e3e12a06677b1525a12bcccb0b4e4c601d
python3 scripts/update.py --skill nixpkgs-development --latest
```

Nixpkgs tracks **master snapshots**, not releases or channel promotions. The
`.version` value is development-series metadata. `--latest` resolves master once,
requires descendant ancestry from the previous snapshot, and regenerates/tests
any advanced SHA, even when only provenance changed. An identical SHA is a no-op.
Rewinds, divergence, unavailable inputs and unverifiable ancestry fail for review.
Explicit full-SHA repinning is reviewed work; `--release` is rejected for Nixpkgs.

The updater copies selected `doc/` sections and builds the pinned source's
`nixpkgs-manual.lib-docs` derivation for twelve curated library APIs. It does not
rebuild the whole website. Its independently pinned Nix 2.35.2 evaluator cannot
change through automated updates. If substitutes are unavailable, Nix may build
that evaluator, nixdoc and their dependencies; network/cache access and disk space
are needed. Authored instructions, selection, branch and evaluator policy remain
reviewed files. The snapshot records consumed inputs, coverage, generated API
records and outputs, including the upstream MIT license.

`--check` verifies deterministic generation and runs a small pinned fixture for
argument/attribute overrides, overlays, library/fileset results and generic module
composition. It builds a local-source package to check phase hooks and installed
output, and executes a small shell helper. Language helpers are evaluated for
availability; their full ecosystems are not built. Checks have been exercised on
x86_64-linux; this is not a claim of cross-platform or native-agent discovery tests.
No services, host configuration, user trust or installed skills are changed.

Custom manual anchors are resolved to bundled sections or pinned source files
with named sections. Unsupported documentation syntax fails before replacement.
Fenced code is preserved, including illustrative or historical upstream examples;
the Python excerpt identifies an upstream duplicate argument needing adaptation.
Consumers must use their own project's pin rather than assume master APIs exist
in older Nixpkgs. Roll back by restoring the entire skill from a reviewed commit.
