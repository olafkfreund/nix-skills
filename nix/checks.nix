{ pkgs, home-manager, packages }:
let
  inherit (pkgs) lib;
  names = builtins.fromJSON (builtins.readFile ../skills.json);
  agentDirectories = import ./agent-directories.nix;
  agentNames = builtins.attrNames agentDirectories;
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
  singleAgent = home { enable = true; skills = [ (builtins.head names) ]; agents = [ "claude" ]; };
  allAgents = home { enable = true; agents = agentNames; };
  disabled = home { };
  fails = settings: !(builtins.tryEval (home settings).activationPackage.drvPath).success;
  links = directory: configuration: lib.filterAttrs (name: _: lib.hasPrefix "${directory}/" name)
    configuration.config.home.file;
  valid =
    assert builtins.attrNames (links ".agents/skills" enabled) == map (name: ".agents/skills/${name}") names;
    assert links ".agents/skills" disabled == { };
    assert subset.config.home.file."test/skills/${builtins.head names}".force == false;
    assert builtins.attrNames (links ".claude/skills" singleAgent)
      == [ ".claude/skills/${builtins.head names}" ];
    assert builtins.attrNames (lib.filterAttrs
      (name: _: builtins.any (agent: lib.hasPrefix "${agentDirectories.${agent}}/" name) agentNames)
      allAgents.config.home.file)
      == lib.sort builtins.lessThan (builtins.concatMap
        (agent: map (name: "${agentDirectories.${agent}}/${name}") names) agentNames);
    assert fails { enable = true; skills = [ "unknown-skill" ]; };
    assert fails { enable = true; skills = [ (builtins.head names) (builtins.head names) ]; };
    assert fails { enable = true; agents = [ "unknown-agent" ]; };
    assert fails { enable = true; agents = [ "claude" "claude" ]; };
    assert fails { enable = true; agents = [ "claude" ]; directory = "custom/skills"; };
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
  devenv-module =
    let
      # Minimal stand-in for devenv's files and enterShell options.
      stub = {
        options.files = lib.mkOption {
          type = lib.types.attrsOf (lib.types.submodule { options.source = lib.mkOption { }; });
          default = { };
        };
        options.enterShell = lib.mkOption { type = lib.types.lines; default = ""; };
      };
      evaluate = settings: (lib.evalModules { modules = [ stub ../devenv/devenv.nix { nix-skills = settings; } ]; }).config;
      defaults = evaluate { };
      expected = lib.concatMap (dir: map (skill: "${dir}/${skill}") [ "nix-workflow" "nix-language" "devenv-project" ])
        [ ".claude/skills" ".agents/skills" ];
      sourcesMatch = lib.all (key: baseNameOf (toString defaults.files.${key}.source) == baseNameOf key) expected;
      unknownFails = !(builtins.tryEval (builtins.deepSeq (evaluate { skills = [ "not-a-skill" ]; }).files true)).success;
    in
    assert lib.sort lib.lessThan (lib.attrNames defaults.files) == lib.sort lib.lessThan expected;
    assert sourcesMatch;
    assert unknownFails;
    pkgs.runCommand "check-devenv-module" { } "touch $out";
  home-manager = assert valid; pkgs.runCommand "check-skill-home" { } ''
    test -e ${enabled.activationPackage}/activate
    ${lib.concatMapStringsSep "\n" (name: ''
      diff -r ${../skills + "/${name}"} ${enabled.config.home.file.".agents/skills/${name}".source}
    '') names}
    test -f ${subset.config.home.file."test/skills/${builtins.head names}".source}/SKILL.md
    touch "$out"
  '';
}
