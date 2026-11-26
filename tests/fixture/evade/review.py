"""レビューで見つかった数え落としの例。閾値 8 で測る。leaf は分岐 1 つ（複雑度 2）。"""

from collections.abc import Callable
from dataclasses import InitVar, dataclass
from typing import Any, ClassVar, SupportsAbs
from typing import Protocol as P

from evade.checks import FLAG, leaf, six


class _AliasChecker(P):
    def alias_check(self) -> int: ...


class _AliasImpl:
    def alias_check(self) -> int:
        return leaf()


def r01_protocol_alias(c: _AliasChecker) -> int:  # 期待 2（別名で import した Protocol も Protocol。満たす _AliasImpl の実装を数える）
    return c.alias_check()


def r03_any_callee(cb: Any) -> int:  # 期待 1（型の分からない値を呼ぶ所は 1 つの文）
    return cb()


class _UA:
    def ua_check(self) -> int:
        return 0


class _UB:
    def ua_check(self) -> int:
        return leaf()


def r04_union_any(x: _UA | Any) -> int:  # 期待 分からない（Any を含む共用型の受け手。_UB.ua_check でもありうる）
    return x.ua_check()


class _Neg:
    def __neg__(self) -> int:
        return leaf()


def r04b_any_dunder(x: Any) -> int:  # 期待 1（Any の値の演算子は 1 つの文。_Neg.__neg__ でもありうるが、ty は型の分からない値の行き先を答えない）
    return -x


class _NeedsReady(P):
    ready: int

    def rd_check(self) -> int: ...


class _ReadyImpl:
    if FLAG:
        ready = 1

    def rd_check(self) -> int:
        return leaf()


def r06_class_if(x: _NeedsReady) -> int:  # 期待 2（クラスの本体の if の中で定義した名前も持つので、_ReadyImpl は満たす。その実装を数える）
    return x.rd_check()


class _RBase:
    def rb_check(self) -> int:
        return 0


class _RImpl(_RBase):
    rb_check = staticmethod(leaf)


class _RProto(P):
    def rb_check(self) -> int: ...


def r07_attr_shadow(x: _RProto) -> int:  # 期待 1（下位のクラスの欄に入れた leaf は、staticmethod(leaf) を書いた所で数える）
    return x.rb_check()


class _Abs:
    def __abs__(self) -> int:
        return leaf()


def r08_lib_protocol(x: SupportsAbs[int]) -> int:  # 期待 2（ライブラリの Protocol を満たす自分の実装 _Abs.__abs__ も数える）
    return x.__abs__()


def r08b_lib_protocol_builtin(x: SupportsAbs[int]) -> int:  # 期待 1（abs() が呼ぶ特殊メソッドも、Protocol の値なら 1 つの文）
    return abs(x)


class _MA:
    def __invert__(self) -> int:
        return 0


class _MB(_MA):
    pass


class _MC(_MA):
    def __invert__(self) -> int:
        return leaf()


class _MD(_MB, _MC):
    pass


def r09_c3(x: _MD) -> int:  # 期待 2（継承の順は C3。_MD, _MB, _MC, _MA の順で _MC.__invert__）
    return ~x


class _BoolBase:
    def __bool__(self) -> bool:
        return True


class _BoolChild(_BoolBase):
    def __bool__(self) -> bool:
        return leaf() > 0


def r10_dunder_override(x: _BoolBase) -> int:  # 期待 2（真偽の判定が呼ぶ __bool__ の、下位のクラスの上書き） 限界 1（ty は暗に呼ぶ特殊メソッドを答えない（真偽の判定の __bool__））
    return 1 if x else 0


class _Gt:
    def __gt__(self, other: int) -> bool:
        return leaf() > 0


def r11a_reflected(x: _Gt) -> bool:  # 期待 2（0 < x は x.__gt__ を呼ぶ） 限界 1（ty は暗に呼ぶ特殊メソッドを答えない（比較の __gt__））
    return 0 < x


class _RAdd:
    def __radd__(self, other: int) -> int:
        return leaf()


def r11b_radd(x: _RAdd) -> int:  # 期待 2（v += x は x.__radd__ を呼びうる） 限界 1（ty は暗に呼ぶ特殊メソッドを答えない（+= の __radd__））
    v = 0
    v += x
    return v


def r11c_subscript_value(xs: list[_Neg]) -> int:  # 期待 2（添字の式の値の型）
    return -xs[0]


def _neg_impl(self: "_AttrNeg") -> int:
    return leaf()


class _AttrNeg:
    __neg__ = _neg_impl


def r11d_attr_dunder(x: _AttrNeg) -> int:  # 期待 2（ty は代入で置いた __neg__ の _neg_impl を - の位置で答える）
    return -x


class _CompBool:
    def __bool__(self) -> bool:
        return leaf() > 0


def r11e_comprehension_if(x: _CompBool) -> list[int]:  # 期待 2（内包表記の if の真偽の判定） 限界 1（ty は暗に呼ぶ特殊メソッドを答えない（内包表記の if の __bool__））
    return [0 for _ in (0,) if x]


class _Cursor:
    def __next__(self) -> int:
        return leaf()


class _Seq:
    def __iter__(self) -> _Cursor:
        return _Cursor()


def r11f_next(x: _Seq) -> int:  # 期待 3（for の 1 と、__iter__ が返す _Cursor の __next__ が呼ぶ leaf の 1。ty が __iter__ の戻り値の型から引く） 限界 2（ty は暗に呼ぶ特殊メソッドを答えない（for の __next__））
    total = 0
    for v in x:
        total += v
    return total



class _SetOnly:
    def __getitem__(self, i: int) -> int:
        return 0

    def __setitem__(self, i: int, v: int) -> None:
        leaf()


