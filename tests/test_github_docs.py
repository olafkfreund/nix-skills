import json
from pathlib import Path
import sys
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import github_docs
import home_manager


class GithubDocsTests(unittest.TestCase):
    def test_pin_links_and_preserve_fences(self):
        source = (
            "[next](other.md#part) and [same](#part)\n"
            "[ref]: ../shared.md\n"
            "```nix\n[inside](other.md)\n```\n"
        )
        result = github_docs.pin_links(
            source,
            "docs/manual/usage/configuration.md",
            home_manager.CONFIG["upstream"],
            "a" * 40,
        )
        self.assertIn("/blob/" + "a" * 40 + "/docs/manual/usage/other.md#part", result)
        self.assertIn("/blob/" + "a" * 40 + "/docs/manual/usage/configuration.md#part", result)
        self.assertIn("[ref]: https://github.com/nix-community/home-manager/blob/" + "a" * 40, result)
        self.assertIn("[inside](other.md)", result)

    def test_pin_links_rejects_escape(self):
        with self.assertRaises(ValueError):
            github_docs.pin_links(
                "[bad](../../../../outside.md)\n",
                "docs/manual/usage/configuration.md",
                home_manager.CONFIG["upstream"],
                "a" * 40,
            )

    def test_source_path_rejects_missing_and_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            (source / "ok.md").write_text("ok")
            self.assertEqual(github_docs.source_path(source, "ok.md").read_text(), "ok")
            with self.assertRaises(ValueError):
                github_docs.source_path(source, "missing.md")
            with self.assertRaises(ValueError):
                github_docs.source_path(source, "../outside.md")

    def test_generate_is_deterministic_and_hashes_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            old = {
                "upstream": home_manager.CONFIG["upstream"],
                "branch": home_manager.CONFIG["branch"],
                "revision": "a" * 40,
                "selection": home_manager.CONFIG["selection"],
            }
            for item in old["selection"]:
                path = source / item["source"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# " + item["title"] + "\n\nExample.\n")
            (source / "LICENSE").write_text("license\n")
            first, manifest = github_docs.generate(old, home_manager.CONFIG, old["revision"], source)
            second, again = github_docs.generate(old, home_manager.CONFIG, old["revision"], source)
            self.assertEqual(first, second)
            self.assertEqual(manifest, again)
            self.assertEqual(set(manifest["outputs"]), set(home_manager.generated_files()) - {"sources.json"})
            self.assertEqual(json.loads(first["sources.json"]), manifest)

    def test_branch_resolution_requires_one_exact_ref(self):
        old = {"upstream": home_manager.CONFIG["upstream"], "branch": "master", "revision": "a" * 40}
        with patch.object(github_docs, "run", return_value="b" * 40 + "\trefs/heads/master"):
            self.assertEqual(github_docs.resolve_revision(old, old["upstream"], "master"), "b" * 40)
        with patch.object(github_docs, "run", return_value=""):
            with self.assertRaises(ValueError):
                github_docs.resolve_revision(old, old["upstream"], "master")

    def test_latest_noop_does_not_fetch_source(self):
        manifest = json.loads((Path(__file__).parents[1] / "skills/home-manager/sources.json").read_text())
        args = Namespace(revision=None, latest=True, check=False, release=None, dump=None, sha256=None)
        with patch.object(github_docs, "resolve_revision", return_value=manifest["revision"]):
            with patch.object(github_docs, "pinned_source", side_effect=AssertionError("unexpected fetch")):
                github_docs.main(args, home_manager.CONFIG)

    def test_check_uses_recorded_revision_not_live_branch(self):
        manifest = json.loads((Path(__file__).parents[1] / "skills/home-manager/sources.json").read_text())
        args = Namespace(revision=None, latest=False, check=True, release=None, dump=None, sha256=None)
        with patch.object(github_docs, "run", side_effect=AssertionError("live branch lookup")), \
             patch.object(github_docs, "pinned_source", side_effect=RuntimeError("stop")) as source:
            with self.assertRaisesRegex(RuntimeError, "stop"):
                github_docs.main(args, home_manager.CONFIG)
        source.assert_called_once_with(home_manager.CONFIG["upstream"], manifest["revision"])


if __name__ == "__main__":
    unittest.main()
