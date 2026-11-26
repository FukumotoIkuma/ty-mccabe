"""8 回目のレビューで挙がった数え落とし。閾値 8 で測る。six は分岐 6 つ（複雑度 7）。"""

from random import random
from typing import Literal, Protocol

from evade.checks import six


class _U01:
    def __iter__(self):  # 期待 7
        six(0)
        return iter(())


def _u01_other(*args: object) -> None:  # 期待 1
    pass


def u01_union_filter(x: _U01, flag: bool) -> object:  # 期待 7（共用型の filter に * で渡した x） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（filter の __iter__））
    return (_u01_other if flag else filter)(*(None, x))


class _U02P[T = int](Protocol):
    def u02m(self) -> T: ...  # 期待 1


class _U02:
    def u02m(self) -> str:  # 期待 7
        six(0)
        return ""


def u02_annotation_only(x: _U02P[str]) -> None:  # 期待 1（注釈だけに書いた _U02P[str]）
    pass


class _U03:
    def __round__(self) -> int:  # 期待 7
        return six(0)


def u03_round_star(args: tuple[_U03]) -> int:  # 期待 7（* で渡したタプルの要素の型） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（round の __round__））
    return round(*args)


class _U04Base:
    def __len__(self) -> int:  # 期待 7
        return six(0)


class _U04(_U04Base):
    def __init__(self) -> None:  # 期待 1
        self.__len__ = lambda: 0


def u04_instance_attr(x: _U04) -> int:  # 期待 7（暗黙の len はインスタンスの属性を見ない） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（len の __len__））
    return len(x)


class _U05Meta(type):
    def __len__(cls) -> int:  # 期待 7
        return six(0)


class _U05(metaclass=_U05Meta):
    pass


def u05_typevar_class[T: type[_U05]](x: T) -> int:  # 期待 7（上限がクラスの値の型引数は metaclass から） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（len の metaclass の __len__））
    return len(x)


class _U06Meta(type):
    @property
    def __match_args__(cls) -> tuple[Literal["u06_value"]]:  # 期待 7
        six(0)
        return ("u06_value",)


class _U06(metaclass=_U06Meta):
    u06_value = 0


def u06_match_args(x: _U06) -> bool:  # 期待 8（case の 1 と、metaclass の __match_args__ の getter） 限界 2（ty は metaclass の __match_args__ の getter を答えない）
    match x:
        case _U06(0):
            return True
    return False


def _u07_left(self: object) -> int:  # 期待 7
    return six(0)


def _u07_right(self: object) -> int:  # 期待 1
    return 0


class _U07:
    __len__ = _u07_left if random() < 0.5 else _u07_right


def u07_assigned_union(x: _U07) -> int:  # 期待 7 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（len の __len__））
    return len(x)


class _U10Meta(type):
    def __instancecheck__(cls, value: object) -> bool:  # 期待 7
        return six(0) == 0


class _U10(metaclass=_U10Meta):
    pass


def u10_isinstance_tuple(value: object) -> bool:  # 期待 7（タプルで渡したクラスの __instancecheck__） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（isinstance の metaclass の __instancecheck__））
    return isinstance(value, (_U10,))


class _U11P(Protocol):
    @property
    def u11_token(self) -> int: ...  # 期待 1


class _U11Base:
    def __getattr__(self, name: str) -> int:  # 期待 7
        return six(0)


def u11_make() -> _U11P:  # 期待 1（Protocol は使う所で数える。ここでは _U11P のメンバーを使わない）
    class _U11(_U11Base):
        pass

    return _U11()


# <module> 期待 7（クラスの本体に名前を書いた _u07_left が呼ぶ six の 6）
