---
status: approved
issue: 19
intent: intent/2026-09-23-19-review-findings.md
---

# Spec: Harden automated reference updates against review findings

The intent was approved without answers to its two open questions, so this spec
uses the recommended defaults. Reject them here if either is wrong:

- **Finding 1:** the update path checks redirects taken from the retained
  records. It keeps no hard-coded title pair.
- **Finding 3:** only `update.yml` passes the workflow's own `github.token`. No
  new secret is added.

**Finding 5 is already satisfied on `main` (8660959).** The unit tests run once,
in the `collection` job (`.github/workflows/check.yml:45`), and not in the skill
matrix. The review's grep matched that line without showing which job it was in.
No change is made for finding 5.

## Design

### 1. Wiki lookup check is driven by retained data (`scripts/wiki.py`)

`lookup_check` (`scripts/wiki.py:363-375`) no longer names
`Garbage Collection` / `Storage optimization`. For every retained page with
namespace 0 and a non-null `redirect`, it calls the bundled helper's
`route(records, title, True)`, and requires:

- no missing target,
- at least one hop,
- a final record whose title equals the redirect target of the last hop.

With zero retained redirects there is nothing to follow, and the redirect part
passes. `validate_records` (`:242-250`) already requires every primary redirect
to end at a bundled title, so the new check tests the shipped helper and adds no
new policy.

The search (`'rebuild'`) and window (`'NixOS modules'`) assertions stay. Both
titles are part of the immutable `TITLES` policy, so upstream edits cannot
remove them. Redirect-following against a known pair stays covered offline by
the fixture tests in `tests/test_wiki.py` (`test_lookup_and_unicode_pagination`).

### 2. One fence tracker for `prose()` and `section()` (`scripts/update.py`)

The duplicated logic is the root cause, so it is extracted rather than patched
in two places. Add `fence_state(line, fence)`. It returns
`(is_marker, new_fence)` using the existing `prose()` rules (`:90-96`):

- a marker opens a fence when none is open;
- a marker closes the open fence only if it uses the same character and is at
  least as long;
- any other marker inside an open fence changes nothing.

`prose()` and `section()` (`:105-128`) both call it. `prose()` keeps its
"Unclosed code fence" error. `section()` keeps its current behaviour of
ignoring headings inside an unclosed fence, which then surfaces as
"Missing or ambiguous section". `devenv.py` imports `section` and gains the fix
without any change of its own.

### 3. Optional GitHub API token (`scripts/update.py`, `devenv.py`, `nixpkgs.py`, `update.yml`)

Add `github_json(url)` to `update.py`:

- It refuses any URL that does not start with `https://api.github.com/`.
- It sends the existing `User-Agent`.
- It adds `Authorization: Bearer $GITHUB_TOKEN` only when that variable is set
  and non-empty. It uses `Request.add_unredirected_header`, so `urllib` does not
  forward the token on a redirect to another host.
- It keeps `timeout=30` and returns the parsed JSON.

`devenv.api` (`scripts/devenv.py:26-29`) and the compare call
(`scripts/nixpkgs.py:36-38`) use it.

`.github/workflows/update.yml` sets `GITHUB_TOKEN: ${{ github.token }}` on the
two update steps of the `generate` job. That job already has only
`permissions: contents: read`. `check.yml` is unchanged, so PR jobs stay
secret-free as AGENTS.md requires. Without a token, behaviour is identical to
today.

### 4. Malformed redirect metadata is a `ValueError` (`scripts/wiki.py:92-93`)

A `<redirect>` element without a non-empty `title` attribute raises
`ValueError('Redirect without title')` when it is parsed. Line 150 is unchanged.

### 6. Hash the dump once per verification (`scripts/wiki.py:342-344`)

The re-hash runs only for `--dump`: `if args.dump and hash_file(path) != snapshot`.
It must stay for that path. Without it, a wrong `--sha256` equal to the recorded
snapshot would return "Already at this dump snapshot" without verification. For
downloads, `download()` already returns the file's hash, and `read_dump`
verifies it again before parsing. That leaves two hashes instead of three.

## Alternatives rejected

- **Delete the redirect assertion from `lookup_check` and test offline only:**
  this stops exercising the shipped helper on the real retained records before
  publication.
- **Patch only `section()`:** the fence rules would still be duplicated and
  could drift apart again.
- **Retry or back off instead of a token:** this delays failures without
  removing them. A shared runner IP can stay rate-limited for the whole hour.
- **Pass the token in `check.yml` as well:** this conflicts with the rule that
  PR jobs are secret-free. The two `devenv` API calls per PR check are well
  within the limit.
- **Set the header with `headers=`:** `urllib` copies those headers to redirect
  targets, including other hosts.
- **Remove the `:343` re-hash entirely:** this breaks verification of
  `--dump` in the no-op path.

## Risks

- **Finding 2 changes excerpt selection for any upstream text that has
  unbalanced fences.** If current upstream sources have such text, the
  regenerated references change bytes. This is detected by `update.py --check`
  plus `git diff --exit-code` for `nix-language`, `devenv-project` and
  `nixpkgs-development`. If it happens, the change stops and the plan is
  revised; generated content is never edited to match.
- **Finding 1 weakens the check if the wiki drops all its redirects.** That is
  acceptable: `validate_records` still checks redirect integrity, and the
  offline tests still cover route-following.
- **Token leakage:** the token is limited to `api.github.com` and sent as an
  unredirected header. A test covers each of these.
- **Hosts:** only GitHub Actions runners (`ubuntu-24.04`) and maintainers'
  local runs are affected. No consumer install changes.

## Verification

- **Unit tests:** `python3 -m unittest discover -s tests -p 'test_*.py'` passes,
  with new tests for:
  - nested fences in `section()` (four backticks around a three-backtick line,
    then a selectable heading), and `prose()` behaving the same as before;
  - `lookup_check` passing with zero redirects, and passing when the bundled
    redirect points to a different bundled title;
  - `github_json` sending no `Authorization` without a token, sending it as an
    unredirected header with a token, and rejecting URLs outside
    `api.github.com`;
  - a bare `<redirect/>` raising `ValueError`;
  - `--dump` with a mismatched `--sha256` equal to the recorded snapshot still
    failing.
- **Offline checks:** `python3 scripts/check_collection.py`, and
  `python3 scripts/check.py --skill <each>` for all six skills.
- **Byte-identical regeneration:** `python3 scripts/update.py --skill <s> --check`
  for `nix-language`, `devenv-project`, `nixpkgs-development` and `nixos-wiki`
  (network and Nix, run locally), then `git diff --exit-code`.
- **CI:** the PR's `Check` workflow passes. A manual `update.yml` dispatch after
  merge confirms that the token path works as a no-op.
