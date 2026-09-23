---
status: approved
issue: 37
spec: spec/2026-09-23-37-nixos-coding-agents.md
---

# Plan: NixOS coding agents skill

## Approved decisions

These come from the approved spec. The plan can be followed without opening
the intent or spec.

**The skill:**
- It is a new authored skill, `nixos-coding-agents`, covering choosing,
  installing and sandboxing AI coding agents on NixOS.
- It links to three upstream projects and copies no text from them:
  - [numtide/llm-agents.nix](https://github.com/numtide/llm-agents.nix)
    (packages)
  - [nothingnesses/agent-images](https://github.com/nothingnesses/agent-images)
    (OCI images)
  - [0xferrous/agent-box](https://github.com/0xferrous/agent-box)
    (disposable workspaces in containers)
- It has no `sources.json`, licence file, provider, updater or scripts.
  `nix/` needs no change.

**Files:**
- `skills/nixos-coding-agents/SKILL.md`: the entrypoint, about 70 lines.
- `skills/nixos-coding-agents/references/user-stories.md`: the guide.
- `skills/nixos-coding-agents/references/setup.md`: the reference
  configuration.
- `skills/nixos-coding-agents/references/security.md`: what each layer
  protects and what it does not.
- Registration: `skills.json` (sorted), a routing row in
  `skills/nix-workflow/SKILL.md` under "Other skills by role", and a
  `README.md` skill-table row.

**Scope:**
- NixOS first.
- nix-darwin and standalone Home Manager get packages only; the images and
  agent-box are Linux only.
- Portal gets one paragraph, a link and a deny-by-default note, with no user
  story of its own.

**Decision tree (in `SKILL.md`):**
1. Try it once with `nix run`, or with the picker.
2. Keep it: add the flake input, the overlay and the packages.
3. Keep it away from secrets: an agent-images container that mounts only the
   project.
4. Run agents in parallel or on throwaway branches: agent-box worktree mode.
5. Set a team standard: an image built with `mkAgentImage`, plus a committed
   `.agent-box.toml`.

Choosing an agent means comparing licence (free or unfree), how it is built
(source or binary), which provider key it needs, and whether the cache has
it. The skill links to the upstream README for these rather than copying it.

**Rules for the agent using the skill:**
- Check the user's release and nixpkgs branch before suggesting `follows`.
- Never suggest `home-manager switch` to someone who runs Home Manager as a
  NixOS module.
- Never add a secret to `env_passthrough` without saying what it exposes.
- Do not build images or start containers without asking.

**Six user stories.** Each has As a / I want / so that, a configuration or
command, a **Check**, and an **Undo**:
1. try an agent with `nix run`;
2. install agents declaratively and pinned, with an unfree predicate listing
   named packages and the cache in `nix.settings`;
3. keep an agent away from `~/.ssh`, `~/.aws` and `.env`;
4. run three agents on three disposable agent-box worktrees;
5. build a team `mkAgentImage` image;
6. pick an agent by licence, cost and provider.

**Security content.** `security.md` opens by saying containers reduce
exposure but are not a hard boundary. It covers:
- what is passed in through `-e` or `env_passthrough`;
- local mode versus worktree mode;
- the trust policy;
- supply chain: daily updates, pinning, the cache key, unfree binaries;
- nixpkgs coupling;
- Portal set to deny by default;
- Nix builds inside a container.

**Examples.** Use an unfree predicate listing named packages, never
`allowUnfree = true`. Include a "checked against upstream on 2026-09-23"
line in `SKILL.md`.

### Resolved while planning (the spec left these to implementation)

Checked in the nixpkgs source on 2026-09-23:

- **No subuid ranges needed.** In `nixos/modules/config/users-groups.nix`,
  `isNormalUser` with empty `subUidRanges` and `subGidRanges` sets
  `autoSubUidGidRange = mkDefault true`, a 65536 range. The ranges that
  agent-images' README adds by hand are therefore redundant for normal users.
  `setup.md` shows explicit ranges only as the fallback for system users, or
  when the user has already set their own ranges.
- **No hand-written policy.** In
  `nixos/modules/virtualisation/podman/default.nix`, enabling Podman sets
  `virtualisation.containers.enable = true`. In `containers.nix`, an empty
  `virtualisation.containers.policy` then writes skopeo's
  `default-policy.json` to `/etc/containers/policy.json`, and that policy
  accepts any image. The hand-written `~/.config/containers/policy.json`
  step is therefore unnecessary on NixOS.
- **Resulting guide.**
  - `setup.md` gives `virtualisation.podman.enable = true;` as the whole
    NixOS setup, with `dockerCompat` optional.
  - `security.md` states that the default policy accepts any image.
  - A stricter `virtualisation.containers.policy` is described only in prose
    with a link to `containers-policy.json(5)`, unless step 3 below confirms
    a working example.

## Steps

The plan cites the current step in each implementation commit. Any deviation
updates this file in the same commit.

1. `skills/nixos-coding-agents/SKILL.md`: write the frontmatter (two lines,
   `name` and a plain one-line `description` with no `: `), the pipeline, the
   decision tree, how to choose an agent, the rules, the reference links and
   the "checked on" line.
   → Verify with `python3 scripts/check_collection.py`, which may report only
   that `skills.json` is missing the skill until step 5.
2. `references/user-stories.md`: write the six stories in the format above.
   Each snippet is the smallest one that works. Upstream-specific details,
   such as the `ab` flags and the `mkAgentImage` parameters, are kept to one
   example plus a link.
   → Verify that the relative links and anchors resolve (`check_collection`).
3. `references/setup.md`: cover:
   - the llm-agents.nix input, both install styles and their cache
     trade-off, the cache settings, the unstable warning, and `home.packages`;
   - Podman with the defaults above, and `podman system migrate` after
     changing the ranges;
   - building, loading and running an agent-images image;
   - installing `ab`, a minimal `~/.agent-box.toml`, and local versus
     worktree mode;
   - the Portal paragraph, and nix-darwin and standalone Home Manager.

   → Verify every option name with the nixos MCP, on unstable. Also check
   `nix.settings.extra-substituters`,
   `nix.settings.extra-trusted-public-keys`,
   `nixpkgs.config.allowUnfreePredicate`,
   `virtualisation.podman.dockerCompat` and `home.packages`. Where a snippet
   is a NixOS module, check it with `nix-instantiate --parse`, which checks
   syntax only and evaluates nothing on the host.
4. `references/security.md`: write the content listed above.
   → Verify with `check_collection`, and by rereading the intent's
   constraints: no default passthrough of the SSH socket or cloud
   credentials, and `insecureAcceptAnything` presented only as a local
   default.
5. `skills.json`: add `"nixos-coding-agents"` in sorted position.
   `skills/nix-workflow/SKILL.md`: add the routing row. `README.md`: add a
   table row.
   → Verify that `check_collection.py` passes cleanly.
6. Run the full check suite (see Tests), then push the branch and open a PR
   with `Closes #37` that links the intent, spec and plan.
   → Verify that CI is green on the PR. Do not merge without your approval.

## Tests

```sh
python3 scripts/check_collection.py              # passes, no errors
python3 -m unittest discover -s tests -p 'test_*.py'
devenv shell check-fast                          # collection, unit tests, actionlint
git add -A skills skills.json README.md          # stage before evaluating the flake
nix flake check
nix build .#nix-skills --no-link --print-out-paths   # output contains nixos-coding-agents/SKILL.md and three references
nix eval .#packages.aarch64-linux.nix-skills.drvPath --raw
```

`devenv shell check-providers` is not affected, since no provider changes,
and is not run. Nothing is installed, no image is built, no container runs,
and no host or home is activated.

## Rollback

- Before merge: close the PR and delete the branch `feat/37-nixos-coding-agents`.
- After merge: `git revert` the implementation commits. That removes the skill
  directory, the `skills.json` entry, the routing row and the README row. No
  state outside the repository is touched, and Home Manager consumers lose the
  skill on their next rebuild.
