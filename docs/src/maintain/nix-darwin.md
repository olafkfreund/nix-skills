# nix-darwin maintenance

```sh
python3 scripts/check.py --skill nix-darwin
python3 scripts/update.py --skill nix-darwin --check
python3 scripts/update.py --skill nix-darwin --revision <full-commit-sha>
python3 scripts/update.py --skill nix-darwin --latest
```

nix-darwin tracks the `master` branch by full commit revision. The package
contains nix-darwin's README, its only prose documentation; options are
generated upstream and are not bundled. `darwin-rebuild` guidance in the
authored SKILL.md was checked against `pkgs/nix-tools/darwin-rebuild.sh` at the
initial revision and should be re-checked when that script changes.
