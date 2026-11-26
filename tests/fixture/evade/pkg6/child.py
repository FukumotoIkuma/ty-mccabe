"""`from evade.pkg6 import *` が import するサブモジュール。"""

from evade.checks import three_a

saved = three_a(0)

# <module> 期待 4（three_a の 3）
