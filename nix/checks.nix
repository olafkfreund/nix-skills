{ pkgs, home-manager, packages }:
let
  inherit (pkgs) lib;
  names = builtins.fromJSON (builtins.readFile ../skills.json);
  home = settings: home-manager.lib.homeManagerConfiguration {
    inherit pkgs;
    modules = [ ./home-manager.nix {
      home.username = "skill-test";
      home.homeDirectory = "/home/skill-test";
      home.stateVersion = "26.05";
      programs.nix-skills = settings;
    } ];
  };
  enabled = home { enable = true; };
  subset = home { enable = true; skills = [ (builtins.head names) ]; directory = "test/skills"; };
  disabled = home { };
  fails = settings: !(builtins.tryEval (home settings).activationPackage.drvPath).success;
  links = configuration: lib.filterAttrs (name: _: lib.hasPrefix ".agents/skills/" name)
    configuration.config.home.file;
  valid =
    assert builtins.attrNames (links enabled) == map (name: ".agents/skills/${name}") names;
    assert links disabled == { };
    assert subset.config.home.file."test/skills/${builtins.head names}".force == false;
    assert fails { enable = true; skills = [ "unknown-skill" ]; };
    assert fails { enable = true; skills = [ (builtins.head names) (builtins.head names) ]; };
    assert builtins.all (directory: fails { enable = true; inherit directory; })
      [ "" "/tmp/skills" "../skills" "a/../skills" "a//skills" "./skills" ];
    true;
in
{
  workflows = pkgs.runCommand "check-workflows" { nativeBuildInputs = [ pkgs.actionlint ]; } ''
    cd ${../.}
    actionlint .github/workflows/*.yml
    touch "$out"
  '';
  collection = pkgs.runCommand "check-skill-collection" { nativeBuildInputs = [ pkgs.python3 ]; } ''
    export PYTHONDONTWRITEBYTECODE=1
    python3 ${../.}/scripts/check_collection.py --root ${../.}
    touch "$out"
  '';
  package-contents = pkgs.runCommand "check-skill-package-contents" { } ''
    diff -r ${../skills} ${packages.nix-skills}/share/nix-skills
    ${lib.concatMapStringsSep "\n" (name: ''
      diff -r ${../skills + "/${name}"} ${packages.${name}}/share/nix-skills/${name}
    '') names}
    touch "$out"
  '';
  home-manager = assert valid; pkgs.runCommand "check-skill-home" { } ''
    test -e ${enabled.activationPackage}/activate
    ${lib.concatMapStringsSep "\n" (name: ''
      diff -r ${../skills + "/${name}"} ${enabled.config.home.file.".agents/skills/${name}".source}
    '') names}
    test -f ${subset.config.home.file."test/skills/${builtins.head names}".source}/SKILL.md
    touch "$out"
  '';
}
