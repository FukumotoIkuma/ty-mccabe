"""親のパッケージに stub があっても、実行するのは __init__.py。閾値 8 で測る。"""

from evade.checks import three_b


def y11_local_import() -> int:  # 期待 7（関数の中の相対の import も、親のパッケージを実行する）
    from . import ready

    return three_b(ready)


# <module> 期待 4（evade.pkg5 の three_a の 3）
