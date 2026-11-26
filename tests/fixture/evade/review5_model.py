"""stub（review5_model.pyi）のあるクラス。"""

from evade.checks import six


class Y09Base:
    def y09m(self, t: int) -> int:  # 期待 1
        return 0


class Y09Child(Y09Base):
    def y09m(self, t: int) -> int:  # 期待 7
        return six(t)


class Y12Base:
    def y12m(self) -> int:  # 期待 7
        return six(0)
