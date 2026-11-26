"""継いだ Protocol の実装の、基底を書いたモジュール。最上位の分岐は 7 つで、閾値（8）以上。"""

from evade.checks import FLAG, six

if FLAG == 1:
    pass
if FLAG == 2:
    pass
if FLAG == 3:
    pass
if FLAG == 4:
    pass
if FLAG == 5:
    pass
if FLAG == 6:
    pass
if FLAG == 7:
    pass


class _Base6:
    def m6(self, t: int) -> int:  # 期待 7
        return six(t)


# <module> 期待 8（if の 7。_Base6 だけでは Protocol を満たさない）
