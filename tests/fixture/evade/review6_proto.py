"""型引数の既定値にだけ書いた Protocol。閾値 8 で測る。"""

from typing import Protocol

from evade.checks import six


class _Z14P(Protocol):
    def z14m(self) -> int: ...  # 期待 1


class _Z14Impl:
    def z14m(self) -> int:  # 期待 7
        return six(0)


def z14_marker[T = _Z14P]() -> None:  # 期待 1
    pass


# <module> 期待 1（型引数の既定値に書いた _Z14P は、メンバーを使う所が無いので、満たすクラスの実装を数えない）
