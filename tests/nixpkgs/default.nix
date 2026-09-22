{ source, system }:
let
  pkgs = import (builtins.toPath source) {
    inherit system;
    config = { };
    overlays = [ ];
  };
  inherit (pkgs) lib;
  called = lib.callPackageWith { dependency = 7; } ({ dependency, extra ? 1 }: {
    value = dependency + extra;
  }) { };
  original = pkgs.stdenvNoCC.mkDerivation (finalAttrs: {
    pname = "skill-original";
    version = "1";
    marker = "${finalAttrs.pname}-${finalAttrs.version}";
    dontUnpack = true;
    installPhase = "mkdir -p $out";
  });
  changed = original.overrideAttrs (finalAttrs: previousAttrs: {
    pname = previousAttrs.pname + "-changed";
    version = "2";
  });
  overlays = lib.fixedPoints.composeExtensions
    (final: prev: { skillBase = 3; skillDependent = final.skillBase + 1; })
    (final: prev: { skillBase = prev.skillBase + 4; });
  extended = pkgs.extend overlays;
  modules = lib.evalModules {
    modules = [
      ({ lib, ... }: {
        options.answer = lib.mkOption { type = lib.types.int; default = 1; };
        options.enabled = lib.mkEnableOption "fixture";
        config.enabled = true;
      })
      ({ lib, config, ... }: { config = lib.mkIf config.enabled { answer = 42; }; })
    ];
  };
  selectedSource = lib.fileset.toSource { root = ./src; fileset = ./src/message; };
in
{
  semantics =
    assert called.value == 8;
    assert (called.override { dependency = 9; }).value == 10;
    assert original.marker == "skill-original-1";
    assert changed.marker == "skill-original-changed-2";
    assert extended.skillBase == 7 && extended.skillDependent == 8;
    assert lib.attrsets.attrByPath [ "a" "b" ] 0 { a.b = 5; } == 5;
    assert lib.attrsets.attrByPath [ "missing" ] 9 { } == 9;
    assert lib.attrsets.mapAttrs (_: value: value + 1) { a = 1; } == { a = 2; };
    assert lib.attrsets.mapAttrsToList (name: value: name + value) { b = "2"; a = "1"; } == [ "a1" "b2" ];
    assert lib.attrsets.optionalAttrs false { a = 1; } == { };
    assert lib.attrsets.recursiveUpdate { a.b = 1; a.c = 2; } { a.b = 3; } == { a.b = 3; a.c = 2; };
    assert lib.lists.optionals true [ 1 2 ] == [ 1 2 ];
    assert lib.lists.unique [ 1 2 1 ] == [ 1 2 ];
    assert lib.strings.escapeShellArg "a b" == "'a b'";
    assert lib.strings.concatMapStringsSep "," toString [ 1 2 ] == "1,2";
    assert builtins.readFile (selectedSource + "/message") == "pinned-nixpkgs-ok\n";
    assert builtins.readDir selectedSource == { message = "regular"; };
    assert modules.config.answer == 42;
    assert lib.isFunction pkgs.python3Packages.buildPythonPackage;
    assert lib.isFunction pkgs.python3Packages.buildPythonApplication;
    assert lib.isFunction pkgs.buildNpmPackage;
    assert lib.isFunction pkgs.buildGoModule;
    assert lib.isFunction pkgs.rustPlatform.buildRustPackage;
    true;

  package = pkgs.stdenvNoCC.mkDerivation {
    pname = "nixpkgs-skill-fixture";
    version = "1";
    src = selectedSource;
    doCheck = true;
    preCheck = "printf pre > check-marker";
    checkPhase = ''
      runHook preCheck
      test "$(cat message)" = pinned-nixpkgs-ok
      test "$(cat check-marker)" = pre
      runHook postCheck
    '';
    postCheck = "printf post >> check-marker";
    preInstall = "test \"$(cat check-marker)\" = prepost; printf pre > install-marker";
    installPhase = ''
      runHook preInstall
      mkdir -p "$out"
      cp message "$out/message"
      cp install-marker "$out/hooks"
      runHook postInstall
    '';
    postInstall = "printf post >> \"$out/hooks\"";
  };
  shellApp = pkgs.writeShellApplication {
    name = "nixpkgs-skill-check";
    runtimeInputs = [ pkgs.coreutils ];
    text = ''printf '%s\n' 'shell-helper-ok' '';
  };
}
