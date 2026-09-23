# Try it in a demo VM

The demo is a disposable NixOS virtual machine with coding agents and these
skills already installed. It changes nothing on your own system, and
deleting one file resets it.

## What is inside

- **Agents** from [llm-agents.nix](https://github.com/numtide/llm-agents.nix):
  Claude Code (`claude`, unfree), Codex (`codex`) and OpenCode
  (`opencode`).
- **The skills,** installed for Claude Code (`~/.claude/skills`) and Codex
  (`~/.agents/skills`). OpenCode reads both directories, so it sees them
  too without a duplicate copy.
- **Podman** for the sandbox examples in the `nixos-coding-agents` skill,
  and **devenv**.
- **A sample project** in `~/example`, with the start prompt and a small
  Python devenv setup.

There are no API keys or accounts in the image. You sign in or add your own
key inside the VM.

## Requirements

- Linux with KVM (`/dev/kvm`), on x86_64 or aarch64.
- Nix 2.26 or newer with flakes enabled. The demo uses a relative flake
  input, which older versions do not support.
- About 3.8 GiB to download: the VM's closure. The agents are 245 to
  555 MiB each. Accepting the flake's `nixConfig` adds the Numtide binary
  cache.
- 4 GiB of RAM and 4 CPU cores for the VM. Its disk file grows to at most
  16 GiB.

## 1. Start it

```sh
mkdir nix-skills-demo && cd nix-skills-demo
nix run github:olafkfreund/nix-skills?dir=demo
```

The VM starts in your terminal and logs in automatically as `demo` on the
console. The disk file `nix-skills-demo.qcow2` is created in the current
directory.

To use a second terminal, connect over SSH. It is forwarded only to your
own machine's loopback address:

```sh
ssh -p 2222 demo@127.0.0.1   # password: demo
```

The fixed password is safe only because of that loopback forward. Never
forward the port more widely.

## 2. Sign in to an agent

Start the agent you want and follow its sign-in, or export your own key in
the VM, for example `export ANTHROPIC_API_KEY=…` for Claude Code or
`export OPENAI_API_KEY=…` for Codex.

## 3. Check the skills and try the prompt

```sh
cd ~/example
claude          # or codex, or opencode
```

In the agent, run `/skills` (Claude Code, Codex) to see the collection,
then paste the start prompt from `~/example/README.md`. Inside the demo,
the "system configuration" the agent reads is the VM itself.

## 4. Stop and reset

Shut down with `sudo poweroff` inside the VM, or press `Ctrl-a` then `x` in
the console. To start from scratch, delete `nix-skills-demo.qcow2`.

## Change the agents

Clone the repository, edit the `demo.agents` default in `demo/demo.nix`
(choose from `claude-code`, `codex`, `opencode` and `gemini-cli`), and run
`nix run ./demo`. Gemini CLI has no skill directory in the Home Manager
module yet, so it does not get the skills installed.

## Limits

- The demo is a convenience, not a hardened sandbox. It protects your own
  files from the agent, but anything you type or copy into the VM is
  readable inside it.
- It is built only as a VM. `nixos-rebuild` cannot build
  `nixosConfigurations.demo` for real hardware, because it defines no disks
  or bootloader. To set up your own machine, follow
  [Getting started](getting-started.md).
- A test in CI boots this VM and checks the agents and skills on every
  change to the demo, the module or the skills.
