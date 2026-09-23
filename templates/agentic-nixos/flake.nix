{
  description = "NixOS configuration with coding agents and nix-skills";

  inputs = {
    # llm-agents.nix is built and tested against nixpkgs-unstable only.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    # nixosModules.agentic: agents from llm-agents.nix plus the nix-skills skills.
    # Its llm-agents.nix input is deliberately not followed, so agent packages keep
    # hitting the Numtide binary cache. Update with `nix flake update agentic`.
    agentic.url = "github:olafkfreund/nix-skills?dir=demo";
  };

  outputs =
    {
      nixpkgs,
      home-manager,
      agentic,
      ...
    }:
    {
      nixosConfigurations.my-machine = nixpkgs.lib.nixosSystem {
        modules = [
          home-manager.nixosModules.home-manager
          agentic.nixosModules.agentic
          ./configuration.nix
        ];
      };
    };
}
