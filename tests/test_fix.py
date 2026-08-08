"""One-off indentation repair for backend/tmm_acoustics.py.

Historical patch. The source file no longer needs this fix. Kept only as a
safety-guarded, path-portable record of what was applied. Does nothing unless
explicitly invoked with --apply.
"""
import os
import sys

REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TARGET = os.path.join(REPO_ROOT, "backend", "tmm_acoustics.py")

BACKUP_SUFFIX = ".fix.bak"


def main():
    if "--apply" not in sys.argv:
        print("test_fix.py: historical patch, no-op (pass --apply to re-apply)")
        return 0
    if not os.path.exists(TARGET):
        print(f"test_fix.py: target not found: {TARGET}")
        return 1

    with open(TARGET, "r", encoding="utf-8") as f:
        content = f.read()

    backup_path = TARGET + BACKUP_SUFFIX
    if not os.path.exists(backup_path):
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)

    lines = content.split("\n")
    fixed_lines = []
    for i, line in enumerate(lines):
        if 454 <= i <= 696:
            stripped = line.lstrip()
            if stripped:
                if line.startswith("def ") or line.startswith("@"):
                    if not line.startswith(" " * 4):
                        line = "    " + line.lstrip()
                elif line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                    if not line.startswith("#") and line.strip():
                        line = "    " + line
        fixed_lines.append(line)

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write("\n".join(fixed_lines))
    print("Fixed indentation (backup at", backup_path + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
