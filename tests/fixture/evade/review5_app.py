"""stub のあるクラスの下位のクラスの上書き・基底から継いだ Protocol の実装。閾値 8 で測る。"""

from typing import Protocol

from evade.review5_model import Y09Base, Y12Base


def y09_stub_override(x: Y09Base, t: int) -> int:  # 期待 7（Y09Base の値は、下位の Y09Child でありうる） 限界 1（ty の実装への移動は、stub のクラスから実行時のソースの下位のクラスを探さない）
    return x.y09m(t)


class _Y12P(Protocol):
    y12_ready: bool

    def y12m(self) -> int: ...  # 期待 1


class _Y12Child(Y12Base):
    y12_ready = True


def y12_use(x: _Y12P) -> int:  # 期待 7（_Y12P を満たす _Y12Child が継いだ Y12Base.y12m を数える）
    return x.y12m()


# <module> 期待 1（分岐は無い）
