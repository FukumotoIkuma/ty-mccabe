"""注釈の中の呼び出しと、for で self に置いた属性。閾値 8 で測る。"""

from typing import Annotated, Protocol

from evade.checks import six


def _y13() -> int:  # 期待 7
    return six(0)


def y13_annotated(x: Annotated[int, _y13()]) -> None:  # 期待 1（注釈は def を実行する所で評価する）
    pass


class _Y14P(Protocol):
    y14_ready: bool

    def y14m(self) -> int: ...  # 期待 1


class _Y14Impl:
    def setup(self) -> None:  # 期待 2
        for self.y14_ready in (True,):
            pass

    def y14m(self) -> int:  # 期待 7
        return six(0)


def y14_use(x: _Y14P) -> int:  # 期待 7（for で self に置いた属性も持つので、_Y14Impl は満たす）
    return x.y14m()


# <module> 期待 7（注釈の _y13 が呼ぶ six の 6）
