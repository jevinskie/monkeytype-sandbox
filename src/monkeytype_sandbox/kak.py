import functools
import typing

import decorator
from rich import print


def chatty(func, *args, **kwargs):
    print(args, sorted(kwargs.items()))
    return func(*args, **kwargs)


@decorator.decorator(chatty)
def printsum1(x=1, y=2):
    print("printsum1")
    print(x + y)


printsum1(1, 2)
printsum1(x=1, y=2)
printsum1(y=2, x=1)


@decorator.decorator(chatty, kwsyntax=True)
def printsum3(x=1, y=2):
    print("printsum3")
    print(x + y)


printsum3(1, 2)
printsum3(x=1, y=2)
printsum3(y=2, x=1)


def chattywrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(args, sorted(kwargs.items()))
        return func(*args, **kwargs)

    # return functools.wraps(wrapper)
    return wrapper


@chattywrapper
def printsum2(x=1, y=2):
    print("printsum2")
    print(x + y)


printsum2(1, 2)
printsum2(x=1, y=2)
printsum2(y=2, x=1)


def decc(cls, *args, **kwargs):
    print(f"cls: {cls} args: {args} kw: {kwargs}")

    def _h(*args2, **kwargs2):
        print(f"_h cls: {cls} args2: {args2} kw2: {kwargs2}")
        return cls

    return _h


def _decf(
    a: int | None = None,
    b: int | None = None,
    c: int | None = None,
    d: int | None = None,
    *args,
    **kwargs,
):
    print(f"func: args: {args} a: {a} b: {b} c: {c} d: {d} kw: {kwargs}")
    return bool(*args, **kwargs)


# decf = decorator.decorate(_decf)


def decf(
    func, a: int | None = None, b: int | None = None, c: int | None = None, d: int | None = None
):
    return decorator.decorate(func, _decf)


# def decf(f, a: int | None = None, b: int | None = None, c: int | None = None, d: int | None = None,):
#     return decorator.decorate(f, _decf)


# @decc(x="10", y=11)
class _Foo:
    @decf(a=2, b=3, c=4, d="5")
    # @decf()
    def foo(self) -> float:
        s = "foo"
        print(s)
        return float(len(s))


Foo = decc(_Foo, x="10", y=11)


class Bar:
    def bar(self) -> int:
        s = "bar"
        print(s)
        return len(s)


f = Foo()
print(f.foo())

b = Bar()
print(b.bar())

if typing.TYPE_CHECKING:
    typing.reveal_type(decc)
    typing.reveal_type(_decf)
    typing.reveal_type(decf)

    typing.reveal_type(_Foo)
    typing.reveal_type(Foo)
    typing.reveal_type(f)
    typing.reveal_type(Foo.foo)
    typing.reveal_type(f.foo)

    typing.reveal_type(Bar)
    typing.reveal_type(b)
    typing.reveal_type(Bar.bar)
    typing.reveal_type(b.bar)
