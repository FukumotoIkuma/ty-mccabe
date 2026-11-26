"""多めに数えていた例。閾値 8 で測る。six は分岐 6 つ（複雑度 7）。"""

from evade.checks import six


class _W14A:
    def m(self, t: int) -> int:  # 期待 1
        return 0


class _W14B(_W14A):
    pass


class _W14C(_W14A):
    def m(self, t: int) -> int:  # 期待 7
        return six(t)


def w14_sibling(x: _W14B, t: int) -> int:  # 期待 1（_W14B の値は、兄弟の _W14C ではありえない）
    return x.m(t)


def w14_base(x: _W14A, t: int) -> int:  # 期待 7（_W14A の値は、下位の _W14C でありうる）
    return x.m(t)


class _W15:
    @property
    def p(self) -> int:  # 期待 1
        return 0

    @p.setter
    def p(self, v: int) -> None:  # 期待 7
        six(v)


def w15_read(x: _W15) -> int:  # 期待 1（読むだけなら setter は動かない）
    return x.p


def w15_write(x: _W15) -> None:  # 期待 7（書けば setter が動く）
    x.p = 1



class _W16:
    def __init__(self) -> None:
        self.a16, self.b16 = 0, 0

    def w16(self) -> int:  # 期待 1（分割代入で置いた属性も、ty が返す定義の場所として索引にある）
        return self.a16


# <module> 期待 7（デコレータで登録した setter が呼ぶ six の 6。デコレータを書いたクラスの本体で数える）
