"""Protocol を満たすクラスの、分割代入で置いた欄。閾値 8 で測る。"""

from typing import Protocol

from evade.checks import FLAG, six


class _P5(Protocol):
    ready5: bool

    def m5(self, t: int) -> int: ...  # 期待 1


class _C5:
    ready5, spare5 = True, False

    def m5(self, t: int) -> int:  # 期待 7
        return six(t)


def use5(p: _P5, t: int) -> int:  # 期待 7（Protocol のメンバーを呼ぶ所は、満たす _C5 の実装を数える）
    return p.m5(t)


if FLAG:
    pass

# <module> 期待 2（if の 1）
