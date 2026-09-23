---
status: draft
issue: 37
intent: intent/2026-09-23-37-nixos-coding-agents.md
---

# Spec: NixOS coding agents skill

## Facts

Checked on 2026-09-23 against the upstream repositories and the NixOS
unstable option index:

- **llm-agents.nix** (MIT):
  - It is a flake with `packages.<system>.<agent>` for about 200 agents, and
    it is updated daily.
  - `overlays.shared-nixpkgs` exposes them as `pkgs.llm-agents.<agent>`,
    built against the user's own nixpkgs. The user's `config`, including
    `allowUnfreePredicate`, then applies. The binary cache only hits when the
    user's nixpkgs revision matches the one upstream built with.
  - The binary cache is `https://cache.numtide.com`, with key
    `niks3.numtide.com-1:DTx8wZduET09hRmMtKdQDxNNthLQETkc/yaX7M4qK0g=`.
  - It is built and tested only against nixpkgs-unstable. Upstream warns that
    `inputs.nixpkgs.follows` onto a stable release "will break eventually".
  - `nix run github:numtide/llm-agents.nix` opens an fzf picker.
  - The generated README lists each package's licence (free or unfree) and
    source (built from source or a binary).
- **agent-images** (BlueOak-1.0.0):
  - `nix build .#<agent>` builds an OCI image, which is loaded with
    `podman load < result`.
  - The image runs as user `agent` (uid 1000) in `/workspace`. Its base tools
    are git, coreutils, ripgrep, jq, curl and similar.
  - `lib.mkAgentImage { pkgs; }` takes `name`, `agent`, `entrypoint`,
    `extraPackages`, `basePackages`, `extraEnv`, `user`, `uid`, `gid`,
    `workingDir` and `extraDirectories`.
  - The images are Linux only.
  - Its NixOS section enables Podman, adds subuid/subgid ranges and writes
    `~/.config/containers/policy.json`.
- **agent-box** (MIT, Rust):
  - The CLI is `ab`, configured in `~/.agent-box.toml` with `workspace_dir`,
    `base_repo_dir`, `[runtime] backend/image/env_passthrough`, and profiles.
  - `ab spawn --local` mounts the current directory, including gitignored
    files.
  - `ab new <repo> -s <session> --git` followed by `ab spawn -s <session>
    --git` gives an isolated worktree containing tracked files only. Jujutsu
    is the default workspace type.
  - The flake exports `homeManagerModules.agent-portal` for Portal, a broker
    for host operations over a Unix socket. It has no NixOS module.
- **NixOS options** (unstable, confirmed by lookup):
  - `virtualisation.podman.enable`
  - `virtualisation.podman.dockerCompat`
  - `virtualisation.containers.policy`: a declarative trust policy; when
    empty, the skopeo default is used.
  - `users.users.<name>.subUidRanges` and `subGidRanges`
  - `users.users.<name>.autoSubUidGidRange`: allocates a 65536 range
    automatically.
- **This repository:**
  - No skill covers AI agents.
  - `skills/nix-workflow/` is the precedent for a skill the author writes
    rather than copies: it has no `sources.json`, no licence file and no
    provider.
  - The routing table is in `skills/nix-workflow/SKILL.md` under
    "Other skills by role".
  - `nix/` packages every entry in `skills.json`, so it needs no change.

## Design

### Default answers to the intent's open questions

The intent was approved without answers. These defaults apply unless the spec
review changes them:

1. **Name.** `nixos-coding-agents`. It covers installing agents as well as
   sandboxing them.
2. **Scope.** NixOS first. A short section covers nix-darwin and standalone
   Home Manager, for installing packages only: the same flake input goes in
   `home.packages` or `environment.systemPackages`. It states that the
   images and agent-box are Linux only.
3. **Portal.** A link and one paragraph in `setup.md`, and a deny-by-default
   note in `security.md`. It does not get its own user story.

### Package

```
skills/nixos-coding-agents/
  SKILL.md
  references/
    user-stories.md
    setup.md
    security.md
```

All of it is authored prose that links to upstream. It contains no copied
upstream text, so it needs no `sources.json`, licence file, provider, updater
or scripts.

