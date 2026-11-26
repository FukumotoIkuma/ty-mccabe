"""表を別々のモジュールに分けて置いても、import した所へ展開される例。"""

from evade import split_a, split_b


def m1_split_tables(k: str, t: int) -> int:  # 期待 1（表の値を呼ぶ所は 1 つの文）
    return split_a.TABLE_A[k](t) + split_b.TABLE_B[k](t)


# <module> 期待 7（split_a・split_b の最上位は閾値未満なので、import したここへ展開される）
