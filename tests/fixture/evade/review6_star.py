"""`from pkg import *` は、`__all__` に挙げたサブモジュールを実行する。閾値 8 で測る。"""

from evade.checks import three_b
from evade.pkg6 import *  # noqa: F403

saved = three_b(0)

# <module> 期待 7（evade.pkg6.child の three_a の 3 と、three_b の 3）
