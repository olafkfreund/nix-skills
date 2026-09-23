# microvm.nix maintenance

```sh
python3 scripts/check.py --skill microvm-nix
python3 scripts/update.py --skill microvm-nix --check
python3 scripts/update.py --skill microvm-nix --revision <full-commit-sha>
python3 scripts/update.py --skill microvm-nix --latest
```

microvm.nix tracks the `main` branch by full commit revision. The package
contains selected documentation for VM declarations, declarative deployment,
host integration, options, networking, and shares. Generated references pin
relative source links and preserve fenced examples; authored instructions and
the reviewed selection remain immutable to automation.
