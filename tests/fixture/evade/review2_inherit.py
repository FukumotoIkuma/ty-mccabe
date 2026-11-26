"""Protocol を、基底から継いだメソッドで満たすクラス。閾値 8 で測る。"""

from typing import Protocol

from evade.checks import FLAG
from evade.review2_parent import _Base6


class _P6(Protocol):
    ready6: bool

    def m6(self, t: int) -> int: ...  # 期待 1


class _Child6(_Base6):
    ready6 = True


def use6(p: _P6, t: int) -> int:  # 期待 7（Protocol のメンバーを呼ぶ所は、_P6 を満たす _Child6 が継いだ _Base6.m6 を数える）
    return p.m6(t)


if FLAG:
    pass

# <module> 期待 2（if の 1。基底のモジュールは閾値以上なので、import からは届かない）
