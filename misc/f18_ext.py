import sys as sys
import traceback
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


class FE:
    class FEI:
        def fei(self):
            class FEIX:
                class FEIY:
                    def foo(self):
                        def bar(arg):
                            traceback.print_stack()
                            return ("flag", sys._getframe(), arg)

                        def bar_wrapper():
                            return bar((sys._getframe(), bar_wrapper, bar))

                        return [bar_wrapper, bar_wrapper(), sys._getframe(), None]

            return FEIX.FEIY()

    stuff_clsvar = FEI().fei().foo()
    stuff_clsvar[-1] = stuff_clsvar[0]()


stuff_glob = FE.FEI().fei().foo()
stuff_glob[-1] = stuff_glob[0]()

print("f18_mod_top_frame:")
print(f18_ext_mod_top_frame)
f18_ext_frame_thingy(f18_ext_mod_top_frame)
