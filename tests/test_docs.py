from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from docs_catalog import render


MIT_TEXT = "MIT License\n\nPermission is hereby granted, free of charge, to any person\n"


def fixture(root, matrix="skill: [gen-skill]"):
    skills = (("gen-skill", '{"upstream": "https://github.com/owner/repo", "branch": "main", "revision": "0123456789abcdef"}', "LICENSE"),
              ("dump-skill", '{"upstream": "https://dumps.example.org/dump.xml.zst", "snapshot_sha256": "fedcba9876543210"}', "COPYING"),
              ("hand-skill", None, None))
    for name, sources, licence in skills:
        package = root / "skills" / name
        package.mkdir(parents=True)
        (package / "SKILL.md").write_text(f"---\nname: {name}\ndescription: About {name}.\n---\n# X\n")
        if sources:
            (package / "sources.json").write_text(sources)
            (package / licence).write_text(MIT_TEXT)
    (root / "LICENSE").write_text(MIT_TEXT)
    (root / "skills.json").write_text('["dump-skill", "gen-skill", "hand-skill"]')
    workflow = root / ".github/workflows/update.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(f"on:\n  schedule:\n    - cron: '17 6 * * 1'\njobs:\n  generate:\n    strategy:\n      matrix:\n        {matrix}\n")


class DocsCatalogTests(unittest.TestCase):
    def test_renders_overview_and_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            catalog = render(root)["catalog.md"]
            self.assertIn("| Skill | Source | Licence |", catalog)
            self.assertIn("| [gen-skill](#gen-skill) | [owner/repo](https://github.com/owner/repo) | [MIT](", catalog)
            self.assertIn("| [hand-skill](#hand-skill) | Hand-written | Repository licence (MIT) |", catalog)
            self.assertIn("## gen-skill\n\nAbout gen-skill.\n", catalog)
            self.assertIn("branch main at [`0123456789ab`](https://github.com/owner/repo/tree/0123456789abcdef)", catalog)
            self.assertIn("[dumps.example.org](https://dumps.example.org/dump.xml.zst), dump snapshot `sha256:fedcba987654`", catalog)
            self.assertNotIn("/tree/fedcba", catalog)
            self.assertNotIn("- **Source:**", catalog.split("## hand-skill")[1])
            schedule = render(root)["update-schedule.md"]
            self.assertIn("`17 6 * * 1`", schedule)
            self.assertIn("## Refreshed automatically\n\n- `gen-skill`", schedule)
            self.assertIn("reviewed pull requests\n\n- `dump-skill`\n- `hand-skill`", schedule)

    def test_licence_detection(self):
        from docs_catalog import licence_name
        with tempfile.TemporaryDirectory() as tmp:
            for text, expected in (("Apache License\nVersion 2.0, January 2004\n", "Apache-2.0"),
                                   ("GNU LESSER GENERAL PUBLIC LICENSE\nVersion 2.1, February 1999\n", "LGPL-2.1"),
                                   (MIT_TEXT, "MIT")):
                path = Path(tmp) / "LICENSE"
                path.write_text(text)
                self.assertEqual(licence_name(path), expected)
            path.write_text("BSD 3-Clause License\n")
            with self.assertRaises(ValueError):
                licence_name(path)

    def test_rejects_unknown_or_missing_matrix(self):
        for matrix in ("skill: [gen-skill, ghost]", "other: [gen-skill]"):
            with self.subTest(matrix=matrix), tempfile.TemporaryDirectory() as tmp:
                fixture(Path(tmp), matrix)
                with self.assertRaises(ValueError):
                    render(Path(tmp))

    def test_real_repository(self):
        root = Path(__file__).resolve().parents[1]
        pages = render(root)
        catalog = pages["catalog.md"]
        overview = [l for l in catalog.splitlines() if l.startswith("| [")]
        self.assertEqual(len(overview), 10)
        self.assertEqual(catalog.count("\n## "), 10)
        for name, count in (("[Apache-2.0]", 1), ("[LGPL-2.1]", 1), ("[MIT]", 6), ("Repository licence (MIT)", 2)):
            self.assertEqual(sum(name in l for l in overview), count, name)
        self.assertNotIn("/tree/", catalog.split("## nixos-wiki")[1].split("\n## ")[0])
        self.assertEqual(pages["update-schedule.md"].split("## Changed only")[0].count("\n- `"), 8)


class CheckDocsTests(unittest.TestCase):
    def tree(self, root, extra=None):
        (root / "guide").mkdir(parents=True, exist_ok=True)
        (root / "SUMMARY.md").write_text("# Summary\n\n- [Intro](index.md)\n- [Guide](guide/page.md)\n")
        (root / "index.md").write_text("# Intro\n\nSee [the guide](guide/page.md#details) and [site](https://example.org).\n")
        (root / "guide/page.md").write_text("# Page\n\n## Details\n\n```nix\npkgs.foo-bar\n```\n")
        for name, text in (extra or {}).items():
            (root / name).write_text(text)

    def test_valid_tree_passes(self):
        from check_docs import validate
        with tempfile.TemporaryDirectory() as tmp:
            self.tree(Path(tmp))
            self.assertEqual(validate(tmp), ["SUMMARY.md", "guide/page.md", "index.md"])

    def test_rejects_broken_links_anchors_unlisted_pages_and_style(self):
        from check_docs import validate
        for extra in ({"index.md": "# Intro\n\n[x](missing.md)\n"},
                      {"index.md": "# Intro\n\n[x](guide/page.md#absent)\n"},
                      {"orphan.md": "# Orphan\n"},
                      {"guide/page.md": '# Page\n\n```nix\npkgs."foo-bar"\n```\n'},
                      {"SUMMARY.md": "# Summary\n\n- [Intro](index.md)\n- [Guide](guide/page.md)\n- [Gone](gone.md)\n"}):
            with self.subTest(extra=list(extra)), tempfile.TemporaryDirectory() as tmp:
                self.tree(Path(tmp), extra)
                with self.assertRaises(ValueError):
                    validate(tmp)


if __name__ == "__main__":
    unittest.main()
