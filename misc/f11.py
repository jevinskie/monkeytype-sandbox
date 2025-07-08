import functools
import typing
from collections.abc import Callable

P = typing.ParamSpec("P")


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


def _bar(cls: type, a: int, b: int) -> int:
    print(f"_bar cls: {cls} a: {a} b: {b}")
    return a + b


bar: classmethod[Foo, [int, int], int] = classmethod(_bar)
bfr = functools.partial(bar.__func__, Foo)
bf = typing.cast(Callable[[int, int], int], functools.partial(bar.__func__, Foo))
print(bar.__wrapped__)
print(bar.__func__(Foo, 1000, 2000))
print(bf(10_000, 20_000))

f = Foo()
print(f)
print(f.regular_meth(1, 2))
print(f.class_meth(10, 20))
print(f.static_meth(100, 200))
print(type(f).static_meth(400, 500))

if typing.TYPE_CHECKING:
    typing.reveal_type(bar)
    typing.reveal_type(bfr)
    typing.reveal_type(bf)
