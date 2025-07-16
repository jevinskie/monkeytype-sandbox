from __future__ import annotations

import sys as sys
import types
from typing import Any, cast

from rich import print

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


class DummyRewriterMeta(type):
    # def __new__(cls, *args, **kwargs) -> None:
    def __new__(
        cls: type[DummyRewriterMeta],
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        **kwargs: Any,
    ) -> type[DummyRewriterMeta]:
        print(
            f"DummyRewriterMeta.__new__() pre cls: {cls} bases: {bases} ns: {namespace} kwargs: {kwargs}"
        )
        r = super().__new__(cls, name, bases, namespace, **kwargs)
        print(f"DummyRewriterMeta.__new__() post cls: {cls} r: {r}")
        return r

    def __init__(self, *args, **kwargs) -> None:
        print(f"DummyRewriterMeta.__init__() pre self: {self} args: {args} kwargs: {kwargs}")
        super().__init__(*args, **kwargs)
        print(f"DummyRewriterMeta.__init__() post self: {self} args: {args} kwargs: {kwargs}")

    def __init_subclass__(cls) -> None:
        print(f"DummyRewriterMeta.__init_subclass__() cls: {cls}")


class DummyRewriter(metaclass=DummyRewriterMeta):
    def __init_subclass__(cls) -> None:
        print(f"DummyRewriter.__init_subclass__() cls: {cls}")


class FE:
    class FEI:
        def fei(self):
            class FEIX(DummyRewriter):
                class FEIY(DummyRewriter):
                    def foo(self):
                        def bar(arg):
                            # traceback.print_stack()
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
