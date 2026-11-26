"""ty の新しい版に道具を合わせる。

    python scripts/follow_ty.py latest          # PyPI の ty の最新の版が今より新しければ、その版を出す（同じなら何も出さない）
    python scripts/follow_ty.py unpublished <数>  # この道具の今の版のファイルが PyPI に <数> だけ無ければ、その版を出す（公開に失敗した版の出し直し）
    python scripts/follow_ty.py update <版>     # その版の ty が指す ruff のコミットに合わせて書き換える

書き換えるのは、Cargo.toml の ruff のコミット・Cargo.lock（そのコミットの ruff のものを写す）・rust-toolchain.toml
（そのコミットの ruff と同じ Rust の版）・pyproject.toml の版と ty の依存・src/main.rs の TY_VERSION。
Cargo.lock は写したあと cargo build が、この道具の依存に合わせて足し引きする（ruff と同じ版はそのまま使う）。
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "ty-mccabe-follow-ty"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def version_tuple(version: str) -> tuple[int, ...]:
    if not re.fullmatch(r"\d+(\.\d+)*", version):
        raise SystemExit(f"数字だけの版でない: {version}")
    return tuple(int(part) for part in version.split("."))


def current_ty() -> str:
    found = re.search(r'"ty==([^"]+)"', (ROOT / "pyproject.toml").read_text())
    if found is None:
        raise SystemExit("pyproject.toml に ty== の依存が無い")
    return found.group(1)


def current_tool() -> str:
    found = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.MULTILINE)
    if found is None:
        raise SystemExit("pyproject.toml に version が無い")
    return found.group(1)


def unpublished(expected: int) -> None:
    version = current_tool()
    try:
        release = json.loads(fetch(f"https://pypi.org/pypi/ty-mccabe/{version}/json"))
    except urllib.error.HTTPError as error:
        # 404 だけが「まだ無い」。ほかの失敗（PyPI が落ちているなど）は、出し直しと取り違えないように止める
        if error.code != 404:
            raise
        print(version)
        return
    # 公開が途中で落ちると、一部のファイルだけが上がっている
    if len(release["urls"]) < expected:
        print(version)


def latest() -> None:
    newest = json.loads(fetch("https://pypi.org/pypi/ty/json"))["info"]["version"]
    if version_tuple(newest) > version_tuple(current_ty()):
        print(newest)


def replace(path: Path, pattern: str, new: str, count: int = 0) -> None:
    text = path.read_text()
    updated, n = re.subn(pattern, new, text, count=count, flags=re.MULTILINE)
    if n == 0:
        raise SystemExit(f"{path.name} に {pattern} が無い")
    path.write_text(updated)


def update(version: str) -> None:
    version_tuple(version)
    content = json.loads(fetch(f"https://api.github.com/repos/astral-sh/ty/contents/ruff?ref={version}"))
    if content.get("type") != "submodule":
        raise SystemExit(f"ty の {version} の ruff が submodule でない: {content.get('type')}")
    rev = content["sha"]
    raw = f"https://raw.githubusercontent.com/astral-sh/ruff/{rev}"
    (ROOT / "Cargo.lock").write_bytes(fetch(f"{raw}/Cargo.lock"))
    channel = re.search(r'^channel = "([^"]+)"', fetch(f"{raw}/rust-toolchain.toml").decode(), re.MULTILINE)
    if channel is None:
        raise SystemExit("ruff の rust-toolchain.toml に channel が無い")
    replace(ROOT / "Cargo.toml", r'rev = "[0-9a-f]{40}"', f'rev = "{rev}"')
    replace(ROOT / "Cargo.toml", r"^# ty \S+（astral-sh/ty の \S+ のタグ）", f"# ty {version}（astral-sh/ty の {version} のタグ）")
    replace(ROOT / "rust-toolchain.toml", r'^channel = "[^"]+"', f'channel = "{channel.group(1)}"')
    replace(ROOT / "pyproject.toml", r'^version = "[^"]+"', f'version = "{version}"', count=1)
    replace(ROOT / "pyproject.toml", r'"ty==[^"]+"', f'"ty=={version}"')
    replace(ROOT / "src/main.rs", r'^const TY_VERSION: &str = "[^"]+";', f'const TY_VERSION: &str = "{version}";')
    print(f"ty {version}: ruff {rev}, Rust {channel.group(1)}")


def main() -> None:
    match sys.argv[1:]:
        case ["latest"]:
            latest()
        case ["unpublished", expected]:
            unpublished(int(expected))
        case ["update", version]:
            update(version)
        case _:
            raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
