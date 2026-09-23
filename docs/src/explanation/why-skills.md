# Why skills

## The problem

General-purpose AI models learn Nix from a mix of old blog posts, other
distributions and imperative habits. Typical results are:

- `nix-env -i` or `curl | sh` instead of a declarative change;
- editing files that NixOS or Home Manager generate;
- options that no longer exist, or advice for a different release;
- searching `/nix/store` by hand and copying store paths.

## What a skill changes

A skill is a folder with a short `SKILL.md` and linked references. The agent
always sees the skill's one-line description; it loads the full text only
when a request matches. That keeps context small while giving the agent,
at the moment it needs it:

- **authoritative text**, for example the NixOS manual's rebuild chapters
  or the Nix language reference, at a recorded upstream revision;
- **rules** such as "check the user's release first" or "propose the
  rebuild command, do not run it";
- **routing** to the right neighbouring skill.

## Why many small skills

Each skill covers one area: the language, NixOS operations, Home Manager,
nix-darwin, devenv, Nixpkgs packaging, microVMs, the wiki, everyday Nix
workflow, and coding agents on NixOS. Users install only what they need, and
each skill can be updated and reviewed on its own. See the
[skill catalog](../reference/catalog.md).

## Why pinned and versioned

Advice is only correct for a version. Generated references record exactly
which upstream revision they come from, and skills tell the agent to check
the user's actual versions before relying on them. See
[Hand-written and generated references](authored-and-generated.md).
