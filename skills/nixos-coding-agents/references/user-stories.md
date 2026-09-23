# User stories

Six stories, from the smallest change to the largest. Each has a minimal
configuration or command, a check, and how to undo it. `<agent>` is a package
name from the
[llm-agents.nix list](https://github.com/numtide/llm-agents.nix#available-tools),
such as `claude-code`, `codex`, `gemini-cli` or `opencode`. The full
configuration behind these stories is in [setup](setup.md).

## 1. Try an agent without changing the system

As a new NixOS user, I want to try an agent once, so that I can judge it
before installing anything.

```sh
nix run github:numtide/llm-agents.nix#codex -- --help
nix run github:numtide/llm-agents.nix          # interactive picker
```

**Check:** the agent starts. Nothing is added to the system or the profile.

**Undo:** nothing to undo. The download stays in the store until the next
garbage collection.

This runs on the host with the user's full access. Before pointing it at a
real project, read [security](security.md).

## 2. Install agents declaratively and pinned

As a NixOS administrator, I want selected agents in my configuration, pinned
in `flake.lock`, so that every machine gets the same version and a bad update
rolls back with the generation.

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    llm-agents.url = "github:numtide/llm-agents.nix";
  };

  outputs = { nixpkgs, llm-agents, ... }: {
    nixosConfigurations.myhost = nixpkgs.lib.nixosSystem {
      modules = [
        ./configuration.nix
        ({ pkgs, ... }: {
          environment.systemPackages =
            with llm-agents.packages.${pkgs.stdenv.hostPlatform.system}; [
              claude-code
              codex
            ];
          nix.settings = {
            extra-substituters = [ "https://cache.numtide.com" ];
            extra-trusted-public-keys = [
              "niks3.numtide.com-1:DTx8wZduET09hRmMtKdQDxNNthLQETkc/yaX7M4qK0g="
            ];
          };
        })
      ];
    };
  };
}
```

These are the flake's own packages, built against its pinned nixpkgs, so they
come from the cache. To build them against your nixpkgs instead, use the
overlay:

```nix
{ inputs, pkgs, ... }:
{
  nixpkgs.overlays = [ inputs.llm-agents.overlays.shared-nixpkgs ];
  environment.systemPackages = [ pkgs.llm-agents.claude-code pkgs.llm-agents.codex ];
}
```

`inputs` must reach the module, for example through `specialArgs`. Cache hits
with the overlay need your nixpkgs revision to match the one upstream built
against. With Home Manager, put the same packages in `home.packages`.

Neither route needs `allowUnfree` or an `allowUnfreePredicate`, and neither
is stopped by them. llm-agents.nix deliberately marks its unfree licence as
`free = true` for evaluation, so choose unfree agents by reading their licence
(story 6), not by relying on the nixpkgs unfree check. See
[security](security.md#the-nixpkgs-unfree-check-does-not-apply).

**Check:** `nixos-rebuild build --flake .#myhost`, then
`ls result/sw/bin | grep -E 'claude|codex'`. Nothing is activated yet.

**Undo:** remove the packages and rebuild, or roll back to the previous
generation. Update agents deliberately with
`nix flake update llm-agents` and review the `flake.lock` diff.

## 3. Run an agent that cannot read my secrets

As a developer, I want the agent to see only the project, so that it cannot
read `~/.ssh`, `~/.aws` or other projects' `.env` files.

