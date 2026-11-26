"""共用型の受け手（モジュールとクラス）に定数の getattr。閾値 8 で測る。"""

from evade import review9_worker


class _U08Local:
    def u08_work(self, t: int) -> int:  # 期待 1
        return 0


def u08_union_receiver(flag: bool, t: int) -> int:  # 期待 7（モジュールの側の u08_work も） 限界 1（ty は名前を文字列で引く所を見分けない（getattr の名前が定数でも））
    receiver = review9_worker if flag else _U08Local()
    return getattr(receiver, "u08_work")(t)
