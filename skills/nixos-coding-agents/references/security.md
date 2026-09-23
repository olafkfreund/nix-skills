# Security

Containers reduce what an agent can reach. They are not a hard security
boundary against a determined attacker, and they protect nothing that is
deliberately passed in. Say plainly which layer the user is on and what it
leaves exposed.

## What each layer protects

| Layer | The agent can reach | Protected |
|---|---|---|
| Host install (`nix run`, packages) | Everything the user can: `~/.ssh`, `~/.aws`, browser profiles, every repository, the network | Nothing beyond normal user permissions |
| agent-images container | The mounted project, anything passed with `-e`, the network | Everything not mounted |
| agent-box `--local` | The whole current directory, including untracked and gitignored files such as `.env` | Everything outside that directory |
| agent-box `--git` worktree | Tracked files in a fresh worktree, plus `env_passthrough` | Gitignored and untracked files, the original checkout |

## What passing things in gives away

- **Environment variables.** Every name in `env_passthrough`, or passed with
  `-e`, is readable by the agent, and by anything the agent runs. Pass only
  the provider key the agent needs, prefer a key scoped to this use with a
  spending limit, and prefer short-lived tokens.
- **Sockets and credentials.** Never forward these by default:
  - `SSH_AUTH_SOCK`: the agent can use every loaded SSH key;
  - `GH_TOKEN` or `~/.config/gh`: it can act as you on GitHub;
  - cloud credentials: it can act as you in that account;
  - the GPG agent socket: it can sign as you.

  If the user asks for one, name exactly what it grants, and prefer a narrow
  alternative such as a deploy key or a fine-grained token for one
  repository.
- **Mounts.** A writable mount can be changed or deleted by the agent. Mount
  the project only, never `$HOME`, and mount reference material read-only
  (`:ro`).
- **The network.** The container has network access by default, so the agent
  can send anything it can read. Treat anything the agent can read as
  potentially disclosed.

## The nixpkgs unfree check does not apply

llm-agents.nix redefines nixpkgs' `unfree` licence with `free = true`, on
purpose, so its packages evaluate without `allowUnfree`. This holds for both
the flake packages and the overlay. As a result:

- `allowUnfree = false`, the default, does not stop an unfree agent from being
  installed;
- `allowUnfreePredicate` has no effect on these packages;
- `meta.license.free` reads `true` even for unfree agents.

Where policy restricts unfree software, check `meta.license.shortName`
(`"unfree"`) or `meta.license.redistributable` for each agent before adding
it, and review additions to the configuration.

## Supply chain

- **Daily updates.** Many agents are prebuilt vendor binaries that change
  daily. Pin the llm-agents.nix input in committed configurations, update it
  deliberately with `nix flake update llm-agents`, and read the `flake.lock`
  diff. `nix run github:…` without a lock fetches whatever is current.
- **Binaries cannot be audited.** Where auditing matters, prefer an agent
  built from source; the package list shows which are.
- **Caches.** Adding `cache.numtide.com` to `nix.settings` trusts its key to
  sign what the system runs. Adding substituters or keys needs the user's
  authorization.
- **nixpkgs coupling.** Following nixpkgs onto a stable release breaks the
  flake eventually and loses cache hits. Leave `follows` unset unless the
  system is on nixpkgs-unstable.

## Image trust policy

On NixOS, `/etc/containers/policy.json` defaults to skopeo's policy, which
accepts any image from any source. That is acceptable for images built locally
from a pinned flake and loaded with `podman load`. It is not a sound default
for a team that pulls images from registries; restrict it with
`virtualisation.containers.policy`, as in [setup](setup.md#rootless-podman-on-nixos).

## Nix inside the container

- **No build sandbox.** Nix builds inside the container run with
  `sandbox = false`, so they are not hermetic.
- **Sharing the host store read-only** lets the agent run anything already in
  it, and read any secret that was ever copied into the store.
- **Forwarding the Nix daemon socket** lets the agent build and add anything
  to the host store through the host daemon. If the user is a trusted user of
  that daemon, this is close to root on the host. Do not suggest it without
  saying so.

Details are in agent-images'
[using Nix inside containers](https://github.com/nothingnesses/agent-images#using-nix-inside-containers).

## Portal

Portal gives the container selected host operations, such as the clipboard
or `gh`, under a policy. Each allowed operation is a way out of the sandbox.
Start from a policy that denies everything and allow operations one at a
time, reads first. Allow anything that writes or acts as the user only after
checking what the policy can restrict in Portal's current documentation.
See the
[agent-box documentation](https://github.com/0xferrous/agent-box/blob/main/docs/src/choose-your-path.md).
