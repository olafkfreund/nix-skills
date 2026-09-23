# Update and roll back

The skills you use are whatever commit your flake lock (or checkout) pins.
Nothing updates on its own.

## With a flake input

Update only this input, review the change, then rebuild:

```sh
nix flake update nix-skills
git diff flake.lock
```

What changed between two commits is visible on GitHub:
`https://github.com/olafkfreund/nix-skills/compare/<old>...<new>`.

To roll back, restore the previous `flake.lock` (for example
`git checkout HEAD~1 -- flake.lock`) and rebuild, or boot the previous
NixOS generation.

## With a clone

Check out a newer reviewed commit (`git checkout --detach <sha>`). Linked
folders follow the checkout; copied folders must be replaced as complete
directories. To roll back, check out the previous commit.

## What changes between versions

Generated references change when upstream sources change; see the
[update schedule](../reference/update-schedule.md). Hand-written guidance
changes only through reviewed pull requests; see
[How updates work](../explanation/updates.md).
