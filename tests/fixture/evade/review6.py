"""5 回目のレビューで挙がった数え落とし（呼ぶ値の型・下位のクラス・特殊メソッド）。閾値 8 で測る。six は分岐 6 つ（複雑度 7）。"""

from collections.abc import Iterator
from typing import TypeVar, overload

from evade.checks import six

_Z01_CALLS = (eval.__call__,)


def z01_bound_eval() -> object:  # 期待 分からない（ty は eval.__call__ の元の eval を覚えている） 限界 1（ty は名前を文字列で引く所を見分けない）
    return _Z01_CALLS[0]("0")


class _Z05:
    def __init__(self, t: int) -> None:  # 期待 7
        six(t)


_Z05T = TypeVar("_Z05T", bound=type[_Z05])


def z05_typevar_class(cls: _Z05T, t: int) -> _Z05:  # 期待 7（上限がクラスの値の型引数を呼ぶ所のコンストラクタ）
    return (cls,)[0](t)


class _Z06:
    @overload
    def __init__(self, t: int) -> None: ...
    @overload
    def __init__(self, t: str) -> None: ...
    def __init__(self, t: int | str) -> None:  # 期待 7
        six(0)


def z06_overload_ctor(t: int) -> _Z06:  # 期待 7（overload のコンストラクタは、実装で数える） 限界 1（ty はコンストラクタの overload を、呼び出しで宣言だけ答える）
    return (_Z06,)[0](t)


class _Z07Meta(type):
    def __len__(cls) -> int:  # 期待 7
        return six(0)


class _Z07(metaclass=_Z07Meta):
    def __len__(self) -> int:  # 期待 1
        return 0


def z07_metaclass(t: int) -> int:  # 期待 7（クラスの値の len は metaclass の __len__） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（len の metaclass の __len__））
    return len(_Z07)


class _Z08Base:
    pass


class _Z08(_Z08Base):
    def __bool__(self) -> bool:  # 期待 7
        return six(0) == 0


def z08_root_lacks(x: _Z08Base) -> int:  # 期待 8（_Z08Base に無い __bool__ も、下位の _Z08 で動く） 限界 2（ty は暗に呼ぶ特殊メソッドを答えない（真偽の判定の __bool__））
    if x:
        return 1
    return 0


class _Z09Base:
    def z09m(self, t: int) -> int:  # 期待 1
        return 0


class _Z09Mixin:
    def z09m(self, t: int) -> int:  # 期待 7
        return six(t)


class _Z09Child(_Z09Mixin, _Z09Base):
    pass


def z09_other_base(x: _Z09Base, t: int) -> int:  # 期待 7（下位の _Z09Child は _Z09Mixin の z09m を継ぐ） 限界 1（ty の実装への移動は、別の基底から継いだだけの下位のクラスを答えない）
    return x.z09m(t)


class _Z10:
    def __iter__(self) -> Iterator[int]:  # 期待 7
        six(0)
        return iter(())


def z10_builtin_class(x: _Z10) -> list[int]:  # 期待 7（タプルから取り出した list も、組み込みの関数の表で引く） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（list の __iter__））
    return (list,)[0](x)


class _Z11:
    def __round__(self) -> int:  # 期待 7
        return six(0)


def z11_keyword(x: _Z11) -> int:  # 期待 7 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（round の __round__））
    return round(number=x)


class _Z12:
    def __lt__(self, other: object) -> bool:  # 期待 7
        return six(0) == 0


def z12_min(a: _Z12, b: _Z12) -> _Z12:  # 期待 7（引数どうしを比べる） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（min の __lt__））
    return min(a, b)


class _Z13:
    def __iter__(self) -> Iterator[int]:  # 期待 7
        six(0)
        return iter(())


def z13_yield_from(x: _Z13) -> Iterator[int]:  # 期待 7 限界 1（ty は暗に呼ぶ特殊メソッドを答えない（yield from の __iter__））
    yield from x


class _Z16:
    @property
    def value(self) -> int:  # 期待 7
        return six(0)


def z16_class_pattern(x: _Z16) -> bool:  # 期待 8（case の 1 と、パターンが読む value の getter）
    match x:
        case _Z16(value=1):
            return True
    return False


# <module> 期待 1（特殊メソッドは、使う所で数える）
