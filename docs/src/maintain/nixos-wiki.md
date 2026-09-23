# NixOS Wiki maintenance and lookup

The wiki skill bundles 17 reviewed English topic pages, the copyright policy and
latest template source, with one retained revision per page. It preserves raw
wikitext, examples and notices; it does not render MediaWiki templates or mirror
the whole wiki. Search excerpts can omit caveats, so read page notices and complete
examples before use. Advice still needs checking against the consumer's actual pin.

```sh
python3 skills/nixos-wiki/scripts/wiki.py search 'rebuild'
python3 skills/nixos-wiki/scripts/wiki.py show 'Nixos-rebuild'
python3 skills/nixos-wiki/scripts/wiki.py show 'Garbage Collection' --follow
python3 skills/nixos-wiki/scripts/wiki.py show 'Template:Warning'
python3 scripts/check.py --skill nixos-wiki
python3 scripts/update.py --skill nixos-wiki --check
```

Lookup and `--check` need only Python 3.10+, work offline, and never execute wiki
examples. `show` limits each original-text window to 200 lines / 16 KiB and gives
continuation arguments (`--start`, `--offset`); `--lines` can request a smaller
window. Template search requires `--templates`. Missing redirect targets are
labeled as live, unpinned links; revision citations do not pin templates used by
the live website's renderer. Other agents may read individual JSON records instead.

Ingestion additionally requires `zstd`; CI supplies it from a fixed Nixpkgs commit.
No global installation is needed. On a task branch or disposable copy:

```sh
python3 scripts/update.py --skill nixos-wiki --latest
python3 scripts/update.py --skill nixos-wiki --dump /path/to/wikidump.xml.zst --sha256 <expected-sha256>
```

The updater bounds download/decompression/XML processing, rejects DTD/entities,
and verifies the compressed hash and decoder success. It rejects regressions,
mutated revision identities, missing primary titles, broken primary redirects and
copyright-policy changes. Same-dump and irrelevant-history/recompression changes
are no-ops; advanced retained revisions with identical text are reported as
provenance-only updates. Changes require review, including template changes.

Retained JSON contains the exact consumed text and metadata, allowing offline
reproduction after the moving dump URL changes. The compressed checksum identifies
the original acquisition; the subset cannot reconstruct the full historical XML.
No full dump, contributor identities/history or media are distributed. Source
origin, selection, namespace/size/schema policy and copyright-policy identity are
immutable to automation, as are SKILL.md and the package's lookup helper. Restore
the complete package from a reviewed repository commit to roll back.
