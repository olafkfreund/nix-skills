{ pkgs, ... }:
{
  packages = [ pkgs.python3 pkgs.git pkgs.gh pkgs.zstd pkgs.actionlint pkgs.nix ];
  scripts.check-fast.exec = ''
    set -eu
    python3 scripts/check_collection.py
    python3 -m unittest discover -s tests -p 'test_*.py'
    actionlint
  '';
  scripts.check-providers.exec = ''
    set -eu
    for skill in nix-language devenv-project home-manager microvm-nix nix-darwin nixos-operations nixpkgs-development nixos-wiki; do
      python3 scripts/check.py --skill "$skill"
      python3 scripts/update.py --skill "$skill" --check
    done
  '';
}
