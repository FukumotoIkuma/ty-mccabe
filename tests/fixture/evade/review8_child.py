"""継ぐ基底を実行時に決めるクラス（継ぎ方は stub の review8_child.pyi で決まる）。"""

from typing import Any

from evade.checks import six
from evade.review8_base import V01Base


def _runtime_base() -> Any:  # 期待 1
    return V01Base


class V01Child(_runtime_base()):
    def v01m(self) -> None:  # 期待 7
        six(0)
