"""2 回目のレビューで見つかった数え落としの例。閾値 8 で測る。six は分岐 6 つ（複雑度 7）、leaf は分岐 1 つ。"""

import os
from collections.abc import Callable
from typing import Any

from evade import checks
from evade.checks import FLAG, leaf, six


def v01_getattr_module(t: int) -> int:  # 期待 8（getattr の名前が文字列の定数なら checks.six と同じ。モジュールの関数も引く） 限界 2（ty は名前を文字列で引く所を見分けない（getattr の名前が定数でも））
    if t:
        pass
    return getattr(checks, "six")(t)


class _V03Base:
    def m(self, t: int) -> int:  # 期待 1
        return 0


_V03Alias = _V03Base


class _V03Child(_V03Alias):
    def m(self, t: int) -> int:  # 期待 7
        return six(t)


def v03_alias_base(x: _V03Base, t: int) -> int:  # 期待 8（基底を別名で書いた下位のクラスの上書きも辿る）
    if t:
        pass
    return x.m(t)


class _V04Base:
    def m(self, t: int) -> int:  # 期待 1
        return 0


class _V04Child(_V04Base):
    if FLAG:

        def m(self, t: int) -> int:  # 期待 7
            return six(t)

    else:

        def m(self, t: int) -> int:  # 期待 1
            return 0


def v04_conditional_override(x: _V04Base, t: int) -> int:  # 期待 8（if・else の中で同じ名前で定義したメソッドは、どれも上書き）
    if t:
        pass
    return x.m(t)


class _V09A:
    def v09m(self) -> int:  # 期待 1
        return 0


class _V09B:
    def v09m(self) -> int:  # 期待 2
        return leaf()


def v09_getattr_any(x: _V09A | Any) -> int:  # 期待 分からない（名前が定数の getattr でも、Any を含む受け手は _V09B.v09m でもありうる） 限界 1（ty は名前を文字列で引く所を見分けない）
    return getattr(x, "v09m")()


class _V09C:
    v09n, v09spare = 1, 0


def v09b_tuple_attr_any(x: Any) -> int:  # 期待 分からない（分割代入で置いた属性も、自分のクラスの名前）
    return x.v09n


def _v11_deco(f: Callable[[], int]) -> Callable[[], int]:  # 期待 4
    if os.environ.get("a"):
        pass
    if os.environ.get("b"):
        pass
    if os.environ.get("c"):
        pass
    return f


@_v11_deco
def v11_decorated() -> int:  # 期待 5（デコレータは def を実行する外の単位で数え、付けた関数には足さない）
    if os.environ.get("a"):
        return 1
    if os.environ.get("b"):
        return 2
    if os.environ.get("c"):
        return 3
    if os.environ.get("d"):
        return 4
    return 0


def v11_use() -> int:  # 期待 8（デコレータを付けた関数を呼ぶ）
    if os.environ.get("a"):
        pass
    if os.environ.get("b"):
        pass
    if os.environ.get("c"):
        pass
    return v11_decorated()


class _V14A:
    def m(self, t: int) -> int:  # 期待 1
        return 0


class _V14B(_V14A):
    def m(self, t: int) -> int:  # 期待 7
        return six(t)


def super() -> _V14A:  # 期待 1（組み込みの super を隠す、自分の関数）
    return _V14A()


def v14_own_super(t: int) -> int:  # 期待 8（自分の super が返す値のメソッドは、下位のクラスの上書きも呼びうる）
    if t:
        pass
    return super().m(t)


class _V17:
    def __len__(self) -> int:  # 期待 7
        return six(0)


def v17_len(x: _V17) -> int:  # 期待 8（len が呼ぶ __len__ は、値の型から ty に引く） 限界 2（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（len の __len__））
    if x is None:
        pass
    return len(x)


# <module> 期待 5（クラスの本体の if の 1 と、デコレータ _v11_deco の 3。特殊メソッドは使う所で数え、デコレータが受け取った関数を呼ぶことは値の流れなので数えない）
