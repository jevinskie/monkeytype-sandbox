from __future__ import annotations

import sys as sys
import traceback
import types
from typing import cast

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


def walk_frames(frame: types.FrameType | None) -> None:
    depth = 0

    class F:
        f_back = frame

    frame = cast(types.FrameType, F())
    depth = 0
    while frame := frame.f_back:
        print(f"[{depth}] name: {frame.f_code.co_name}")
        depth += 1


walk_frames(FE.stuff_clsvar[1][1])
# Current:
# [0] name: bar
# [1] name: bar_wrapper
# [2] name: foo
# [3] name: FE
# [4] name: <module>
# Desired:
# [0] name: bar
# [1] name: bar_wrapper
# [2] name: foo
# [3] name: FE
# [4] name: misc.f18_ext
