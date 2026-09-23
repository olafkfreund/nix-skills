# A starting point, not a finished system: fill in the parts marked CHANGE ME.
{ ... }:
{
  # CHANGE ME: generate this for your machine with
  #   nixos-generate-config --show-hardware-config > hardware-configuration.nix
  imports = [ ./hardware-configuration.nix ];

  # CHANGE ME: check the boot loader for your machine (this is the usual UEFI setup).
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  networking.hostName = "my-machine";

  # CHANGE ME: your user. Set a password after installing (`passwd alice`), or use
  # hashedPasswordFile; never commit a password to this file.
  users.users.alice = {
    isNormalUser = true;
    extraGroups = [ "wheel" ];
  };

  nix-skills.agentic = {
    enable = true;
    # Choose from "claude-code" (unfree), "codex", "opencode" and "gemini-cli".
    agents = [ "claude-code" ];
    # Installs the nix-skills skills for this user's agents through Home Manager.
    user = "alice";
    # cache.enable = true;   # Numtide binary cache for the agents (default: true)
    # podman.enable = true;  # rootless Podman for sandboxed agents
    # devenv.enable = true;  # devenv for per-project environments
  };

  home-manager.users.alice.home.stateVersion = "26.05";

  # CHANGE ME: the NixOS release you first installed; do not change it later.
  system.stateVersion = "26.05";
}