Enable rootless Podman once, as in [setup](setup.md#rootless-podman-on-nixos).
Then build and load an image, and run it with only the project mounted:

```sh
nix build github:nothingnesses/agent-images#claude-code
podman load < result
cd ~/projects/my-repo
podman run --rm -it --userns=keep-id \
  -v "$PWD":/workspace \
  -e ANTHROPIC_API_KEY \
  localhost/agent-images/claude-code:latest
```

`--userns=keep-id` makes files the agent writes in `/workspace` belong to you.
`-e ANTHROPIC_API_KEY` passes the host's value; the agent can read it, so use
a key scoped to this use.

**Check:** the container sees its own empty home and the project, nothing
else.

```sh
podman run --rm --entrypoint sh -v "$PWD":/workspace \
  localhost/agent-images/claude-code:latest -c 'ls -a ~; ls /home; ls /workspace'
```

**Undo:** `podman rmi localhost/agent-images/claude-code:latest`.

The mounted project is still fully readable and writable, including any
`.env` file in it. Story 4 narrows that further.

## 4. Run three agents on three disposable worktrees

As a reviewer, I want three agents to attempt the same task on separate
branches, so that I can compare their diffs and keep the best.

Install `ab` and write `~/.agent-box.toml` as in
[setup](setup.md#agent-box). Then, from the repository:

```sh
cd ~/projects/my-repo
for s in a b c; do ab new my-repo -s "$s" --git; done
ab spawn -s a --git     # repeat for b and c, each in its own terminal
```

Each session is a Git worktree with tracked files only, so gitignored files
such as `.env` and `result` are not in it.

**Check:** a gitignored file is invisible inside a session.

```sh
ab spawn -s a --git --entrypoint ls -c=".env"   # No such file or directory
git worktree list                               # the three session paths
git -C <session-path> diff
```

**Undo:** remove the sessions with the
[agent-box CLI](https://github.com/0xferrous/agent-box/blob/main/docs/src/reference/agent-box/cli.md)
or `git worktree remove <session-path>`.

Worktree mode needs the image from story 3 and `base_repo_dir` pointing at the
real (not symlinked) parent directory of your repositories. Without `--git`,
agent-box uses Jujutsu workspaces.

## 5. Publish one reproducible team image

As a team lead, I want one image with our agent and toolchain, so that
everyone runs the same thing and new members start in minutes.

```nix
# flake.nix in a team repository
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    llm-agents.url = "github:numtide/llm-agents.nix";
    agent-images.url = "github:nothingnesses/agent-images";
  };

  outputs = { nixpkgs, llm-agents, agent-images, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      mkAgentImage = agent-images.lib.mkAgentImage { inherit pkgs; };
    in {
      packages.${system}.team-agent = mkAgentImage {
        name = "team-agent";
        agent = llm-agents.packages.${system}.claude-code;
        entrypoint = [ "claude" ];
        extraPackages = with pkgs; [ nodejs python3 ];
        gid = 100; # the host's `users` group, for rootless Podman
      };
    };
}
```

Commit `flake.lock` and an `agent-box.example.toml` that each member copies to
`~/.agent-box.toml`, with `image` set to the loaded image name that
`podman load` prints. The other `mkAgentImage` parameters (`basePackages`,
`extraEnv`, `user`, `uid`, `workingDir`, `extraDirectories`, Nix inside the
image) are documented in
[agent-images](https://github.com/nothingnesses/agent-images#custom-images).

**Check:** `nix build .#team-agent --print-out-paths` prints the same store
path on two machines at the same `flake.lock`.

**Undo:** remove the output, and `podman rmi` the loaded image.

## 6. Pick an agent by licence, cost and provider

As a newcomer, I want to narrow 200 agents to two or three, so that I do not
sign up for the wrong service.

Ask, in order:

1. **Which model provider can I use?** An existing subscription or key
   usually decides it. For example, `claude-code` uses Anthropic, `codex`
   uses OpenAI and `gemini-cli` uses Google; `opencode`, `crush` and `goose`
   support several providers, including local models.
2. **Free or unfree licence, source or binary?** The
   [package list](https://github.com/numtide/llm-agents.nix#available-tools)
   shows both. Prefer a free, source-built agent when you need to audit it.
3. **How will I run it?** On the host, in a container, or in parallel
   sessions. Any agent in llm-agents.nix works on the host; agent-images
   builds images for a subset.

**Check:** read the licence label. Use `shortName`, not `free`, which
llm-agents.nix sets to `true` even for unfree agents.

```sh
nix eval github:numtide/llm-agents.nix#claude-code.meta.license.shortName   # "unfree"
nix eval github:numtide/llm-agents.nix#codex.meta.license.spdxId            # "Apache-2.0"
```

**Undo:** nothing to undo. Then try the shortlist with story 1.
