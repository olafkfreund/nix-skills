# NixOS demo system: coding agents from llm-agents.nix with nix-skills installed for them.
# No secrets: users sign in to agents or add their own API keys inside the running VM.
{
  config,
  lib,
  pkgs,
  nix-skills,
  llm-agents,
  ...
}:
let
  cfg = config.demo;
  agentPackages = llm-agents.packages.${pkgs.stdenv.hostPlatform.system};
  has = agent: builtins.elem agent cfg.agents;
  # OpenCode also reads ~/.claude/skills and ~/.agents/skills, so it only gets its
  # own directory when neither is installed; otherwise every skill would appear twice.
  skillAgents =
    lib.optional (has "claude-code") "claude"
    ++ lib.optional (has "codex") "codex"
    ++ lib.optional (has "opencode" && !has "claude-code" && !has "codex") "opencode";
  startPrompt = ''
    Use the nix-skills skills. I'm on NixOS and want to set up this machine for
    agentic coding. Read my system configuration first, tell me what you found,
    and propose changes as a diff. Do not rebuild, install or run containers
    until I approve.
  '';
in
{
  options.demo.agents = lib.mkOption {
    type = lib.types.listOf (
      lib.types.enum [
        "claude-code"
        "codex"
        "opencode"
        "gemini-cli"
      ]
    );
    default = [
      "claude-code"
      "codex"
      "opencode"
    ];
    description = "Coding agents from llm-agents.nix to install in the demo system.";
  };

  config = {
    networking.hostName = "nix-skills-demo";
    system.stateVersion = "26.05";

    nix.settings = {
      experimental-features = [
        "nix-command"
        "flakes"
      ];
      extra-substituters = [ "https://cache.numtide.com" ];
      extra-trusted-public-keys = [
        "niks3.numtide.com-1:DTx8wZduET09hRmMtKdQDxNNthLQETkc/yaX7M4qK0g="
      ];
    };

    virtualisation.podman.enable = true;
    environment.systemPackages = map (agent: agentPackages.${agent}) cfg.agents ++ [
      pkgs.devenv
      pkgs.git
      pkgs.curl
    ];

    # A local demo account; SSH is only forwarded to the host's loopback address.
    users.users.demo = {
      isNormalUser = true;
      extraGroups = [ "wheel" ];
      initialPassword = "demo";
    };
    services.getty.autologinUser = "demo";
    services.openssh.enable = true;

    home-manager.users.demo = {
      imports = [ nix-skills.homeManagerModules.default ];
      programs.nix-skills = {
        enable = true;
        agents = skillAgents;
      };
      home.stateVersion = "26.05";
      home.file."example/README.md".text = ''
        # nix-skills demo project

        Start an agent here (for example `claude`, `codex` or `opencode`), sign in or
        set your own API key, check the skills with `/skills`, then paste:

        ```text
        ${startPrompt}```

        `devenv shell` enters the sample Python environment defined in `devenv.nix`.
      '';
      home.file."example/devenv.nix".text = ''
        { pkgs, ... }:
        {
          languages.python.enable = true;
          packages = [ pkgs.git ];
        }
      '';
      home.file."example/devenv.yaml".text = ''
        inputs:
          nixpkgs:
            url: github:cachix/devenv-nixpkgs/rolling
      '';
    };

    virtualisation.vmVariant.virtualisation = {
      memorySize = 4096;
      cores = 4;
      diskSize = 16384;
      graphics = false;
      forwardPorts = [
        {
          from = "host";
          host.address = "127.0.0.1";
          host.port = 2222;
          guest.port = 22;
        }
      ];
    };
  };
}
