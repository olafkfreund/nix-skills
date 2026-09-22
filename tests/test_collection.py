import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_collection import validate
from check_jobs import validate as validate_jobs


class CollectionTests(unittest.TestCase):
    def test_required_job_results(self):
        good = {name: {"result": "success"} for name in ("check", "collection", "distribution")}
        validate_jobs(good)
        for name in good:
            for result in ("failure", "cancelled", "skipped", None):
                with self.subTest(job=name, result=result), self.assertRaises(ValueError):
                    validate_jobs(good | {name: {"result": result}})
        with self.assertRaises(ValueError):
            validate_jobs({})

    def test_generic_contribution_and_rejected_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "skills/example-skill"
            package.mkdir(parents=True)
            registry = root / "skills.json"
            registry.write_text('["example-skill"]')
            original = "---\nname: example-skill\ndescription: Review example configurations.\n---\n# Guide\n\nRead [details](reference.md#details).\n"
            entry = package / "SKILL.md"
            entry.write_text(original)
            (package / "reference.md").write_text("# Details\nUseful instructions.\n")
            # Valid helpers are packaged as data, never imported/executed here.
            (package / "helper.py").write_text("raise RuntimeError('must not run')\n")
            self.assertEqual(validate(root), ["example-skill"])
            for bad in ([], {}, ["Example"], ["../example-skill"], ["x" * 65], ["default"], ["nix-skills"],
                        ["example-skill", "example-skill"], ["missing"],
                        ["z", "example-skill"], [True]):
                with self.subTest(registry=bad):
                    registry.write_text(json.dumps(bad))
                    with self.assertRaises(ValueError):
                        validate(root)
            registry.write_text('["example-skill"]')
            for bad in ("no frontmatter", original.replace("name: example-skill", "name: other"),
                        original.replace("description: Review example configurations.", "description: >"),
                        original.replace("description: Review example configurations.", "description: [invalid, metadata]"),
                        original.replace("description: Review example configurations.", "description: false"),
                        original.replace("description: Review example configurations.", "description: TRUE"),
                        original.replace("description: Review example configurations.", "description: Review\ninvalid yaml"),
                        original.replace("description: Review example configurations.", "description: 123"),
                        original.replace("description: Review example configurations.", "description: Review\ndescription:"),
                        original + "\nTODO: finish this\n",
                        original + "\n[bad](../../outside)\n",
                        original + "\n[bad](%2Fetc/passwd)\n",
                        original + "\n[bad](//example.com/file)\n",
                        original + "\n[bad](reference.md#absent)\n",
                        original + "\n[bad](missing.md)\n",
                        original + "\n[bad]: ../../outside\n"):
                with self.subTest(text=bad):
                    entry.write_text(bad)
                    with self.assertRaises(ValueError):
                        validate(root)
            entry.write_text(original + "\n```markdown\n[example](missing.md)\nTODO\n```\n")
            self.assertEqual(validate(root), ["example-skill"])
            (package / "escape").symlink_to(root)
            with self.assertRaises(ValueError):
                validate(root)
