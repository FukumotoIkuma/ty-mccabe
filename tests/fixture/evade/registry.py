"""デコレータで登録した関数の例。登録した関数を呼ぶ所は値の流れなので数えず、関数はそれ自身の数で出る。"""

from collections.abc import Callable

from evade.checks import FLAG

_HANDLERS: list[Callable[[], int]] = []


def register(fn: Callable[[], int]) -> Callable[[], int]:  # 期待 1
    _HANDLERS.append(fn)
    return fn


@register
def handler() -> int:  # 期待 3（分岐 2 つ）
    if FLAG:
        return 1
    if not FLAG:
        return 2
    return 0


def g1_dispatch() -> int:  # 期待 1（登録した関数を呼ぶ所は 1 つの文）
    return sum(f() for f in _HANDLERS)


# <module> 期待 1（デコレータで登録した handler は、それ自身の数で出る。登録した関数を呼ぶ所は値の流れなので数えない）
