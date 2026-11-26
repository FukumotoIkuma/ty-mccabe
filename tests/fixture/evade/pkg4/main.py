"""親のパッケージ（evade.pkg4）の最上位は、このモジュールより先に動く。閾値 8 で測る。"""

from evade.checks import three_b

from . import flag

saved = three_b(flag)

# <module> 期待 7（evade.pkg4 の three_a の 3 と、three_b の 3）
