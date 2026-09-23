# Demo-only settings on top of nixosModules.agentic: a throwaway user, automatic
# console login, loopback-only SSH, a sample project and VM sizing. Never use on real hardware.
{ ... }:
let
  startPrompt = ''
    Use the nix-skills skills. I'm on NixOS and want to set up this machine for
    agentic coding. Read my system configuration first, tell me what you found,
    and propose changes as a diff. Do not rebuild, install or run containers
    until I approve.
  '';
in
{
  networking.hostName = "nix-skills-demo";
  system.stateVersion = "26.05";

  nix-skills.agentic = {
    enable = true;
    agents = [
      "claude-code"
      "codex"
      "opencode"
    ];
    user = "demo";
    podman.enable = true;
    devenv.enable = true;
  };

  # A local demo account; SSH is only forwarded to the host's loopback address.
  users.users.demo = {
    isNormalUser = true;
    extraGroups = [ "wheel" ];
    initialPassword = "demo";
  };
  services.getty.autologinUser = "demo";
  services.openssh.enable = true;

  home-manager.users.demo = {
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
}
