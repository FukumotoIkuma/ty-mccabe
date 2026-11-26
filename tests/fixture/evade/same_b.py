from evade import same_a
from evade.checks import six


class Rule(same_a.Rule):
    def apply(self, t: int) -> int:
        return six(t)


class Other:
    def apply(self, t: int) -> int:
        return six(t)

# <module> 期待 1
