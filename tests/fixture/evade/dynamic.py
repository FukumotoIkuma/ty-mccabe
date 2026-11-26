"""名前を文字列で引く例。名前が定数なら属性と同じに引き、そうでなければ数える所が決まらないので分からない。"""

import importlib

from evade.checks import leaf


class _Dyn:
    def act(self) -> int:  # 期待 2
        return leaf()


def d1_getattr_const(x: _Dyn) -> int:  # 期待 2（名前が文字列の定数なら x.act と同じ） 限界 1（ty は名前を文字列で引く所を見分けない（getattr の名前が定数でも））
    return getattr(x, "act")()


def d2_getattr_var(x: _Dyn, name: str) -> int:  # 期待 分からない（名前を文字列で引く） 限界 1（ty は名前を文字列で引く所を見分けない）
    return getattr(x, name)()


def d3_import_module(name: str) -> object:  # 期待 分からない（どのモジュールか決まらない） 限界 1（ty は名前を文字列で引く所を見分けない）
    return importlib.import_module(name)


def d4_globals(name: str) -> object:  # 期待 分からない（名前を文字列で引く） 限界 1（ty は名前を文字列で引く所を見分けない）
    return globals()[name]


def d5_dict(x: _Dyn) -> object:  # 期待 分からない（__dict__ から名前で引く） 限界 1（ty は名前を文字列で引く所を見分けない）
    return x.__dict__


# <module> 期待 1
