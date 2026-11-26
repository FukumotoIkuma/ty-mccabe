"""7 回目のレビューで挙がった数え落とし。閾値 8 で測る。six は分岐 6 つ（複雑度 7）。"""

from collections.abc import Iterator
from typing import Protocol

from evade.checks import six


class _V02P(Protocol):
    @property
    def v02_token(self) -> int: ...

    def v02m(self) -> None: ...


class _V02:
    def __getattr__(self, name: str) -> int:  # 期待 1
        return 0

    def v02m(self) -> None:  # 期待 7
        six(0)


def v02_use(x: _V02P) -> None:  # 期待 7（__getattr__ の読み取りでも Protocol の property を満たすので、_V02.v02m を数える）
    x.v02m()


class _V03P[T = int](Protocol):
    def v03m(self) -> T: ...  # 期待 1


class _V03:
    def v03m(self) -> str:  # 期待 7
        six(0)
        return ""


def v03_use(x: _V03P[str]) -> str:  # 期待 7（型引数を当てた _V03P[str] を _V03 が満たすので、_V03.v03m を数える）
    return x.v03m()


class _V05:
    def __init__(self, f: object) -> None:  # 期待 7
        six(0)


def v05_class_decorator() -> None:  # 期待 7（クラスを当てるコンストラクタ。中に書いた def は分岐ではない） 限界 1（ty はデコレータを当てる呼び出しが呼ぶものを答えない）
    @_V05
    def inner() -> None:  # 期待 7 限界 1（ty はデコレータを当てる呼び出しが呼ぶものを答えない）
        pass


class _V06Meta(type):
    def __len__(cls) -> int:  # 期待 7
        return six(0)


class _V06(metaclass=_V06Meta):
    pass


def v06_union_class(x: type[_V06] | str) -> int:  # 期待 7（共用型の要素のクラスの値は metaclass から引く） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（len の metaclass の __len__））
    return len(x)


class _V07A:
    @property
    def value(self) -> int:  # 期待 7
        return six(0)


class _V07B:
    @property
    def value(self) -> int:  # 期待 7
        return six(1)


def v07_pattern_union(x: _V07A | _V07B, flag: bool) -> bool:  # 期待 8（case の 1 と、どちらかの getter）
    cls = _V07A if flag else _V07B
    match x:
        case cls(value=0):
            return True
    return False


class _V08:
    def __eq__(self, other: object) -> bool:  # 期待 7
        return six(0) == 0


def v08_value_as(x: _V08) -> bool:  # 期待 8（case の 1 と、as を付けた値のパターンの ==） 限界 2（ty は暗に呼ぶ特殊メソッドを答えない（値のパターンの __eq__））
    match x:
        case 0 as matched:
            return matched is None
    return False


class _V09:
    def __iter__(self) -> Iterator[int]:  # 期待 7
        six(0)
        return iter(())


def v09_zip_after_star(prefix: tuple[()], x: _V09) -> object:  # 期待 7 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（zip の __iter__））
    return zip(*prefix, x)


class _V10:
    def __round__(self) -> int:  # 期待 7
        return six(0)


def v10_round_double_star(x: _V10) -> int:  # 期待 7 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（round の __round__））
    return round(**{"number": x})


def _v11_impl(self: object) -> None:  # 期待 7
    six(0)


class _V11Base:
    def v11m(self) -> None:  # 期待 1
        pass


class _V11Child(_V11Base):
    v11m = _v11_impl


def v11_assigned_method(x: _V11Base) -> None:  # 期待 7（下位のクラスが代入で置いた関数）
    x.v11m()


class _V12:
    def v12_read(self) -> int:  # 期待 7
        return six(0)

    v12_value = property(v12_read)


def v12_property_call(x: _V12) -> int:  # 期待 7（property(...) で置いた property の getter）
    return x.v12_value


class _V13P(Protocol):
    @property
    def v13_value(self) -> int: ...  # 期待 1

    @v13_value.setter
    def v13_value(self, v: int) -> None: ...  # 期待 1


class _V13Base:
    @property
    def v13_value(self) -> int:  # 期待 1
        return 0

    @v13_value.setter
    def v13_value(self, v: int) -> None:  # 期待 7
        six(v)


def v13_make() -> _V13P:  # 期待 1（Protocol は使う所で数える。ここでは _V13P のメンバーを使わない）
    class _V13Impl(_V13Base):
        pass

    return _V13Impl()


class _V14:
    def __class_getitem__(cls, key: int) -> int:  # 期待 7
        return six(key)


def v14_class_getitem() -> int:  # 期待 7（クラスの添字は、クラスの __class_getitem__） 限界 1（ty は暗に呼ぶ特殊メソッドを答えない（クラスの添字の __class_getitem__））
    return _V14[1]


# <module> 期待 7（クラスの本体に名前を書いた _v11_impl・v12_read が呼ぶ six の 6）
