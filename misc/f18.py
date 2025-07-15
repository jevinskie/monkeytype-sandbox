import sys
import types

import f18_ext

print("f18 mod top level")


f18_mod_top_frame = sys._getframe()


def f18_get_frame() -> types.FrameType:
    return sys._getframe()


f18_func_frame = f18_get_frame()


def f18_frame_thingy(frame: types.FrameType) -> None:
    print(f"f18_fame_thingy() {frame}")


print("f18_mod_top_frame:")
print(f18_mod_top_frame)
f18_frame_thingy(f18_mod_top_frame)
print("f18_ext module from f18:")
print(f18_ext)
