{ pkgs, inputs, ... }:
{
  # Skills linked into .claude/skills and .agents/skills for this project's agents.
  # All skills: devenv-project, home-manager, microvm-nix, nix-darwin, nix-language,
  # nix-workflow, nixos-coding-agents, nixos-operations, nixos-wiki, nixpkgs-development
  # (https://olafkfreund.github.io/nix-skills/reference/catalog.html).
  # Add a matching pair of lines to .gitignore for every skill you add.
  nix-skills.skills = [
    "nix-workflow"
    "nix-language"
    "devenv-project"
  ];

  # Optional: pin a coding agent in this project's shell. Uncomment the llm-agents
  # input in devenv.yaml first; choose from claude-code, codex, opencode, gemini-cli.
  # packages = [ inputs.llm-agents.packages.${pkgs.stdenv.hostPlatform.system}.claude-code ];

  # The project's own tooling, for example:
  # languages.python.enable = true;
}
