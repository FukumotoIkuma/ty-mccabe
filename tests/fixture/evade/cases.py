"""迂回の例。閾値 8 で測る（分岐 6 つの six は複雑度 7 で閾値未満なので、隠した先から呼ぶ側へ展開される）。"""

import functools
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from evade import same_a
from evade.checks import six, three_a, three_b
from evade.checks import six as renamed


def e01_whole(t: int) -> int:  # 期待 7（分岐を自分で持つ）
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


def e02_split(t: int) -> int:  # 期待 7（2 つに分けた）
    return three_a(t) + three_b(t)


_TABLE = {"a": three_a, "b": three_b}


def e03_table(t: int) -> int:  # 期待 1（辞書に入れた。three_a・three_b は _TABLE を書いたモジュールの最上位で数える）
    return _TABLE["a"](t) + _TABLE["b"](t)


class _Cached:
    def __init__(self) -> None:
        self._fn = functools.lru_cache(maxsize=8)(self._read)

    def _read(self, t: int) -> int:
        return six(t)

    def get(self, t: int) -> int:
        return self._fn(t)


def e04_wrapped_attr(t: int) -> int:  # 期待 7（属性に包んで入れた）
    return _Cached().get(t)


@dataclass(frozen=True)
class _Spec:
    check: Callable[[int], int]


_SPECS = {"x": _Spec(check=six)}


def e05_field(t: int) -> int:  # 期待 1（dataclass の欄に入れた。six は _SPECS を書いたモジュールの最上位で数える）
    return _SPECS["x"].check(t)


def _apply(fn: Callable[[int], int], t: int) -> int:
    return fn(t)


def e06_param(t: int) -> int:  # 期待 7（引数で渡した）
    return _apply(six, t)


def e07_same_name(r: same_a.Rule, t: int) -> int:  # 期待 7（下位のクラスが同じ名前で上書き）
    return r.apply(t)


class _WithProp:
    def __init__(self, t: int) -> None:
        self.t = t

    @property
    def value(self) -> int:
        return six(self.t)


def e08_property(t: int) -> int:  # 期待 7（property に移した）
    return _WithProp(t).value


def _deco(fn: Callable[[int], int]) -> Callable[[int], int]:  # 期待 7（six の 6。中に書いた def は分岐ではない）
    def wrapper(t: int) -> int:
        return fn(t) + six(t)

    return wrapper


@_deco
def _decorated(t: int) -> int:
    return t


def e09_decorator(t: int) -> int:  # 期待 1（デコレータに移した。_decorated に付けた _deco は閾値以上で、それ自身の数で出る）
    return _decorated(t)


class _Num:
    def __init__(self, t: int) -> None:
        self.t = t

    def __add__(self, other: "_Num") -> int:
        return six(self.t)


def e10_operator(t: int) -> int:  # 期待 7（演算子の特殊メソッドに移した）
    return _Num(t) + _Num(t)


def e11_callback(t: int) -> int:  # 期待 7（ライブラリに呼び返させた）
    return sorted([t], key=six)[0]


def e12_lambda(t: int) -> int:  # 期待 7（lambda に包んだ）
    f = lambda v: six(v)  # noqa: E731
    return f(t)


def _factory() -> Callable[[int], int]:
    return six


def e13_returned(t: int) -> int:  # 期待 7（関数を返す関数を通した）
    return _factory()(t)


_REGISTRY: list[Callable[[int], int]] = []
_REGISTRY.append(six)


def e14_registry(t: int) -> int:  # 期待 2（登録した一覧を回す。for の 1。six は _REGISTRY.append(six) を書いたモジュールの最上位で数える）
    total = 0
    for fn in _REGISTRY:
        total += fn(t)
    return total


class _Callable:
    def __call__(self, t: int) -> int:
        return six(t)


def e15_call(t: int) -> int:  # 期待 7（__call__ に移した）
    c = _Callable()
    return c(t)


class _Ctx(AbstractContextManager["_Ctx"]):
    def __init__(self, t: int) -> None:
        self.t = t

    def __enter__(self) -> "_Ctx":
        six(self.t)
        return self

    def __exit__(self, *a: object) -> None:
        return None


def e16_with(t: int) -> int:  # 期待 7（with の特殊メソッドに移した。with が呼ぶ特殊メソッドは値の型から ty に引く） 限界 1（ty は暗に呼ぶ特殊メソッドを答えない（with の __enter__））
    with _Ctx(t):
        return t


def e17_alias(t: int) -> int:  # 期待 7（別名で import した）
    return renamed(t)


class _Iter:
    def __init__(self, t: int) -> None:
        self.t = t

    def __iter__(self) -> Iterator[int]:
        yield six(self.t)


def e18_iter(t: int) -> int:  # 期待 8（for の特殊メソッドに移した。for の 1 が増える） 限界 2（ty は暗に呼ぶ特殊メソッドを答えない（for の __iter__））
    total = 0
    for v in _Iter(t):
        total += v
    return total


class Checker(Protocol):
    def check(self, t: int) -> int: ...


def e19_protocol(c: Checker, t: int) -> int:  # 期待 1（Protocol のメンバーを呼ぶ所は 1 つの文。満たす _Spec の欄に入れた six は _SPECS を書いた所で数える）
    return c.check(t)