def r22_subscript_read(x: _SetOnly) -> int:  # 期待 1（読むだけなら __setitem__ は動かない）
    return x[0]


def r22b_subscript_write(x: _SetOnly) -> None:  # 期待 2（書けば __setitem__ が動く） 限界 1（ty は暗に呼ぶ特殊メソッドを答えない（添字に書く __setitem__））
    x[0] = 1


class _Desc:
    def __get__(self, obj: object, owner: type | None = None) -> int:
        return leaf()


class _HasDesc:
    item = _Desc()


def r12_descriptor(b: _HasDesc) -> int:  # 期待 2（属性を読むと動く記述子の __get__ が呼ぶ leaf の 1。ty が属性の記述子の型から引く） 限界 1（ty は記述子の __get__ を答えない）
    return b.item


class _Runner:
    def run_cb(self, cb: Callable[[], int]) -> int:  # 期待 1（引数で受けたコールバックを呼ぶ所は 1 つの文。leaf は _m(leaf) を書いた所で数える）
        return cb()


_m = _Runner().run_cb
_m(leaf)

_ALIAS_A: list[Callable[[], int]] = []
_ALIAS_B = _ALIAS_A
_ALIAS_B.append(leaf)


def r14_alias() -> int:  # 期待 1（一覧の値を呼ぶ所は 1 つの文。leaf は _ALIAS_B.append(leaf) を書いた所で数える）
    return _ALIAS_A[0]()



def _register(xs: list[Callable[[], int]]) -> None:  # 期待 2（leaf を書いたのはここ）
    xs.append(leaf)


_REG_A: list[Callable[[], int]] = []
_register(_REG_A)


def r14b_param_append() -> int:  # 期待 1（leaf は _register の中で書いたので、_register で数える）
    return _REG_A[0]()


def _keep(xs: list[Callable[[], int]]) -> int:
    return len(xs)


_REG_C: list[Callable[[], int]] = [six]
_REG_D: list[Callable[[], int]] = [leaf]
_keep(_REG_C)
_keep(_REG_D)


def r14c_no_backflow() -> int:  # 期待 1（一覧の値を呼ぶ所は 1 つの文）
    return _REG_D[0]()


_TABLE2 = {"a": leaf}


def r14d_dict_get() -> int:  # 期待 2（dict の get が返す値）
    f = _TABLE2.get("a")
    return f() if f else 0


class _CallMe:
    def __call__(self) -> int:
        return leaf()


def r15a_call_result() -> int:  # 期待 2（作ったものを呼ぶ所の __call__ は、値の型から ty に引く）
    return _CallMe()()


_FN: Callable[[], int] = leaf


class _CbBox:
    @property
    def callback(self) -> Callable[[], int]:
        return _FN


def r15b_property_call(b: _CbBox) -> int:  # 期待 1（property が返した値を呼ぶ所は 1 つの文。leaf は _FN = leaf を書いた所で数える）
    return b.callback()


class _Mgr:
    def __enter__(self) -> Callable[[], int]:
        return _FN

    def __exit__(self, *a: object) -> None:
        return None


def r15c_with_enter(m: _Mgr) -> int:  # 期待 1（with の値を呼ぶ所は 1 つの文）
    with m as cb:
        return cb()


def _apply_cb(cb: Callable[[], int]) -> int:  # 期待 1（引数で受けたコールバックを呼ぶ所は 1 つの文）
    return cb()


def r16a_starred() -> int:  # 期待 2
    return _apply_cb(*(), leaf)


@dataclass
class _KwBox:
    cb: Callable[[], int]


_KW = _KwBox(**{"cb": leaf})


def r16b_kwargs(b: _KwBox) -> int:  # 期待 1（欄の値を呼ぶ所は 1 つの文。leaf は _KwBox(**{"cb": leaf}) を書いた所で数える）
    return b.cb()


@dataclass
class _CvBox:
    kind: ClassVar[str] = "x"
    cb: Callable[[], int]


_CV = _CvBox(leaf)


def r16c_classvar(b: _CvBox) -> int:  # 期待 1（欄の値を呼ぶ所は 1 つの文）
    return b.cb()


@dataclass
class _IvBox:
    n: int
    cb: InitVar[Callable[[], int]]

    def __post_init__(self, cb: Callable[[], int]) -> None:  # 期待 1（引数の値を呼ぶ所は 1 つの文。leaf は _IvBox(0, leaf) を書いた所で数える）
        cb()


_IV = _IvBox(0, leaf)


def r17a_lambda_default() -> int:  # 期待 2（lambda の既定値の式は、外の関数の中で動く）
    f = lambda x=leaf(): x  # noqa: E731
    return f()


def _deco_real(fn: Callable[[], int]) -> Callable[[], int]:  # 期待 2
    if FLAG:
        return fn
    return fn


_DS = [_deco_real]


def _factory2() -> Callable[[Callable[[], int]], Callable[[], int]]:
    return _DS[0]


@_factory2()
def r17b_decorated() -> int:  # 期待 1（デコレータを作る関数が返したデコレータは値。_deco_real は _DS = [_deco_real] を書いた所で数える）
    return 0


def _pump(step: Callable[[bool], None], x: bool) -> None:  # 期待 2（引数で受けたコールバックを呼ぶ所は 1 つの文なので、r18_outer・inner とは組にならない）
    if x:
        step(False)


def r18_outer(x: bool) -> None:  # 期待 3（中に書いた関数は外の関数と同じ組。中に書いた def は分岐ではない）
    if x:
        pass

    def inner(y: bool) -> None:  # 期待 3
        _pump(inner, y)

    inner(x)

# <module> 期待 10（six・leaf・_deco_real と、クラスの本体の if の 1）
