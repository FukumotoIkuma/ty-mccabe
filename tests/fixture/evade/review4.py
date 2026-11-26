"""3 回目のレビューで挙がった数え落とし。閾値 8 で測る。six は分岐 6 つ（複雑度 7）。"""

from collections import deque

from evade.checks import six


def _x01(t: int) -> int:  # 期待 7
    return six(t)


_X01_TABLE = (_x01,)


def x01_tuple_item(t: int) -> int:  # 期待 7（固定長のタプルの要素は、ty が呼ぶ先を答える）
    return _X01_TABLE[0](t)


class _X04(deque[int]):
    def appendleft(self, value: int, /) -> None:  # 期待 7
        six(value)


def x04_lib_base(items: deque[int], value: int) -> None:  # 期待 7（deque の値は、deque を継いだ _X04 でありうる）
    items.appendleft(value)


class _X06:
    @property
    def value(self) -> int:  # 期待 7
        return six(0)

    @value.setter
    def value(self, new: int) -> None:  # 期待 1
        pass


def x06_augmented(box: _X06) -> None:  # 期待 7（+= は getter で読んでから setter で書く） 限界 1（ty は += の属性を書く所としてだけ答え、getter で読むことを答えない）
    box.value += 1


def x12_register(callback=lambda: six(0)) -> None:  # 期待 1（既定値の lambda は、def を実行する所の一部）
    pass


class _X14:
    def work(self, t: int) -> int:  # 期待 7
        return six(t)


def x14_dict(w: _X14, t: int) -> int:  # 期待 分からない（getattr で __dict__ を引くのも、名前を文字列で引く） 限界 1（ty は名前を文字列で引く所を見分けない）
    return getattr(_X14, "__dict__")["work"](w, t)


# <module> 期待 7（既定値の lambda が呼ぶ six の 6）
