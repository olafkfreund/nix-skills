{ config, lib, pkgs, ... }:
let
  cfg = config.programs.nix-skills;
  names = builtins.fromJSON (builtins.readFile ../skills.json);
  packages = import ./packages.nix { inherit pkgs; };
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
    directory = lib.mkOption {
      type = lib.types.addCheck lib.types.str validDirectory;
      default = ".agents/skills";
      description = "Destination relative to the home directory, without dot or parent components.";
    };
  };
  config = lib.mkIf cfg.enable {
    assertions = [ {
      assertion = builtins.length cfg.skills == builtins.length (lib.unique cfg.skills);
      message = "programs.nix-skills.skills must not contain duplicates";
    } ];
    home.file = lib.genAttrs (map (name: "${cfg.directory}/${name}") cfg.skills)
      (target: {
        source = "${packages.${builtins.baseNameOf target}}/share/nix-skills/${builtins.baseNameOf target}";
      });
  };
}
