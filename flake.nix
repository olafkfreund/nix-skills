{
  description = "Portable Nix skills and declarative Home Manager installation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/d4bff64ad63ff84484ef2204c1328924725c1c82";
    home-manager = {
      url = "github:nix-community/home-manager/cbcbfa2778e0c5653ef349df3ebae8288efac3c0";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, home-manager }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forSystems = nixpkgs.lib.genAttrs systems;
    in {
      packages = forSystems (system: import ./nix/packages.nix {
        pkgs = import nixpkgs { inherit system; };
      });
      homeManagerModules.default = import ./nix/home-manager.nix;
      checks = forSystems (system: import ./nix/checks.nix {
        pkgs = import nixpkgs { inherit system; };
        inherit home-manager;
        packages = self.packages.${system};
      });
    };
}
