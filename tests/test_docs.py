from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from docs_catalog import render


def fixture(root, matrix="skill: [gen-skill]"):
    for name, sources in (("gen-skill", '{"upstream": "https://example.org/up", "branch": "main", "revision": "0123456789abcdef"}'),
                          ("hand-skill", None)):
        package = root / "skills" / name
        package.mkdir(parents=True)
        (package / "SKILL.md").write_text(f"---\nname: {name}\ndescription: About {name}.\n---\n# X\n")
        if sources:
            (package / "sources.json").write_text(sources)
            (package / "LICENSE").write_text("MIT\n")
    (root / "skills.json").write_text('["gen-skill", "hand-skill"]')
    workflow = root / ".github/workflows/update.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(f"on:\n  schedule:\n    - cron: '17 6 * * 1'\njobs:\n  generate:\n    strategy:\n      matrix:\n        {matrix}\n")


class DocsCatalogTests(unittest.TestCase):
    def test_renders_generated_and_hand_written_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            pages = render(root)
            self.assertIn("| About gen-skill. | generated from upstream | https://example.org/up | main `0123456789ab` |", pages["catalog.md"])
            self.assertIn("| About hand-skill. | hand-written | — | — | repository licence |", pages["catalog.md"])
            self.assertIn("`17 6 * * 1`", pages["update-schedule.md"])
            self.assertIn("## Refreshed automatically\n\n- `gen-skill`", pages["update-schedule.md"])
            self.assertIn("reviewed pull requests\n\n- `hand-skill`", pages["update-schedule.md"])

    def test_rejects_unknown_or_missing_matrix(self):
        for matrix in ("skill: [gen-skill, ghost]", "other: [gen-skill]"):
            with self.subTest(matrix=matrix), tempfile.TemporaryDirectory() as tmp:
                fixture(Path(tmp), matrix)
                with self.assertRaises(ValueError):
                    render(Path(tmp))

    def test_real_repository(self):
        root = Path(__file__).resolve().parents[1]
        pages = render(root)
        self.assertEqual(pages["catalog.md"].count("/SKILL.md) |"), 10)
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
