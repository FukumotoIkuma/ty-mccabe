"""文字列で書いた注釈の、ライブラリの Protocol。閾値 8 で測る。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from evade.checks import six

if TYPE_CHECKING:
    from _typeshed import SupportsRead


class _Reader7:
    def read(self, n: int = -1) -> str:  # 期待 7
        return str(six(n))


def use7(x: "SupportsRead[str]") -> str:  # 期待 7（文字列で書いた注釈のライブラリの Protocol も、満たす _Reader7 の実装を数える）
    return x.read()


# <module> 期待 2（if の 1）
