"""分岐 6 つの確かめ。どの迂回の例も、この 6 つをどこかに隠す。"""


def six(t: int) -> int:
    if t == 1:
        return 1
    if t == 2:
        return 2
    if t == 3:
        return 3
    if t == 4:
        return 4
    if t == 5:
        return 5
    if t == 6:
        return 6
    return 0


def three_a(t: int) -> int:
    if t == 1:
        return 1
    if t == 2:
        return 2
    if t == 3:
        return 3
    return 0


def three_b(t: int) -> int:
    if t == 4:
        return 4
    if t == 5:
        return 5
    if t == 6:
        return 6
    return 0


FLAG = True


def leaf() -> int:  # 期待 2（レビューの例が隠す、分岐 1 つの関数）
    if FLAG:
        return 1
    return 0

# <module> 期待 1
