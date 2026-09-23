# Home Manager maintenance

```sh
python3 scripts/check.py --skill home-manager
python3 scripts/update.py --skill home-manager --check
python3 scripts/update.py --skill home-manager --revision <full-commit-sha>
python3 scripts/update.py --skill home-manager --latest
```

Home Manager tracks the `master` branch by full commit revision. The package
contains selected manual pages for NixOS-module integration, configuration,
dotfiles, modular services, and writing modules. It does not mirror the full
option catalogue. Relative source links are pinned to the selected commit,
fenced examples are preserved, and the authored `SKILL.md` is never replaced.
An upstream path or license change fails for review rather than changing the
curated selection automatically.