**`SKILL.md`** (short entrypoint, about 70 lines, like `nixos-operations`):

- Frontmatter: `name: nixos-coding-agents`, plus a single-line description
  covering choosing, installing and sandboxing AI coding agents on NixOS with
  llm-agents.nix, agent-images and agent-box.
- The three-layer pipeline, one line per project, with links.
- **Decision tree:**
  1. **Trying it once.** Use `nix run github:numtide/llm-agents.nix#<agent>`,
     or the picker.
  2. **Keeping it.** Add a flake input, the overlay and a list of packages
     (see `setup.md`).
  3. **Keeping it away from secrets.** Use an agent-images container that
     mounts only the project.
  4. **Running agents in parallel or on throwaway branches.** Use agent-box
     worktree mode.
  5. **Setting a team standard.** Build an image with `mkAgentImage` and
     commit a sample `.agent-box.toml`.
- **Choosing an agent.** Compare licence (free or unfree), how it is built
  (source or binary), the model provider and key it needs, and whether the
  cache has it. The upstream README lists all of these, and the skill links
  to it rather than copying the list, which changes daily.
- **Rules for the agent using this skill:**
  - Check the user's release and whether their nixpkgs is unstable or stable
    before suggesting `follows`.
  - Never suggest `home-manager switch` to someone who runs Home Manager as a
    NixOS module.
  - Never add a secret to `env_passthrough` without saying what it exposes.
  - Do not build images or start containers without asking.
- Links to the three reference files.

**`references/user-stories.md`** is the guide. There are six stories, each
with **As a / I want / so that**, a minimal configuration or command, a
**Check** command, and **Undo**:

1. **Try an agent without changing the system.** Uses `nix run`. Check: `…
   --version`. Undo: nothing to undo.
2. **Install selected agents declaratively and pinned.** Uses a flake input,
   `overlays.shared-nixpkgs`, `environment.systemPackages`, an
   `allowUnfreePredicate` limited to the chosen agents, and the cache in
   `nix.settings`. Check: `nixos-rebuild build` and then `which <agent>`.
   Undo: roll back to the previous generation.
3. **Run an agent that cannot read `~/.ssh`, `~/.aws` or `.env`.** Uses the
   rootless Podman setup, then builds and loads the image and runs it with
   only `./project:/workspace` mounted. Check: `ls ~/.ssh` inside the
   container fails.
4. **Run three agents on three disposable worktrees and compare their
   diffs.** Uses `ab new … --git` and `ab spawn` three times, then `git diff`
   on each worktree. Check: a gitignored file is not visible inside the
   container.
5. **Publish one reproducible team image.** A `mkAgentImage` flake output
   with the team's toolchain in `extraPackages`, a non-default `gid` for
   rootless Podman, and a committed `.agent-box.toml` example. Check:
   `nix build` gives the same store path on two machines.
6. **Pick an agent by licence, cost and provider.** Reading the upstream
   README fields, and an unfree predicate example. Check: `nix eval` of the
   package's `meta.license`.

**`references/setup.md`** is the reference configuration behind the stories:

- **llm-agents.nix.** The input, both install styles (flake packages or the
  overlay) and their cache trade-off, the cache settings, the
  nixpkgs-unstable warning, and Home Manager's `home.packages`.
- **Rootless Podman on NixOS.** `virtualisation.podman.enable`, the
  subuid/subgid ranges, and the trust policy set declaratively through
  `virtualisation.containers.policy`, preferred over the hand-written
  `~/.config/containers/policy.json` that upstream describes.
  - It prefers `autoSubUidGidRange` if implementation confirms that is enough
    for these images. Otherwise it uses explicit `subUidRanges` and
    `subGidRanges`, as upstream does.
  - It notes that after changing the ranges, the user runs `podman system
    migrate`, or `podman system reset`, which deletes containers and images,
    from their own terminal.
- **agent-images.** Building, loading and running an image. The
  `mkAgentImage` parameters are covered by a link, not copied.
- **agent-box.** Installing `ab` from its flake, a minimal
  `~/.agent-box.toml`, local mode versus worktree mode, and profiles (link).
