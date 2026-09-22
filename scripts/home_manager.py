"""Home Manager documentation provider."""

from github_docs import generated_files as _generated_files, main as _main, validate_manifest as _validate

CONFIG = {
    "skill": "home-manager",
    "upstream": "https://github.com/nix-community/home-manager",
    "branch": "master",
    "selection": [
        {"source": "docs/manual/nix-flakes/nixos.md", "output": "references/nixos.md", "title": "NixOS module"},
        {"source": "docs/manual/usage/configuration.md", "output": "references/configuration.md", "title": "Configuration"},
        {"source": "docs/manual/usage/dotfiles.md", "output": "references/dotfiles.md", "title": "Dotfiles"},
        {"source": "docs/manual/usage/modular-services.md", "output": "references/modular-services.md", "title": "Modular services"},
        {"source": "docs/manual/writing-modules.md", "output": "references/writing-modules.md", "title": "Writing modules"},
    ],
}


def generated_files():
    return _generated_files(CONFIG)


def validate_manifest(package):
    return _validate(package, CONFIG)


def main(args):
    return _main(args, CONFIG)
