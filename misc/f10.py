from __future__ import annotations

from typing import TYPE_CHECKING, reveal_type

from rich import inspect as rinspect


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


f = Foo()
print(f)
print(f.regular_meth(1, 2))
print(f.class_meth(10, 20))
print(f.static_meth(100, 200))
print(type(f).static_meth(400, 500))
# print(f.class_meth.__wrapped__)
# print(f.static_meth.__wrapped__)
rinspect(Foo.class_meth, all=True)
rinspect(f.class_meth, all=True)
print(dir(Foo.class_meth))
print(dir(f.class_meth))
print(vars(Foo.class_meth))
print(vars(f.class_meth))

print(dir(Foo.regular_meth))
print(dir(f.regular_meth))
print(vars(Foo.regular_meth))
print(vars(f.regular_meth))

try:
    print(getattr(Foo.class_meth, "__wrapped__"))
except Exception:
    pass
try:
    print(Foo.static_meth.__wrapped__)
except Exception:
    pass


if TYPE_CHECKING:
    reveal_type(Foo)
    reveal_type(f)
    reveal_type(f.regular_meth)
    reveal_type(f.class_meth)
    reveal_type(f.static_meth)
    reveal_type(Foo.regular_meth)
    reveal_type(Foo.class_meth)
    reveal_type(Foo.static_meth)
    reveal_type(f.class_meth.__wrapped__)
    reveal_type(f.static_meth.__wrapped__)
    reveal_type(Foo.class_meth.__wrapped__)
    reveal_type(Foo.static_meth.__wrapped__)
