from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP = {Path(__file__).resolve(), ROOT / ".git"}
DENY = [
    "/" + "Users/",
    "@" + "andrew.cmu.edu",
    "shawn" + ".xiang",
    "Open" + "Assets",
    "BEGIN " + "PRIVATE KEY",
    "ghp" + "_",
]


def main() -> int:
    findings = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.resolve() in SKIP or ".git" in path.parts:
            continue
        if any(part in {".venv", ".build", "__pycache__"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in DENY:
            if token in text:
                findings.append(f"{path.relative_to(ROOT)}: forbidden private token")
    if findings:
        print("\n".join(findings))
        return 1
    print("privacy check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
