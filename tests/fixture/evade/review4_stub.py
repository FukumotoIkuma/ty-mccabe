"""自分のプロジェクトの stub（review4_stub.pyi）があるモジュール。"""

from evade.checks import six


class X05:
    def work(self, t: int) -> int:  # 期待 7
        return six(t)
