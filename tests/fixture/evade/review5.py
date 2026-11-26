"""4 回目のレビューで挙がった数え落とし（呼ぶ値の型・特殊メソッド）。閾値 8 で測る。six は分岐 6 つ（複雑度 7）。"""

from collections import ChainMap
from collections.abc import Callable
from fractions import Fraction
from typing import overload

from evade.checks import six


@overload
def _y01(t: int) -> int: ...
@overload
def _y01(t: str) -> str: ...
def _y01(t: int | str) -> int | str:  # 期待 7
    return six(0)


_Y01_TABLE = (_y01,)


def y01_overload(t: int) -> object:  # 期待 7（overload の関数は、実装で数える）
    return _Y01_TABLE[0](t)


class _Y02:
    def __init__(self, t: int) -> None:  # 期待 7
        six(t)


class _Y02Holder:
    @property
    def factory(self) -> type[_Y02]:  # 期待 1
        return _Y02


def y02_property_class(h: _Y02Holder, t: int) -> _Y02:  # 期待 7（property が返すクラスを呼ぶ所のコンストラクタ）
    return h.factory(t)


def _y03() -> int:  # 期待 7
    return six(0)


_Y03_TABLE = (_y03,)


def y03_union(cb: Callable[[], str], flag: bool) -> object:  # 期待 7（共用型の、関数に決まる要素は辿る）
    return (_Y03_TABLE[0] if flag else cb)()


class _Y04:
    def __len__(self) -> int:  # 期待 7
        return six(0)


_Y04_MEASURE = (len,)
_Y04_EVAL = (eval,)


def y04_builtin_in_tuple(x: _Y04) -> int:  # 期待 7 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（len の __len__））
    return _Y04_MEASURE[0](x)


def y04_eval_in_tuple() -> object:  # 期待 分からない 限界 1（ty は名前を文字列で引く所を見分けない）
    return _Y04_EVAL[0]("0")


class _Y05(ChainMap[str, int]):
    def __len__(self) -> int:  # 期待 7
        return six(0)


def y05_lib_dunder(m: ChainMap[str, int]) -> int:  # 期待 7（ChainMap の値は、ChainMap を継いだ _Y05 でありうる） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（len の __len__））
    return len(m)


class _Y06(Fraction):
    def __neg__(self) -> Fraction:  # 期待 7
        six(0)
        return self


def y06_lib_operator(x: Fraction) -> Fraction:  # 期待 7 限界 1（ty は演算子の特殊メソッドの、下位のクラスでの上書きを答えない）
    return -x


class _Y07:
    def __iter__(self):  # 期待 7
        six(0)
        return iter(())


def y07_zip_second(x: _Y07) -> object:  # 期待 7 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（zip の __iter__））
    return zip((0,), x)


class _Y08:
    def __round__(self) -> int:  # 期待 7
        return six(0)


def y08_round(x: _Y08) -> int:  # 期待 7 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（round の __round__））
    return round(x)


# <module> 期待 7（表に名前を書いた _y01・_y03 が呼ぶ six の 6）
