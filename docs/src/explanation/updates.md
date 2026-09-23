# How updates work

Generated references are refreshed by the **Update references** workflow.
Which skills it covers, and when it runs, is on the
[update schedule](../reference/update-schedule.md). It never merges or
installs anything: every refresh becomes a pull request that must pass the
same checks as a human change.

## The pipeline

1. **Generate** (one job per skill, read-only). The updater fetches the
   latest upstream source, regenerates the skill's references and
   `sources.json`, and runs that skill's checks and the unit tests. The
   result is packed into an artifact.
2. **Accept** (publication job). A separate job, starting from the current
   default branch, accepts the artifact only if it is safe. It rejects:
   - a stale base, symlinks, or paths that escape the skill;
   - invalid hashes;
   - changes to hand-written instructions or to the selection of upstream
     files;
   - Nixpkgs evaluator or branch-policy changes, and changes to any other
     skill.

   An artifact with no changes is verified and produces nothing.
3. **Publish.** For a changed skill, the job pushes that skill's fixed
   update branch (for example `automation/home-manager-reference-update`) and
   opens or updates at most one pull request for it, with a report of
   changed inputs, coverage and option or built-in metadata.
4. **Check.** The pull request runs the full **Check** workflow like any
   other: collection and style checks, every provider's regeneration check,
   the flake checks and the distribution builds.
5. **Merge by a person.** `main` is protected: a pull request and a passing
   `collection-check` are required, for administrators too. A maintainer
   reviews the report and merges.

## Why it is built this way

- **Least privilege.** Generation runs with read-only permissions and never
  sees a publishing credential. Only the single publication step that
  pushes and opens the pull request receives `UPDATE_PR_TOKEN`; see the
  [security model](security.md).
- **No silent changes to guidance.** The accept step rejects changes to
  hand-written text, so an upstream change can only ever update generated
  references.
- **Reviewable.** One pull request per skill, with a report, keeps each
  upstream change small and easy to judge or revert.

Design history for this pipeline is in the repository's
[`intent/`](https://github.com/olafkfreund/nix-skills/tree/main/intent),
[`spec/`](https://github.com/olafkfreund/nix-skills/tree/main/spec) and
[`plan/`](https://github.com/olafkfreund/nix-skills/tree/main/plan)
folders, for example issues #43 and #48.
