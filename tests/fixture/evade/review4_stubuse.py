"""stub のあるメソッドは、ty の stub から実行時のソースへの置き換えで辿る。閾値 8 で測る。"""

from evade.review4_stub import X05


def x05_stub(w: X05, t: int) -> int:  # 期待 7
    return w.work(t)
