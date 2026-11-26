"""どこにも名前を書かない Protocol は照らさない。閾値 8 で測る。"""

from typing import Protocol

from evade.checks import six


class _W13P(Protocol):
    def w13m(self) -> int: ...  # 期待 1


class _W13Impl:
    def w13m(self) -> int:  # 期待 7
        return six(0)


# <module> 期待 1（_W13P はどこにも名前を書かないので、_W13Impl.w13m はここで数えない）
