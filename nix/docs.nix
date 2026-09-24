{
  pkgs,
  home-manager,
  module,
}:
let
  inherit (pkgs) lib;
  root = ../.;
  source = lib.fileset.toSource {
    inherit root;
    fileset = lib.fileset.unions [
      ../docs
      ../scripts
      ../skills
      ../skills.json
      ../LICENSE
      ../.github/workflows/update.yml
    ];
  };
  # Evaluate the module the same way nix/checks.nix does, only to read its options.
  home = home-manager.lib.homeManagerConfiguration {
    inherit pkgs;
    modules = [
      module
      {
        home.username = "docs";
        home.homeDirectory = "/home/docs";
        home.stateVersion = "26.05";
      }
    ];
  };
  options = pkgs.nixosOptionsDoc {
    options = home.options.programs.nix-skills;
    transformOptions =
      option:
      option
      // {
        # Point "declared by" at GitHub rather than at a store path.
        declarations = [
          {
            name = "nix/home-manager.nix";
            url = "https://github.com/olafkfreund/nix-skills/blob/main/nix/home-manager.nix";
          }
        ];
      };
  };
in
pkgs.runCommand "nix-skills-docs"
  {
    nativeBuildInputs = [
      pkgs.mdbook
      pkgs.python3
    ];
  }
  ''
    cp -R ${source} work && chmod -R u+w work && cd work
    python3 scripts/docs_catalog.py . docs/src/reference
    { printf '# Home Manager module options\n\nGenerated from `homeManagerModules.default` when this site was built.\n\n'
      cat ${options.optionsCommonMark}
    } > docs/src/reference/options.md
    (cd scripts && python3 check_docs.py ../docs/src)
    mdbook build docs --dest-dir "$out"
  ''
