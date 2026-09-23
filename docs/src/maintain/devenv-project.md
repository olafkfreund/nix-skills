# devenv maintenance

The same commands accept `--skill devenv-project`; omitting `--skill` retains
all existing Nix behavior:

```sh
python3 scripts/check.py --skill devenv-project
python3 scripts/update.py --skill devenv-project --check
python3 scripts/update.py --skill devenv-project --release v2.3.1
python3 scripts/update.py --skill devenv-project --latest
```

Devenv updates use stable GitHub Releases, not unreleased `main`. The updater
converts selected Markdown/MDX sections, preserving tab labels, version notices,
warning meaning, and fenced executable text. Unsupported forms or renamed paths
fail for review. It reads the committed options JSON at the same revision and
records generator/template provenance; it does not rebuild the full website or
option catalogue. Declaration links into devenv are checked and pinned; foreign
links retain their distinct origin. Public devenv.sh links are checked but follow
the moving site, while exact source citations and hashes remain revision-pinned.

`--check` obtains the matching CLI from the pinned upstream flake and evaluates
matching modules in a disposable project using the reviewed auxiliary pins in
`tests/devenv/devenv.lock`. It compares representative defaults against upstream
option data and runs harmless shell/script/task/`enterTest` assertions. Language
and service enablement is evaluated without starting services. The test does not
run `devenv allow` or modify user trust. A candidate update changes only the
module pin in its temporary fixture; unrelated input changes fail for review.
Local builds can use configured substitutes; CI explicitly uses upstream's
published devenv/Cachix cache keys. There is no fallback to the host CLI.