- **Portal.** One paragraph and a link, including
  `homeManagerModules.agent-portal`.
- **nix-darwin and standalone Home Manager.** Packages only.

**`references/security.md`** covers what each layer protects and what it does
not:

- **Host install.** No isolation. The agent can read everything the user can.
- **Container.**
  - It protects unmounted paths.
  - It does not protect anything mounted, or anything passed in through
    `-e` or `env_passthrough`.
  - Passing `SSH_AUTH_SOCK`, `GH_TOKEN` or cloud credentials gives the agent
    that access.
  - Scope API keys per provider and prefer short-lived tokens.
- **Local mode versus worktree mode.** Local mode shows gitignored `.env`
  files; worktree mode shows only committed and tracked files.
- **Trust policy.** `insecureAcceptAnything` is acceptable for locally built,
  `localhost/` images only. It is not a team default.
- **Supply chain.**
  - llm-agents.nix updates binaries daily, so pin the input in committed
    configurations and review `flake.lock` diffs.
  - Adding a third-party cache means trusting its key.
  - Unfree binaries cannot be audited.
- **nixpkgs coupling.** Following nixpkgs onto a stable release breaks the
  flake and loses cache hits.
- **Portal.** Policies deny by default. Mediated write operations should ask
  first.
- **Nix inside the container.** Build sandboxing is limited in containers;
  link to the upstream note.

### Registration and routing

- `skills.json`: add `"nixos-coding-agents"` in sorted position.
- `skills/nix-workflow/SKILL.md`, "Other skills by role": add a row for
  "Running AI coding agents" → `nixos-coding-agents`.
- `README.md`: add a skill-table row. It gets no maintenance subsection,
  since nothing is automated. It should mention that the skill is authored
  and links to upstream.

## Alternatives rejected

- **Extending `nix-workflow`.** Its scope is everyday Nix practice. Agents,
  containers and a security model would blur its routing role and make it
  much larger.
- **A provider that pins the upstream READMEs,** like `nixos-operations`.
  Upstream changes daily, the README's package list is generated, and
  agent-images uses BlueOak licensing. A provider would need its own updater
  contract and review for little gain over links.
- **One skill per project.** Users need the combination, and choosing between
  the layers is the onboarding problem. Three skills would spread the
  decision tree across them.
- **A NixOS or Home Manager module in this repo** that installs agents. That
  is out of scope: this repository distributes skills, not system
  configuration. llm-agents.nix already provides packages and an overlay.
- **Codex's layout of six reference files.** Its split between
  `choosing-tools.md`, `examples.md`, `llm-agents-nix.md`, `agent-images.md`
  and `agent-box.md` duplicates what the stories and setup already cover.
  Three files are enough.

## Risks

- **Snippets go stale.** Upstream APIs may change, such as the
  `mkAgentImage` parameters or the `ab` flags. Mitigations:
  - keep upstream specifics to minimal examples plus links;
  - add a "checked against upstream on 2026-09-23" line in `SKILL.md`.
- **Wrong NixOS options.** Every option is confirmed in the option index
  during implementation. Where a snippet can be evaluated offline, it is
  checked with `nix eval` against a throwaway configuration, never by
  rebuilding the host.
- **Security advice that reads as a guarantee.** `security.md` opens by
  saying containers reduce exposure but are not a security boundary against
  a determined attacker.
- **Validation.** `check_collection.py` rejects `: ` in the description and
  broken anchors. Keep the description plain and run the check.
- **Unfree licensing.** The examples use a predicate listing named packages,
  never a blanket `allowUnfree = true`.

## Verification

- `python3 scripts/check_collection.py` passes.
- `devenv shell check-fast` passes: collection checks, unit tests and
  actionlint.
- `nix flake check`, `nix build .#nix-skills --no-link`, and
  `nix eval .#packages.aarch64-linux.nix-skills.drvPath --raw` succeed. New
  files are staged before the flake is evaluated.
- The built package contains `nixos-coding-agents/SKILL.md` and its three
  references.
- Every NixOS and Home Manager option named in the skill is found in the
  option index for unstable.
- Nothing is installed, no image is built, no container runs, and no host or
  home is activated.
