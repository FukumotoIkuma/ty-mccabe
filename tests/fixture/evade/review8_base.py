"""stub（review8_child.pyi）でだけ継ぎ方が決まる下位のクラスの根。閾値 8 で測る。"""


class V01Base:
    def v01m(self) -> None:  # 期待 1
        pass


def v01_use(x: V01Base) -> None:  # 期待 7（stub で V01Base を継ぐ V01Child でありうる） 限界 1（ty の実装への移動は、stub のクラスから実行時のソースの下位のクラスを探さない）
    x.v01m()
