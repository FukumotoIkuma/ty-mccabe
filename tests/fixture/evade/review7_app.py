"""stub が 2 つの実装に写るコンストラクタは、どちらも辿る。閾値 8 で測る。"""

from evade.review7_model import W05


def w05_both_ctors() -> W05:  # 期待 7（three_a・three_b の 3 ずつ）
    return W05()
