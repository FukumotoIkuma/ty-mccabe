"""型引数を付けたクラスを呼ぶ所のコンストラクタ。閾値 8 で測る。"""

from typing import Generic, TypeVar

from evade.checks import six

T = TypeVar("T")


class _X02(Generic[T]):
    def __init__(self, value: T, t: int) -> None:  # 期待 7
        six(t)


def x02_generic(t: int) -> _X02[int]:  # 期待 7
    return _X02[int](0, t)


# <module> 期待 1（__init__ はクラスを呼ぶ所で数える）
