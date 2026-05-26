"""Final submission hygiene checker.

Run from the project root:
    python scripts/submission_check.py
"""
from __future__ import annotations

from pathlib import Path
import fnmatch
import subprocess


ROOT = Path(__file__).resolve().parents[1]
WARN_PATTERNS = [
    ".env",
    "backend/.env",
    "crm.db",
    "backend/crm.db",
    "*.db",
    "venv",
    "backend/venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def find_existing() -> list[str]:
    warnings: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        name = path.name
        relative = rel(path)
        for pattern in WARN_PATTERNS:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(relative, pattern):
                warnings.append(relative)
                break
    return sorted(set(warnings))


def run_git(args: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        return completed.returncode, (completed.stdout + completed.stderr).strip()
    except FileNotFoundError:
        return 127, "git is not installed or not on PATH"


def tracked_risky_files() -> list[str] | None:
    code, output = run_git(["rev-parse", "--is-inside-work-tree"])
    if code != 0:
        return None
    code, output = run_git(["ls-files"])
    if code != 0:
        return []
    risky = []
    for line in output.splitlines():
        path = Path(line)
        normalized = path.as_posix()
        for pattern in WARN_PATTERNS:
            if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(normalized, pattern):
                risky.append(normalized)
                break
    return sorted(set(risky))


def main() -> int:
    print("Submission hygiene check")
    print("========================")

    existing = find_existing()
    if existing:
        print("\nGenerated/secret-like files currently present:")
        for item in existing:
            print(f"  WARNING: {item}")
        print("\nThese may be fine locally, but do not include them in the final ZIP or Git commit.")
    else:
        print("\nNo generated/secret-like files found in the working tree scan.")

    code, status = run_git(["status", "--short"])
    if code == 0:
        print("\nGit status:")
        print(status or "  clean")
    else:
        print("\nGit is not initialized or unavailable here.")
        print("Manual check: initialize/push from a Git repo and verify ignored files before submission.")

    risky = tracked_risky_files()
    if risky is None:
        print("\nTracked-file check skipped because this folder is not a Git repository.")
        print('Manual command after Git init: git ls-files | findstr /i ".env crm.db venv __pycache__"')
        return 0

    if risky:
        print("\nRisky files are tracked by Git:")
        for item in risky:
            print(f"  ERROR: {item}")
        return 1

    print("\nNo risky files are tracked by Git.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
