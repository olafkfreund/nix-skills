{ ... }: {
  env.SKILL_TEST = "devenv-skill-ok";
  scripts.skill-check.exec = ''printf '%s\n' "$SKILL_TEST"'';
  tasks."skill:check".exec = ''set -eu; test "$SKILL_TEST" = devenv-skill-ok; printf task-ok > task-result'';
  enterTest = ''set -eu; test "$(skill-check)" = devenv-skill-ok; printf test-ok > test-result'';
  cachix.enable = false;
  devenv.warnOnNewVersion = false;
}
