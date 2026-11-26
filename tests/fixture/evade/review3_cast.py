"""注釈でなく cast に名前を書いた Protocol も照らす。閾値 8 で測る。"""

from typing import Protocol, cast

from evade.checks import six


class _W13Q(Protocol):
    def w13n(self) -> int: ...  # 期待 1


class _W13QImpl:
    def w13n(self) -> int:  # 期待 7
        return six(0)


def w13_cast(x: object) -> int:  # 期待 7（cast に名前を書いた Protocol も、満たす _W13QImpl の実装を数える）
    return cast(_W13Q, x).w13n()


# <module> 期待 1（分岐は無い）
