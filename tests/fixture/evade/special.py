"""特殊メソッドに分岐を移す例。暗に呼ぶ特殊メソッドは ty が答えないので、限界として数が下がる（docs/design.md の 8）。"""

from typing import Any

from evade.checks import FLAG


class _Box:
    def __bool__(self) -> bool:  # 期待 3
        if FLAG:
            return True
        elif FLAG is None:
            return False
        return False


def s1_truth(b: _Box) -> int:  # 期待 3（真偽の判定が呼ぶ __bool__ を、値の型から ty に引く） 限界 1（ty は暗に呼ぶ特殊メソッドを答えない（真偽の判定の __bool__））
    return 1 if b else 0


def s2_truth_any(b: Any) -> int:  # 期待 1（型の分からない値の真偽の判定は 1 つの文）
    return 1 if b else 0


# <module> 期待 1（特殊メソッドは、使う所で数える）
