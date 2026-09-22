"""microvm.nix documentation provider."""

from github_docs import generated_files as _generated_files, main as _main, validate_manifest as _validate

CONFIG = {
    "skill": "microvm-nix",
    "upstream": "https://github.com/microvm-nix/microvm.nix",
    "branch": "main",
    "selection": [
        {"source": "doc/src/intro.md", "output": "references/intro.md", "title": "Introduction"},
        {"source": "doc/src/declaring.md", "output": "references/declaring.md", "title": "Declaring VMs"},
        {"source": "doc/src/declarative.md", "output": "references/declarative.md", "title": "Declarative deployment"},
        {"source": "doc/src/host.md", "output": "references/host.md", "title": "Host integration"},
        {"source": "doc/src/host-systemd.md", "output": "references/host-systemd.md", "title": "Host systemd"},
        {"source": "doc/src/options.md", "output": "references/options.md", "title": "Options"},
        {"source": "doc/src/simple-network.md", "output": "references/simple-network.md", "title": "Simple networking"},
        {"source": "doc/src/routed-network.md", "output": "references/routed-network.md", "title": "Routed networking"},
        {"source": "doc/src/interfaces.md", "output": "references/interfaces.md", "title": "Network interfaces"},
        {"source": "doc/src/shares.md", "output": "references/shares.md", "title": "Shares"},
    ],
}


def generated_files():
    return _generated_files(CONFIG)


def validate_manifest(package):
    return _validate(package, CONFIG)


def main(args):
    return _main(args, CONFIG)
