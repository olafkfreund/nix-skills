"""Flag two common LLM mistakes in Markdown code examples, offline.

- quoted-name: `pkgs."foo-bar"` or `"foo-bar" = …` where the name is a valid
  Nix identifier (Nix manual, language/identifiers) and needs no quotes.
- store-search / store-path: searching `/nix/store` or hard-coding a store path.

A fence directly after `<!-- nix-style: counterexample -->` is skipped.
"""

import re

from update import fence_state

MARKER = "<!-- nix-style: counterexample -->"
KEYWORDS = {"assert", "else", "if", "in", "inherit", "let", "or", "rec", "then", "with"}
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_'-]*")
# A plain string literal used as a name: after `.`, or starting a binding and followed by `=`/`.`.
QUOTED_NAME = re.compile(r'(?:(?<=\.)"([^"\\$]*)")|(?:(?:^|(?<=[{;]))\s*"([^"\\$]*)"(?=\s*(?:=(?!=)|\.)))')
STORE_SEARCH = re.compile(r"\b(?:find|ls|fd|locate)\b.*?/nix/store|/nix/store/\*")
STORE_PATH = re.compile(r"/nix/store/[0-9a-df-np-sv-z]{32}-")


def _unneeded(name):
    return bool(IDENTIFIER.fullmatch(name)) and name not in KEYWORDS


def findings(text):
    """Return (kind, line) for each problem in fenced code blocks of Markdown text."""
    result, fence, language, skip, previous = [], None, "", False, ""
    for line in text.splitlines():
        marker, new_fence = fence_state(line, fence)
        if marker:
            if fence is None:
                language = line.strip().lstrip("`~").strip().split(" ")[0].lower()
                skip = previous.strip() == MARKER
            fence = new_fence
        elif fence is not None and not skip:
            if language == "nix" and any(
                    _unneeded(m[1] if m[1] is not None else m[2]) for m in QUOTED_NAME.finditer(line)):
                result.append(("quoted-name", line.strip()))
            if STORE_SEARCH.search(line):
                result.append(("store-search", line.strip()))
            elif STORE_PATH.search(line):
                result.append(("store-path", line.strip()))
        previous = line
    return result
