"""組み込みの関数を修飾名・別名で呼ぶ所、reversed、match のガードが暗に呼ぶ特殊メソッド。閾値 8 で測る。"""

import builtins
from builtins import len as size

from evade.checks import six


class _X07:
    def __len__(self) -> int:  # 期待 7
        return six(0)


def x07_qualified(box: _X07) -> int:  # 期待 7 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（len の __len__））
    return builtins.len(box)


def x07_alias(box: _X07) -> int:  # 期待 7 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（len の __len__））
    return size(box)


class _X08:
    def __reversed__(self):  # 期待 7
        six(0)
        return iter(())


def x08_reversed(box: _X08):  # 期待 7 限界 1（ty は組み込みの関数が中で呼ぶ特殊メソッドを答えない（reversed の __reversed__））
    return reversed(box)


class _X09:
    def __bool__(self) -> bool:  # 期待 7
        return six(0) == 0


def x09_guard(box: _X09, t: int) -> int:  # 期待 8（ガード付きの case は C901 の 1。ガードの真偽の判定が __bool__ を呼ぶ） 限界 2（ty は暗に呼ぶ特殊メソッドを答えない（match のガードの __bool__））
    match t:
        case 0 if box:
            return 1
    return 0


# <module> 期待 1（特殊メソッドは、使う所で数える）
