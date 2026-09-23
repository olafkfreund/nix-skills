# Setup

The configuration behind the [user stories](user-stories.md). Upstream
details were checked on 2026-09-23. Confirm current flags and parameters in
each project before relying on them.

## llm-agents.nix

[numtide/llm-agents.nix](https://github.com/numtide/llm-agents.nix) packages
about 200 AI coding agents and tools, and updates them daily.

- **Try without installing.** `nix run github:numtide/llm-agents.nix#<agent>`
  runs one agent; `nix run github:numtide/llm-agents.nix` opens an fzf picker.
  Using the flake directly also configures its binary cache.
- **Flake packages (recommended).** Add the input and list
  `llm-agents.packages.${pkgs.stdenv.hostPlatform.system}.<agent>` in
  `environment.systemPackages` or `home.packages`. They are built against the
  flake's own pinned nixpkgs, so they come from the cache, at the cost of a
  second nixpkgs evaluation. See [story 2](user-stories.md#2-install-agents-declaratively-and-pinned).
- **Overlay.** `overlays.shared-nixpkgs` exposes the same agents as
  `pkgs.llm-agents.<agent>`, built against your nixpkgs, sharing its
  dependencies. The cache only hits when your nixpkgs revision matches
  upstream's, so expect local builds.
- **nixpkgs branch.** Upstream builds and tests only against
  nixpkgs-unstable. Do not set `llm-agents.inputs.nixpkgs.follows` to a stable
  release; it breaks eventually. Leaving `follows` unset is safe on any
  release.
- **Binary cache.** When llm-agents.nix is an input, the flake's own
  `nixConfig` is not applied for you. Add the cache to the system instead:

  ```nix
  nix.settings = {
    extra-substituters = [ "https://cache.numtide.com" ];
    extra-trusted-public-keys = [
      "niks3.numtide.com-1:DTx8wZduET09hRmMtKdQDxNNthLQETkc/yaX7M4qK0g="
    ];
  };
  ```

  Adding a cache means trusting its key to sign what you run. See
  [security](security.md#supply-chain).
- **Unfree agents.** No `allowUnfree` setting is needed or effective; see
  [security](security.md#the-nixpkgs-unfree-check-does-not-apply).

## Rootless Podman on NixOS

On NixOS this is one option:

```nix
virtualisation.podman.enable = true;
# virtualisation.podman.dockerCompat = true;   # optional `docker` alias
```

The steps agent-images' README lists for NixOS are already covered by NixOS
defaults:

- **Subordinate ids.** A user with `isNormalUser = true` and no
  `subUidRanges` or `subGidRanges` of their own gets
  `autoSubUidGidRange`, a 65536 range, automatically. Set explicit
  `users.users.<name>.subUidRanges` and `subGidRanges` only for other users,
  and never through `environment.etc`, because the setuid `newuidmap` cannot
  follow a symlinked `/etc/subuid`.
- **Trust policy.** Enabling Podman enables `virtualisation.containers`,
  which writes `/etc/containers/policy.json`. With
  `virtualisation.containers.policy` left empty that file is skopeo's
  default, which accepts any image, so no `~/.config/containers/policy.json`
  is needed. To restrict it, set `virtualisation.containers.policy`; the
  format is in
  [containers-policy.json(5)](https://github.com/containers/image/blob/main/docs/containers-policy.json.5.md).

Rebuilding is the user's step, from their own terminal. After ranges change,
run `podman system migrate`. If a failed `podman load` left storage broken,
`podman system reset --force` fixes it but deletes all local containers and
images; ask first.

## agent-images

[nothingnesses/agent-images](https://github.com/nothingnesses/agent-images)
builds one OCI image per agent from llm-agents.nix. Each runs as user `agent`
(uid 1000) in `/workspace`, with git, coreutils, ripgrep, jq, curl and similar
tools. The images are Linux only.

```sh
nix build github:nothingnesses/agent-images#<agent>
podman load < result
podman run --rm -it --userns=keep-id -v "$PWD":/workspace \
  -e <PROVIDER>_API_KEY localhost/agent-images/<agent>:latest
```

- **`--userns=keep-id`** maps your uid into the container, so files written
  in `/workspace` belong to you and writes to `$HOME` or `/tmp` inside do not
  fail.
- **Custom images.** `agent-images.lib.mkAgentImage { inherit pkgs; }` takes
  `name`, `agent`, `entrypoint` and optional `extraPackages`, `basePackages`,
  `extraEnv`, `user`, `uid`, `gid`, `workingDir` and `extraDirectories`. See
  [custom images](https://github.com/nothingnesses/agent-images#custom-images)
  and [story 5](user-stories.md#5-publish-one-reproducible-team-image).
- **Nix inside the image.** Optional, with trade-offs. See
  [using Nix inside containers](https://github.com/nothingnesses/agent-images#using-nix-inside-containers)
  and [security](security.md#nix-inside-the-container).

## agent-box

[0xferrous/agent-box](https://github.com/0xferrous/agent-box) provides `ab`,
which creates a workspace per session and runs the agent image in it.

- **Install.** Try it with `nix run github:0xferrous/agent-box -- --help`
  (the default package is `ab`), or add the input and list
  `agent-box.packages.${pkgs.stdenv.hostPlatform.system}.default` in
  `environment.systemPackages` or `home.packages`. It uses Git, Jujutsu for
  JJ workspaces, and Podman or Docker.
- **Configuration.** A minimal `~/.agent-box.toml`:

  ```toml
  workspace_dir = "~/.local/agent-box/workspaces"
  base_repo_dir = "~/projects"   # the real, not symlinked, parent of your repositories

  [runtime]
  backend = "podman"
  image = "localhost/agent-images/claude-code:latest"
  env_passthrough = ["ANTHROPIC_API_KEY"]   # only what the agent needs
  ```

  The full format, including profiles, is in the
  [config reference](https://github.com/0xferrous/agent-box/blob/main/docs/src/reference/agent-box/config.md)
  and [profiles guide](https://github.com/0xferrous/agent-box/blob/main/docs/src/how-to/agent-box/use-profiles.md).
- **Modes.**
  - `ab spawn --local` mounts the current directory as it is, including
    untracked and gitignored files.
  - `ab new <repo> -s <session> --git`, then `ab spawn -s <session> --git`,
    creates a Git worktree with tracked files only.
  - Without `--git`, sessions are Jujutsu workspaces.
  - `--entrypoint <cmd> -c=<arg>` runs a one-off command instead of the agent.
- **Portal.** agent-box also ships Portal, which brokers selected host
  operations (clipboard, `gh` and others) to the container over a Unix socket
  under a policy. It is configured through the Home Manager module
  `homeManagerModules.agent-portal`; there is no NixOS module. Start from
  [choose your path](https://github.com/0xferrous/agent-box/blob/main/docs/src/choose-your-path.md),
  and see [security](security.md#portal).

## nix-darwin and standalone Home Manager

Only the packages layer applies: add the llm-agents.nix input and list agents
in `environment.systemPackages` (nix-darwin) or `home.packages`, with the
cache in the system's Nix settings. The images are Linux only; on macOS they
need a Linux remote builder and a Linux container runtime, which this skill
does not cover. Users of Home Manager as a NixOS module rebuild with
`nixos-rebuild`, never `home-manager switch`.
