{ config, lib, pkgs, ... }:
let
  cfg = config.programs.nix-skills;
  names = builtins.fromJSON (builtins.readFile ../skills.json);
  packages = import ./packages.nix { inherit pkgs; };
  agentDirectories = import ./agent-directories.nix;
  validDirectory = directory:
    directory != "" && !(lib.hasPrefix "/" directory)
    && builtins.all (part: part != "" && part != "." && part != "..")
      (lib.splitString "/" directory);
in
{
  options.programs.nix-skills = {
    enable = lib.mkEnableOption "the selected portable Nix skills";
    skills = lib.mkOption {
      type = lib.types.listOf (lib.types.enum names);
      default = names;
      description = "Skill directories to link; defaults to the complete collection.";
    };
    agents = lib.mkOption {
      type = lib.types.listOf (lib.types.enum (builtins.attrNames agentDirectories));
      default = [ ];
      description = "Agents to install into their native user skill directories.";
    };
    directory = lib.mkOption {
      type = lib.types.addCheck lib.types.str validDirectory;
      default = ".agents/skills";
      description = "Destination relative to the home directory, without dot or parent components.";
    };
  };
  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = builtins.length cfg.skills == builtins.length (lib.unique cfg.skills);
        message = "programs.nix-skills.skills must not contain duplicates";
      }
      {
        assertion = builtins.length cfg.agents == builtins.length (lib.unique cfg.agents);
        message = "programs.nix-skills.agents must not contain duplicates";
      }
      {
        assertion = cfg.agents == [ ] || cfg.directory == ".agents/skills";
        message = "programs.nix-skills.directory cannot be customized when agents are selected";
      }
    ];
    home.file =
      let
        skillFiles = directory:
          lib.genAttrs (map (name: "${directory}/${name}") cfg.skills)
            (target: {
              source = "${packages.${builtins.baseNameOf target}}/share/nix-skills/${builtins.baseNameOf target}";
            });
      in
        if cfg.agents == [ ]
        then skillFiles cfg.directory
        else lib.foldl' (files: agent: files // skillFiles agentDirectories.${agent}) { } cfg.agents;
  };
}
