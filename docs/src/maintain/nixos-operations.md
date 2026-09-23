# NixOS operations maintenance

```sh
python3 scripts/check.py --skill nixos-operations
python3 scripts/update.py --skill nixos-operations --check
python3 scripts/update.py --skill nixos-operations --revision <full-commit-sha>
python3 scripts/update.py --skill nixos-operations --latest
```

NixOS operations follows Nixpkgs `master` by full commit revision, with its own
manifest and the same pinned Nix toolchain and master-ancestry check as
`nixpkgs-development`. It bundles selected NixOS manual chapters (changing the
configuration, upgrading, rollback, store cleaning, boot problems and service
management). Links to NixOS options come from a reviewed map of option names,
and resolve to each option's declaring file, found by evaluating the NixOS
options at the pinned revision. An unmapped, missing or unused option link
fails the update for review. The provider reuses the `nixpkgs-development`
manual converter unchanged. Its excerpts are covered by the Nixpkgs
[COPYING](https://github.com/olafkfreund/nix-skills/blob/main/skills/nixos-operations/COPYING).
