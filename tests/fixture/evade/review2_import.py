"""ドットで区切った import は、親のパッケージの初期化も実行する。閾値 8 で測る。"""

import evade.pkg2.child
from evade.checks import FLAG

if FLAG:
    pass

# <module> 期待 8（if の 1 と、evade.pkg2 の three_a の 3 と、evade.pkg2.child の three_b の 3）
