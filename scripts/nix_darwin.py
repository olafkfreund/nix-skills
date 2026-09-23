"""nix-darwin documentation provider."""

from github_docs import generated_files as _generated_files, main as _main, validate_manifest as _validate

CONFIG = {
    "skill": "nix-darwin",
    "upstream": "https://github.com/nix-darwin/nix-darwin",
    "branch": "master",
    "selection": [
        {"source": "README.md", "output": "references/readme.md", "title": "nix-darwin README"},
    ],
}


def generated_files():
    return _generated_files(CONFIG)


def validate_manifest(package):
    return _validate(package, CONFIG)


def main(args):
    return _main(args, CONFIG)
