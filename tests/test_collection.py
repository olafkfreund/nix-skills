import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_collection import validate
from check_jobs import validate as validate_jobs
from nix_style import MARKER, findings


def fenced(language, body, marker=False):
    return (MARKER + "\n" if marker else "") + f"```{language}\n{body}\n```\n"


class NixStyleTests(unittest.TestCase):
    def test_flags_unneeded_quotes_and_store_searches(self):
        for body in ('pkgs."foo-bar"', 'packages."x86_64-linux".default', '"foo-bar" = 1;', '{ "a_b" = 1; }'):
            with self.subTest(body=body):
                self.assertEqual([k for k, _ in findings(fenced("nix", body))], ["quoted-name"])
        for body in ("find /nix/store/*foo-* -name x", "ls /nix/store | grep foo", "ls /nix/store/*-openssl*/lib"):
            with self.subTest(body=body):
                self.assertEqual([k for k, _ in findings(fenced("sh", body))], ["store-search"])
        path = "/nix/store/0123456789abcdfghijklmnpqrsvwxyz-foo"
        self.assertEqual([k for k, _ in findings(fenced("nix", f'x = "{path}";'))], ["store-path"])

    def test_allows_required_quotes_values_and_counterexamples(self):
        for body in ('".config/foo" = x;', '"2.0" = x;', '"a.b" = 1;', '"with" = 1;', '"or" = 1;',
                     '"${name}" = 1;', 'description = "foo-bar";', 'x = "a" == "b";', '[ "foo-bar" ]'):
            with self.subTest(body=body):
                self.assertEqual(findings(fenced("nix", body)), [])
        self.assertEqual(findings(fenced("sh", 'pkgs."foo-bar"')), [])
        self.assertEqual(findings(fenced("sh", "find /nix/store/*foo-* -name x", marker=True)), [])
        self.assertEqual(findings('Prose may say pkgs."foo-bar" and find /nix/store.\n'), [])

    def test_validate_fails_authored_and_reports_generated(self):
        from check_collection import generated_findings
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "skills/example-skill"
            (package / "references").mkdir(parents=True)
            (root / "skills.json").write_text('["example-skill"]')
            (package / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: Review example configurations.\n---\n# Guide\n")
            (package / "references/example.md").write_text(fenced("nix", 'x = pkgs."foo-bar";'))
            with self.assertRaisesRegex(ValueError, "quoted-name"):
                validate(root)
            (package / "sources.json").write_text('{"outputs": {"references/example.md": "sha256-x"}}')
            self.assertEqual(validate(root), ["example-skill"])
            self.assertEqual(generated_findings(root), {"quoted-name": 1})


class ReadmeSkillTableTests(unittest.TestCase):
    def test_table_must_match_registry(self):
        from check_collection import check_skill_table
        row = lambda n: f"| [{n}](skills/{n}/SKILL.md) | Purpose | Source |"
        table = lambda ns: "# Title\n\n| Skill | Purpose | Source and licence |\n| --- | --- | --- |\n" + "\n".join(map(row, ns)) + "\n\nMore text.\n"
        check_skill_table(table(["a-skill", "b-skill"]), ["a-skill", "b-skill"])
        for text in (table(["a-skill"]), table(["a-skill", "b-skill", "c-skill"]), "# Title\n\nNo table here.\n"):
            with self.subTest(text=text[:40]), self.assertRaises(ValueError):
                check_skill_table(text, ["a-skill", "b-skill"])


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
