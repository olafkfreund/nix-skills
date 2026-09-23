# Offline VM test of the demo (nixosModules.agentic plus demo settings): agents start,
# skills are installed for Claude Code and Codex only.
{
  pkgs,
  modules,
  skillCount,
}:
pkgs.testers.runNixOSTest {
  name = "nix-skills-demo";
  nodes.machine = {
    imports = modules;
  };
  testScript = ''
    machine.wait_for_unit("multi-user.target")
    machine.wait_for_unit("home-manager-demo.service")

    def as_demo(command):
        return machine.succeed(f"su - demo -c '{command}'")

    for binary in ["claude", "codex", "opencode"]:
        as_demo(f"timeout 60 {binary} --version")

    for directory in [".claude/skills", ".agents/skills"]:
        count = int(as_demo(f"ls ~/{directory} | wc -l").strip())
        assert count == ${toString skillCount}, f"{directory}: {count} skills"
        as_demo(f"test -r ~/{directory}/nix-workflow/SKILL.md")

    as_demo("test ! -e ~/.config/opencode/skills")
    as_demo("podman --version")
    as_demo("devenv version")
    as_demo("test -r ~/example/README.md")
  '';
}
