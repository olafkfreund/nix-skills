# devenv module: link whole nix-skills skill folders into a project's agent skill directories.
# Import it from a project's devenv.yaml:
#   inputs.nix-skills = { url = "github:olafkfreund/nix-skills"; flake = false; }
#   imports: [ nix-skills/devenv ]
# It only manages these links; devenv leaves any existing file or directory at a path alone.
{ config, lib, ... }:
let
  cfg = config.nix-skills;
  names = builtins.fromJSON (builtins.readFile ../skills.json);
  paths = lib.concatMap (dir: map (skill: "${dir}/${skill}") cfg.skills) cfg.directories;
in
{
  options.nix-skills = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Link the selected nix-skills skills into the project's agent skill directories.";
    };
    skills = lib.mkOption {
      type = lib.types.listOf (lib.types.enum names);
      default = [
        "nix-workflow"
        "nix-language"
        "devenv-project"
      ];
      description = "Skills to link, by name from the nix-skills catalog.";
    };
    directories = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      # Claude Code reads .claude/skills; Codex and Antigravity read .agents/skills; OpenCode reads both.
      default = [
        ".claude/skills"
        ".agents/skills"
      ];
      description = "Project directories to link the skills into.";
    };
  };

  config = lib.mkIf cfg.enable {
    files = lib.listToAttrs (
      lib.concatMap (
        dir:
        map (skill: {
          name = "${dir}/${skill}";
          value.source = ../skills + "/${skill}";
        }) cfg.skills
      ) cfg.directories
    );

    # Links point into /nix/store; remind (never fail) when one is not git-ignored.
    enterShell = ''
      if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        for path in ${lib.escapeShellArgs paths}; do
          git check-ignore -q "$path" || echo "nix-skills: add $path to .gitignore (it links into /nix/store)"
        done
      fi
    '';
  };
}
