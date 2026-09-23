---
status: approved
issue: 19
spec: spec/2026-09-23-19-review-findings.md
---

# Plan: Harden automated reference updates against review findings

Branch: `fix/19-review-findings`, based on `main` 8660959.
Intent: `intent/2026-09-23-19-review-findings.md`.
Spec: `spec/2026-09-23-19-review-findings.md`.

## Approved decisions

Finding 5 is already satisfied on `main`, so it is not changed. All other
changes fail closed exactly as before. Hashes, limits, publication allowlists
and immutable-policy checks are not relaxed. No new third-party dependencies are
added. Generated skill content must stay byte-identical.

- **D1 (finding 1):** `scripts/wiki.py` `lookup_check` no longer names a
  redirect pair.
  - For every retained record with namespace 0 and a truthy `redirect`, call
    the bundled helper's `route(records, title, True)`.
  - Require no missing target, at least one hop, and
    `record['title'] == hops[-1]['redirect']['title']`.
  - With zero redirects this part passes.
  - The `'rebuild'` search and `'NixOS modules'` window assertions stay.
- **D2 (finding 2):** add `fence_state(line, fence) -> (is_marker, new_fence)`
  to `scripts/update.py`, using the current `prose()` rules:
  - the marker regex is `^[ >\t]*(`{3,}|~{3,})`;
  - a marker opens a fence when none is open;
  - a marker closes the fence only with the same character and at least the
    same length;
  - otherwise the fence is unchanged.

  `prose()` and `section()` both use it. `prose()` still raises
  "Unclosed code fence". `section()` still ignores headings inside an open
  fence.
- **D3 (finding 3):** add `github_json(url)` to `scripts/update.py`.
  - Reject URLs that do not start with `https://api.github.com/`
    (`ValueError`).
  - Send `User-Agent: nix-skills`.
  - If `os.environ.get('GITHUB_TOKEN')` is non-empty, set it with
    `request.add_unredirected_header('Authorization', 'Bearer ' + token)`.
  - Keep `timeout=30` and return `json.load(response)`.

  Call sites:
  - `devenv.api(path)` stays as a one-line wrapper:
    `return github_json('https://api.github.com/repos/cachix/devenv/' + path)`.
  - The `nixpkgs.resolve_revision` compare call uses `github_json(url)`.

  `.github/workflows/update.yml` adds `env: GITHUB_TOKEN: ${{ github.token }}`
  to both update steps of the `generate` job. `check.yml` is not changed.
- **D4 (finding 4):** in `scripts/wiki.py` `extract.start`, a
  `mediawiki/page/redirect` element whose `title` attribute is missing or
  empty raises `ValueError('Redirect without title')`.
- **D6 (finding 6):** in `scripts/wiki.py` `main`, change the line
  `if hash_file(path) != snapshot:` to
  `if args.dump and hash_file(path) != snapshot:`.
- **Stop rule:** if any `update.py --check` output differs from the committed
  references, stop. Do not edit generated files. Revise this plan and ask.

## Steps

Each step is one commit with its tests. Messages use Conventional Commits with
`(#19)`.

1. **D2:** in `scripts/update.py`, add `fence_state` and use it in `prose()`
   and `section()`. In `tests/test_update.py`, add a nested-fence test:
   `section()` finds `## B` after a four-backtick block containing a
   three-backtick line, and `prose()` leaves that block untouched. The existing
   `test_section_and_code_preservation` must pass unchanged.
   → Verify with `python3 -m unittest tests.test_update`, then with
   `python3 scripts/update.py --skill nix-language --check` and
   `--skill devenv-project --check` (network and Nix), and
   `git diff --exit-code`.
2. **D3:** in `scripts/update.py`, add `github_json`. Rewrite `devenv.api` as
   the wrapper, and point the `nixpkgs.resolve_revision` compare call at
   `github_json`. In `tests/test_nixpkgs.py:50,55`, patch
   `nixpkgs.github_json` instead of `urlopen` and `json.load`. In
   `tests/test_update.py`, add tests with `urlopen` patched to capture the
   `Request`:
   - with no token, there is no `Authorization` in `header_items()`;
   - with a token, `Authorization` is only in `unredirected_hdrs`;
   - a non-`api.github.com` URL raises `ValueError`.

   → Verify with `python3 -m unittest tests.test_update tests.test_devenv tests.test_nixpkgs`.
3. **D3 workflow:** in `.github/workflows/update.yml`, add the `GITHUB_TOKEN`
   env to the two update steps (lines 28-31).
   → Verify that the file parses
   (`nix run nixpkgs#yq-go -- '.jobs.generate.steps' .github/workflows/update.yml`
   shows `GITHUB_TOKEN` on both update steps) and that `git diff` touches only
   those steps. `check_collection.py` does not inspect workflows. The full
   check comes from the PR run and the post-merge dispatch.
4. **D1, D4, D6:** make the changes in `scripts/wiki.py`. In
   `tests/test_wiki.py`, add:
   - `lookup_check` passing on records with every redirect removed;
   - `lookup_check` passing when `Storage optimization` redirects to another
     bundled title while `Garbage Collection` is a plain page;
   - a bare `<redirect/>` in `xml()` output raising `ValueError`;
   - `update.py --skill nixos-wiki --dump F --sha256 <recorded snapshot>`,
     where `F` has different bytes, exiting non-zero with
     "Dump SHA-256 mismatch" (via the existing subprocess helper).

   → Verify with `python3 -m unittest tests.test_wiki` and
   `python3 scripts/update.py --skill nixos-wiki --check`.
5. **Full verification:** run the commands under Tests below.
   → Verify that all pass and `git status` is clean.
6. **PR:** push with `git push -u origin fix/19-review-findings`. Open a PR
   with `Closes #19` that links the intent, spec and plan, and follows
   `.github/pull_request_template.md`.
   → Verify that the PR's `Check` workflow is green. After merge, dispatch
   `update.yml` manually and confirm the runs are no-ops or open the normal
   PRs.

## Tests

```sh
python3 scripts/check_collection.py
python3 -m unittest discover -s tests -p 'test_*.py'
for s in nix-language devenv-project home-manager microvm-nix nixpkgs-development nixos-wiki; do
  python3 scripts/check.py --skill "$s"
done
for s in nix-language devenv-project nixpkgs-development nixos-wiki; do
  python3 scripts/update.py --skill "$s" --check
done
git diff --exit-code
```

Expected result: every command exits 0, the unit test count rises by the new
tests, and there is no diff in `skills/`.

Limitation: the network and Nix checks run on one x86_64-linux host. The
authenticated API path is proven only by the post-merge `update.yml` dispatch.

## Rollback

Every step is its own commit. Revert individual commits with `git revert`, or
revert the merge commit of the PR. No generated content, lockfile or consumer
interface changes, so a revert needs no follow-up regeneration.