def e20_bound_method(t: int) -> int:  # 期待 7（メソッドを値として取り出してから呼んだ）
    m = _Cached().get
    return m(t)


@dataclass(frozen=True)
class _A:
    t: int

    @property
    def value(self) -> int:
        return three_a(self.t)


@dataclass(frozen=True)
class _B:
    t: int

    @property
    def value(self) -> int:
        return three_b(self.t)


type _AB = _A | _B


def e21_union(x: _A | _B) -> int:  # 期待 7（共用型の受け手の property に移した）
    return x.value


def e22_alias(x: _AB) -> int:  # 期待 7（型の別名の共用型の受け手）
    return x.value


def e23_typevar[T: _A | _B](x: T) -> int:  # 期待 7（型引数の受け手）
    return x.value


def e24_try(t: int) -> int:  # 期待 2（複数行の except ... as）
    try:
        return t
    except (
        ValueError,
        KeyError,
    ) as exc:
        raise RuntimeError(str(exc)) from exc


def e25_typevar_loop[T: _A | _B](xs: list[T]) -> int:  # 期待 8（注釈の無い for の変数の受け手。for の 1）
    total = 0
    for x in xs:
        total += x.value
    return total


def e26_subscript_typevar[T: _A | _B](pair: tuple[int, T]) -> int:  # 期待 7（添字の式の受け手が型引数）
    return pair[1].value


class _Labeled:
    def __init__(self, t: int) -> None:
        self.t = t

    @property
    def label(self) -> int:
        return six(self.t)


def e27_takes_property_value(n: int) -> int:  # 期待 1（property を読んだ値は関数ではないので、渡されても辿らない）
    return len(str(n))


def e28_reads_property(x: _Labeled) -> int:  # 期待 7（property を読むと property が動く）
    return e27_takes_property_value(x.label)



def e29_any_receiver(t: int) -> int:  # 期待 分からない（Any の値の属性は、自分の property でありうる）
    import json
    return json.loads("{}").label


def _big_unit(t: int) -> int:  # 期待 8（分岐 7 つ。閾値以上なので、それ自身の数で出る）
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
    if t == 7:
        return 7
    return 0


def e30_calls_big_unit(t: int) -> int:  # 期待 1（閾値以上の関数を呼ぶ所は 1 つの文）
    return _big_unit(t)


def e31_big_and_small(t: int) -> int:  # 期待 4（閾値以上の塊を切り出すと、残りの小さな関数だけが数に入る）
    return _big_unit(t) + three_a(t)


def _ping(t: int) -> int:  # 期待 7（呼び合う _pong と組にまとめる。分岐は組で 6 つ）
    if t > 10:
        return _pong(t - 1)
    if t > 5:
        return 1
    if t > 3:
        return 2
    return 0


def _pong(t: int) -> int:  # 期待 7
    if t > 10:
        return _ping(t - 1)
    if t > 5:
        return 1
    if t > 3:
        return 2
    return 0


def e32_mutual(t: int) -> int:  # 期待 7（組は 7 で閾値未満なので、呼ぶ側へ展開される）
    return _ping(t)


def e33_nested_big(t: int) -> int:  # 期待 8（中に書いた関数は、閾値以上でも外の関数の一部。中に書いた def は分岐ではない）
    def inner(v: int) -> int:
        if v == 1:
            return 1
        if v == 2:
            return 2
        if v == 3:
            return 3
        if v == 4:
            return 4
        if v == 5:
            return 5
        if v == 6:
            return 6
        if v == 7:
            return 7
        return 0

    return inner(t)


class _Measure(Protocol):
    unit: str

    def measure(self, t: int) -> int: ...


class _SmallRuler:
    unit: str = "cm"

    def measure(self, t: int) -> int:
        return six(t)


class _BigRuler:
    unit: str = "m"

    def measure(self, t: int) -> int:
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
        if t == 7:
            return 7
        return 0


class _NoUnit:
    def measure(self, t: int) -> int:
        return three_a(t)


def e34_protocol(m: _Measure, t: int) -> int:  # 期待 7（Protocol のメンバーを呼ぶ所は、ty が満たすと答えたクラスの実装を数える。_NoUnit は満たさず、_BigRuler.measure は閾値以上なので 1 つの文）
    return m.measure(t)


def e35_protocol_local(t: int) -> int:  # 期待 7（Protocol の型を書いても、ty は代入した _SmallRuler に型を絞るので、行き先が決まる）
    m: _Measure = _SmallRuler()
    return m.measure(t)


class _HasFn(Protocol):
    fn: Callable[[int], int]


@dataclass(frozen=True)
class _FnHolder:
    fn: Callable[[int], int]


_HOLDER = _FnHolder(fn=six)


def e36_protocol_field(h: _HasFn, t: int) -> int:  # 期待 1（Protocol の欄の値を呼ぶ所は 1 つの文。six は _FnHolder(fn=six) を書いた所で数える）
    return h.fn(t)


class _Addable(Protocol):
    def __add__(self, other: "_Num") -> int: ...


def e37_protocol_dunder(a: _Addable, b: _Num) -> int:  # 期待 1（Protocol の値の演算子は 1 つの文。_Num.__add__ は、実装を定義したモジュールの最上位で数える）
    return a + b

# <module> 期待 13（six・three_a・three_b。表・欄・登録として、ここで名前を書いた）
