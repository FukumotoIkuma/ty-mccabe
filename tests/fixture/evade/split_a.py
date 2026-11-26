"""モジュールを分けて表を置く例（split_main が import する）。"""

from evade.checks import three_a

TABLE_A = {"a": three_a}

# <module> 期待 4（表に置いた three_a）
