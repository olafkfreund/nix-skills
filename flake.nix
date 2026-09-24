{
  description = "Portable Nix skills and declarative Home Manager installation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/d4bff64ad63ff84484ef2204c1328924725c1c82";
    home-manager = {
      url = "github:nix-community/home-manager/cbcbfa2778e0c5653ef349df3ebae8288efac3c0";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      home-manager,
    }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forSystems (
        system:
        import ./nix/packages.nix {
          pkgs = import nixpkgs { inherit system; };
        }
        // {
          docs = import ./nix/docs.nix {
            pkgs = import nixpkgs { inherit system; };
            inherit home-manager;
            module = self.homeManagerModules.default;
          };
        }
      );
      homeManagerModules.default = import ./nix/home-manager.nix;
      templates.agentic-nixos = {
        path = ./templates/agentic-nixos;
        description = "NixOS configuration with coding agents and nix-skills";
        welcomeText = ''
          # NixOS with coding agents and nix-skills

          Next steps (see README.md):

          1. `nixos-generate-config --show-hardware-config > hardware-configuration.nix`
          2. Edit the parts of `configuration.nix` marked CHANGE ME: boot loader, user, agents.
          3. `nixos-rebuild build --flake .#my-machine`, then `sudo nixos-rebuild switch --flake .#my-machine`.
             Home Manager runs as a NixOS module: never use `home-manager switch`.
          4. Start your agent, sign in, check `/skills`, and paste:

                 Use the nix-skills skills. I'm on NixOS and want to set up this machine for
                 agentic coding. Read my system configuration first, tell me what you found,
                 and propose changes as a diff. Do not rebuild, install or run containers
                 until I approve.

          Guide: https://olafkfreund.github.io/nix-skills/how-to/own-machine.html
        '';
      };
      templates.project = {
        path = ./templates/project;
        description = "Project with nix-skills linked for its coding agents (devenv)";
        welcomeText = ''
          # Project with nix-skills for its coding agents

          Next steps (see README.md):

          1. `devenv shell` links the skills in `devenv.nix` into `.claude/skills` and `.agents/skills`.
          2. Start your agent in this directory and check the skills with `/skills`.
          3. Edit `nix-skills.skills` in `devenv.nix`; add a matching pair of lines to `.gitignore`.

          Guide: https://olafkfreund.github.io/nix-skills/how-to/project.html
        '';
      };
      templates.default = self.templates.agentic-nixos;
      checks = forSystems (
        system:
        import ./nix/checks.nix {
          pkgs = import nixpkgs { inherit system; };
          inherit home-manager;
          packages = self.packages.${system};
        }
        // {
          inherit (self.packages.${system}) docs;
        }
      );
    };
}
