# NixOS module: coding agents from llm-agents.nix, with nix-skills installed for them.
# Safe for real machines: it adds no users, passwords, logins, SSH, firewall or boot settings.
{ nix-skills, llm-agents }:
{
  config,
  lib,
  pkgs,
  options,
  ...
}:
let
  cfg = config.nix-skills.agentic;
  agentPackages = llm-agents.packages.${pkgs.stdenv.hostPlatform.system};
  has = agent: builtins.elem agent cfg.agents;
  # OpenCode also reads ~/.claude/skills and ~/.agents/skills, so it only gets its
  # own directory when neither is installed; otherwise every skill would appear twice.
  skillAgents =
    lib.optional (has "claude-code") "claude"
    ++ lib.optional (has "codex") "codex"
    ++ lib.optional (has "opencode" && !has "claude-code" && !has "codex") "opencode";
  withHomeManager = options ? home-manager;
in
{
  options.nix-skills.agentic = {
    enable = lib.mkEnableOption "coding agents from llm-agents.nix with nix-skills installed for them";
    agents = lib.mkOption {
      type = lib.types.listOf (
        lib.types.enum [
          "claude-code"
          "codex"
          "opencode"
          "gemini-cli"
        ]
      );
      default = [ "claude-code" ];
      description = "Coding agents to install from llm-agents.nix.";
    };
    user = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "User whose Home Manager configuration gets the skills; null installs none.";
    };
    cache.enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Add the Numtide binary cache (cache.numtide.com) for the agent packages.";
    };
    podman.enable = lib.mkEnableOption "rootless Podman for sandboxed agents";
    devenv.enable = lib.mkEnableOption "devenv for per-project environments";
  };

  config = lib.mkIf cfg.enable (
    lib.mkMerge [
      {
        assertions = [
          {
            assertion = cfg.user == null || withHomeManager;
            message = "nix-skills.agentic.user needs the Home Manager NixOS module (home-manager.nixosModules.home-manager) imported";
          }
        ];
        environment.systemPackages =
          map (agent: agentPackages.${agent}) cfg.agents
          ++ [
            pkgs.git
            pkgs.curl
          ]
          ++ lib.optional cfg.devenv.enable pkgs.devenv;
        nix.settings.experimental-features = [
          "nix-command"
          "flakes"
        ];
        virtualisation.podman.enable = lib.mkIf cfg.podman.enable true;
      }
      (lib.mkIf cfg.cache.enable {
        nix.settings.extra-substituters = [ "https://cache.numtide.com" ];
        nix.settings.extra-trusted-public-keys = [
          "niks3.numtide.com-1:DTx8wZduET09hRmMtKdQDxNNthLQETkc/yaX7M4qK0g="
        ];
      })
      (lib.optionalAttrs withHomeManager {
        home-manager.users = lib.mkIf (cfg.user != null) {
          ${cfg.user} = {
            imports = [ nix-skills.homeManagerModules.default ];
            programs.nix-skills = {
              enable = true;
              agents = skillAgents;
            };
          };
        };
      })
    ]
  );
}
