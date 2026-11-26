"""文字列で書いた cast の Protocol と、クラスの本体の for で置いた属性。閾値 8 で測る。"""

from typing import Protocol, cast

from evade.checks import six


class _X10P(Protocol):
    def x10m(self) -> int: ...  # 期待 1


class _X10Impl:
    def x10m(self) -> int:  # 期待 7
        return six(0)


def x10_string_cast(x: object) -> int:  # 期待 7（文字列で書いた cast の Protocol も、満たす _X10Impl の実装を数える）
    return cast("_X10P", x).x10m()


class _X11P(Protocol):
    ready: bool

    def x11m(self) -> int: ...  # 期待 1


class _X11Impl:
    for ready in [True, False]:
        pass

    def x11m(self) -> int:  # 期待 7
        return six(0)


def x11_use(x: _X11P) -> int:  # 期待 7（クラスの本体の for で置いた属性も持つので、_X11Impl は満たす）
    return x.x11m()


# <module> 期待 2（クラスの本体の for の 1）
