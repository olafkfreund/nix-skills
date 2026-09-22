{ pkgs }:
let
  names = builtins.fromJSON (builtins.readFile ../skills.json);
  package = selected: pkgs.runCommand "nix-skills" { } ''
    mkdir -p "$out/share/nix-skills"
    ${pkgs.lib.concatMapStringsSep "\n" (name: ''
      cp -R ${../skills + "/${name}"} "$out/share/nix-skills/${name}"
    '') selected}
  '';
in
pkgs.lib.genAttrs names (name: package [ name ]) // {
  nix-skills = package names;
  default = package names;
}
