{
  description = "Disposable NixOS demo VM: coding agents with nix-skills installed";

  nixConfig = {
    extra-substituters = [ "https://cache.numtide.com" ];
    extra-trusted-public-keys = [
      "niks3.numtide.com-1:DTx8wZduET09hRmMtKdQDxNNthLQETkc/yaX7M4qK0g="
    ];
  };

  inputs = {
    # The skills of this same commit (relative path inputs need Nix 2.26 or newer).
    nix-skills.url = "path:..";
    nixpkgs.follows = "nix-skills/nixpkgs";
    home-manager.follows = "nix-skills/home-manager";
    # No follows: llm-agents.nix is built and cached against its own nixpkgs-unstable.
    llm-agents.url = "github:numtide/llm-agents.nix";
  };

  outputs =
    {
      self,
      nixpkgs,
      home-manager,
      nix-skills,
      llm-agents,
    }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forSystems = nixpkgs.lib.genAttrs systems;
      agentic = import ./agentic.nix { inherit nix-skills llm-agents; };
      modules = [
        home-manager.nixosModules.home-manager
        agentic
        ./demo.nix
      ];
      demoFor = system: nixpkgs.lib.nixosSystem { inherit system modules; };
    in
    {
      nixosModules.agentic = agentic;
      nixosConfigurations.demo = demoFor "x86_64-linux";

      packages = forSystems (system: rec {
        vm = (demoFor system).config.system.build.vm;
        default = vm;
      });

      apps = forSystems (system: rec {
        vm = {
          type = "app";
          program = "${self.packages.${system}.vm}/bin/run-nix-skills-demo-vm";
        };
        default = vm;
      });

      checks = forSystems (system: {
        vm-test = import ./test.nix {
          pkgs = nixpkgs.legacyPackages.${system};
          inherit modules;
          skillCount = builtins.length (builtins.fromJSON (builtins.readFile "${nix-skills}/skills.json"));
        };
      });
    };
}
