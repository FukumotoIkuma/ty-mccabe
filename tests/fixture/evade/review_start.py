callbacks = [lambda: leaf()]  # ファイルの先頭のバイトから書いた変数（モジュールの位置と同じ 0）

from evade.checks import leaf  # noqa: E402


def r02_file_start() -> int:  # 期待 1（一覧の値を呼ぶ所は 1 つの文。lambda はモジュールの最上位の一部）
    return callbacks[0]()

# <module> 期待 2（モジュールの最上位の lambda が呼ぶ leaf）
