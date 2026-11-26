"""stub が属性として宣言したサブモジュールも、import すると実行する。閾値 8 で測る。"""


def u09_import() -> None:  # 期待 7 限界 1（ty の定義への移動は、stub が属性として宣言したサブモジュールを、属性の宣言として答える）
    from evade.pkg9 import child  # noqa: F401
