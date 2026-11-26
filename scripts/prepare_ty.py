"""ty に当てるパッチ（patches/ty.patch）を当てた ruff を vendor/ruff に用意する（Cargo.toml の [patch] がそこを使う）。

    python scripts/prepare_ty.py [取ってくる元]   # 既定は https://github.com/astral-sh/ruff
    python scripts/prepare_ty.py save             # vendor/ruff で直した差分を patches/ty.patch に書く

Cargo.toml の rev の ruff を取ってきて（vendor/ruff が同じ rev なら取ってこない）、パッチを当てる（当たっていれば何もしない）。
パッチが当たらなければ（ty の版を上げて、当てる所のコードが変わったなど）2 で終える。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor" / "ruff"
PATCH = ROOT / "patches" / "ty.patch"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(VENDOR), *args], check=check, text=True, capture_output=True)


def rev() -> str:
    found = re.search(r'rev = "([0-9a-f]{40})"', (ROOT / "Cargo.toml").read_text())
    if found is None:
        raise SystemExit("Cargo.toml に ruff の rev が無い")
    return found.group(1)


def checkout(source: str, wanted: str) -> None:
    if not (VENDOR / ".git").exists():
        VENDOR.mkdir(parents=True, exist_ok=True)
        git("init", "--quiet")
    head = git("rev-parse", "HEAD", check=False).stdout.strip()
    if head == wanted:
        return
    # GitHub はコミットの sha を名指しして取ってこられる。前の rev のパッチは checkout で消える
    git("fetch", "--quiet", "--depth", "1", source, wanted)
    git("checkout", "--quiet", "--force", wanted)
    git("clean", "--quiet", "-fdx")


def apply() -> None:
    if git("apply", "--reverse", "--check", str(PATCH), check=False).returncode == 0:
        return
    applied = git("apply", str(PATCH), check=False)
    if applied.returncode != 0:
        print(applied.stderr, file=sys.stderr)
        raise SystemExit(2)


def save() -> None:
    # 新しく足したファイルも差分に入れる（git diff は追跡していないファイルを出さない）
    git("add", "--intent-to-add", "--all")
    PATCH.parent.mkdir(exist_ok=True)
    PATCH.write_text(git("diff").stdout)


def main() -> None:
    match sys.argv[1:]:
        case ["save"]:
            save()
        case [] | [_]:
            checkout(sys.argv[1] if len(sys.argv) > 1 else "https://github.com/astral-sh/ruff", rev())
            apply()
        case _:
            raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
