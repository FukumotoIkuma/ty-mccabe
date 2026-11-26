"""6 回目のレビューで挙がった数え落とし（下位のクラスで動くメンバー・metaclass・overload・パターン）。閾値 8 で測る。
six は分岐 6 つ（複雑度 7）。"""

from collections import OrderedDict
from typing import TypeVar, overload

from evade.checks import six


class _W01Mixin:
    def move_to_end(self, key: str, last: bool = True) -> None:  # 期待 7
        six(0)


class _W01(_W01Mixin, OrderedDict[str, int]):
    pass


def w01_lib_root_mixin(d: OrderedDict[str, int]) -> None:  # 期待 7（OrderedDict の値は、_W01Mixin の move_to_end を継ぐ _W01 でありうる） 限界 1（ty の実装への移動は、別の基底から継いだだけの下位のクラスを答えない）
    d.move_to_end("a")


class _W02Base:
    def w02m(self) -> int:  # 期待 1
        return 0


class _W02Mixin:
    def w02m(self) -> int:  # 期待 7
        return six(0)


class _W02Child(_W02Mixin, _W02Base):
    pass


_W02T = TypeVar("_W02T", bound=_W02Base)


def w02_typevar_bound(x: _W02T) -> int:  # 期待 7（型引数の上限の下位のクラスで動くもの） 限界 1（ty の実装への移動は、別の基底から継いだだけの下位のクラスを答えない）
    return x.w02m()


_F = TypeVar("_F")


class _W03Decorators:
    @staticmethod
    def setter(f: _F) -> _F:  # 期待 1
        return f


class _W03Base:
    def w03m(self) -> int:  # 期待 1
        return 0


class _W03Mixin:
    @_W03Decorators.setter
    def w03m(self) -> int:  # 期待 7
        return six(0)


class _W03Child(_W03Mixin, _W03Base):
    pass


def w03_setter_named_decorator(x: _W03Base) -> int:  # 期待 7（.setter という名前のデコレータでも、property でなければ普通のメソッド） 限界 1（ty の実装への移動は、別の基底から継いだだけの下位のクラスを答えない）
    return x.w03m()


class _W04Meta1(type):
    pass


class _W04Meta2(_W04Meta1):
    def __len__(cls) -> int:  # 期待 7
        return six(0)


class _W04Left(metaclass=_W04Meta1):
    pass


class _W04Right(metaclass=_W04Meta2):
    pass


class _W04(_W04Left, _W04Right):
    def __len__(self) -> int:  # 期待 1
        return 0


def w04_selected_metaclass() -> int:  # 期待 7（Python が選ぶ metaclass は _W04Meta2） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（len の metaclass の __len__））
    return len(_W04)


@overload
def _w06_init(obj: object, t: int) -> None: ...
@overload
def _w06_init(obj: object, t: str) -> None: ...
def _w06_init(obj: object, t: int | str) -> None:  # 期待 7
    six(0)


class _W06:
    __init__ = _w06_init


def w06_assigned_overload(t: int) -> _W06:  # 期待 7（代入した overload の関数は、実装で数える） 限界 1（ty は代入した overload の関数を、呼び出しで宣言だけ答える）
    return _W06(t)


class _W07:
    def __round__(self) -> int:  # 期待 7
        return six(0)


def _w07_other(value: object = None, *, number: _W07) -> int:  # 期待 1
    return 0


def w07_keyword_candidate(x: _W07, choose: bool) -> int:  # 期待 7（条件式は C901 に数えない） 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（round の __round__））
    return (_w07_other if choose else round)(number=x)


class _W08:
    def __lt__(self, other: "_W08") -> bool:  # 期待 7
        return six(0) == 0


def w08_starred_min(a: _W08, b: _W08) -> _W08:  # 期待 7 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（min の __lt__））
    return min(*(a, b))


class _W09:
    @property
    def value(self) -> int:  # 期待 7
        return six(0)


_W09Alias = _W09


def w09_pattern_alias(x: _W09) -> bool:  # 期待 8（case の 1 と、getter）
    match x:
        case _W09Alias(value=1):
            return True
    return False


class _W11:
    __match_args__ = ("value",)

    @property
    def value(self) -> int:  # 期待 7
        return six(0)


def w11_match_args(x: _W11) -> bool:  # 期待 8（位置のパターンは __match_args__ の value を読む）
    match x:
        case _W11(1):
            return True
    return False


class _W12:
    def __eq__(self, other: object) -> bool:  # 期待 7
        return six(0) == 0


def w12_value_pattern(x: _W12) -> bool:  # 期待 8（値のパターンは == で比べる） 限界 2（ty は暗に呼ぶ特殊メソッドを答えない（値のパターンの __eq__））
    match x:
        case 1:
            return True
    return False


class _W13Decorator:
    def __call__(self, f: _F) -> _F:  # 期待 7
        six(0)
        return f


def w13_decorator_call() -> None:  # 期待 7（@_W13Decorator() が呼ぶ __call__。中に書いた def は分岐ではない） 限界 1（ty はデコレータを当てる呼び出しが呼ぶものを答えない）
    @_W13Decorator()
    def inner() -> None:  # 期待 7 限界 1（ty はデコレータを当てる呼び出しが呼ぶものを答えない）
        pass


# <module> 期待 7（クラスの本体に名前を書いた _w06_init が呼ぶ six の 6）
