"""定数の getattr で、モジュールの属性として読む関数。"""

from evade.checks import six


def u08_work(t: int) -> int:  # 期待 7
    return six(t)
