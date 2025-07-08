import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, ParamSpec, cast, reveal_type

P = ParamSpec("P")


class Foo:
    def regular_meth(self, a: int, b: int) -> int:
        print(f"Foo.regular_meth self: {self} a: {a} b: {b}")
        return a + b

    @classmethod
    def class_meth(cls, a: int, b: int) -> int:
        print(f"Foo.class_meth cls: {cls} a: {a} b: {b}")
        return a + b

    @staticmethod
    def static_meth(a: int, b: int) -> int:
        print(f"Foo.static_meth a: {a} b: {b}")
        return a + b


def _bar(cls: type[Foo], a: int, b: int, /) -> int:
    print(f"_bar cls: {cls} a: {a} b: {b}")
    return a + b


bar_raw: classmethod[Foo, [int, int], int] = classmethod(_bar)
bar = cast(classmethod[Foo, [int, int], int], bar_raw)
bf_raw = functools.partial(bar_raw.__func__, Foo)
bf = cast(Callable[[int, int], int], bf_raw)
print(bar.__wrapped__)
# print(bar.__func__(Foo, 1000, 2000))
print(bf_raw(10_000, 20_000))

f = Foo()
print(f)
print(f.regular_meth(1, 2))
print(f.class_meth(10, 20))
print(f.static_meth(100, 200))
print(type(f).static_meth(400, 500))

if TYPE_CHECKING:
    reveal_type(bar_raw)
    reveal_type(bar)
    reveal_type(bar.__wrapped__)
    reveal_type(bar.__func__)
    reveal_type(bf_raw)
    reveal_type(bf)
