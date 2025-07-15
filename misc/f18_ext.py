import sys as sys
import types

print("f18_ext mod top level")


# TODO: Add lambas
# TODO: Add generators? ugh
# TODO: Add context managers? ugh

f18_ext_mod_top_frame = sys._getframe()


def f18_ext_get_frame() -> types.FrameType:
    return sys._getframe()


f18_ext_func_frame = f18_ext_get_frame()


def f18_ext_frame_thingy(frame: types.FrameType) -> None:
    print(f"f18_ext_frame_thingy() {frame}")


big_glob = []


class FE:
    class FEI:
        def fei(self):
            class FEIX:
                class FEIXY:
                    def foo(self):
                        def bar(arg):
                            return ("flag", sys._getframe(), arg)

                        def bar_wrapper():
                            return bar((sys._getframe(), bar_wrapper, bar))

                        return [bar_wrapper, bar_wrapper(), sys._getframe(), None]

            return FEIX.FEIXY()

    big_clsvar = FEI().fei().foo()
    big_clsvar[-1] = big_clsvar[0]()
    global big_glob
    big_glob = FEI().fei().foo()
    big_glob[-1] = big_glob[0]()


print("f18_mod_top_frame:")
print(f18_ext_mod_top_frame)
f18_ext_frame_thingy(f18_ext_mod_top_frame)
