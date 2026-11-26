"""stub（review7_model.pyi）が 2 つの実装に写るコンストラクタ。"""

from os import getenv

from evade.checks import three_a, three_b


class W05:
    if getenv("MODE"):

        def __init__(self) -> None:  # 期待 4
            three_a(0)

    else:

        def __init__(self) -> None:  # 期待 4
            three_b(0)


# <module> 期待 2（if の 1。__init__ はクラスを呼ぶ所で数える）
