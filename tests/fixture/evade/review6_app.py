"""stub のあるモジュールの、stub に無い下位のクラスと、複数の実装。閾値 8 で測る。"""

from evade.review6_model import Z03Base, z04

_Z04_TABLE = (z04,)


def z03_private_child(x: Z03Base, t: int) -> int:  # 期待 7（Z03Base の値は、stub に無い _Z03Child でありうる） 限界 1（ty の実装への移動は、stub のクラスから実行時のソースの下位のクラスを探さない）
    return x.z03m(t)


def z04_both(t: int) -> int:  # 期待 7（stub の z04 は、実装の 2 つのどちらでもありうる）
    return _Z04_TABLE[0](t)
