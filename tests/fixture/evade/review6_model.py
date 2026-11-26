"""stub（review6_model.pyi）に載せていない下位のクラスと、stub が複数の実装に写る関数。"""

from os import getenv

from evade.checks import six, three_a, three_b


class Z03Base:
    def z03m(self, t: int) -> int:  # 期待 1
        return 0


class _Z03Child(Z03Base):
    def z03m(self, t: int) -> int:  # 期待 7
        return six(t)


if getenv("FEATURE"):

    def z04(t: int) -> int:  # 期待 4
        return three_a(t)

else:

    def z04(t: int) -> int:  # 期待 4
        return three_b(t)


# <module> 期待 2（if の 1。z04 はここから呼ばない）
