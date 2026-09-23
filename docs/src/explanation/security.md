# Security model

## What installing a skill does

A skill is text: instructions and references. Installing it links read-only
folders from the Nix store into your agent's skill directory. The Home
Manager module installs no agent, starts no service and never forces over
existing files. Some skills describe commands; agents are told to propose
rebuilds, secret changes or destructive commands and wait for your approval.

## Repository automation

- **Read-only by default.** Every workflow's default token permission is
  read-only. Pull request checks run with no secrets and cannot publish.
- **No privileged pull request triggers.** The repository does not use
  `pull_request_target`.
- **Publication is narrow.** Only one step, in the job that pushes an update
  branch and opens its pull request, receives the `UPDATE_PR_TOKEN` secret.
  Generation, artifact acceptance and checks never see it, and it is not
  stored in the job's git configuration.
- **The token is an accepted risk.** `UPDATE_PR_TOKEN` currently holds a
  classic token with account-wide scopes. Narrowing it to this repository
  only needs a new secret value; see [Narrow the update token](../how-to/update-token.md).
- **Protected main branch.** Changes need a pull request and a passing
  `collection-check`; administrators are included, and force-pushes and
  branch deletion are blocked.
- **Pinned actions.** Every GitHub Action is pinned to a commit hash.
- **The documentation site** is deployed by a job that alone holds the
  Pages permissions; pull requests only build it.

## Running coding agents

An agent running directly on your machine can read what you can read,
including `~/.ssh`, cloud credentials and `.env` files. The
[`nixos-coding-agents` skill](https://github.com/olafkfreund/nix-skills/blob/main/skills/nixos-coding-agents/SKILL.md)
explains what containers and disposable worktrees protect, and what they do
not: anything you mount or pass into them remains readable.
