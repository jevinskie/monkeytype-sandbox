from __future__ import annotations

import functools
import typing

import decorator

if not typing.TYPE_CHECKING:
    from rich import print


def chatty(func, *args, **kwargs):
    print(args, sorted(kwargs.items()))
    return func(*args, **kwargs)


@decorator.decorator(chatty)
def printsum1(x: int = 1, y: int = 2) -> float:
    print("printsum1")
    print(x + y)
    return float(x + y)


printsum1(1, 2)
printsum1(x=1, y=2)
printsum1(y=2, x=1)


@decorator.decorator(chatty, kwsyntax=True)
def printsum3(x: int = 1, y: int = 2) -> float:
    print("printsum3")
    print(x + y)
    return float(x + y)


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
def printsum2(x: int = 1, y: int = 2) -> float:
    print("printsum2")
    print(x + y)
    return float(x + y)


printsum2(1, 2)
printsum2(x=1, y=2)
printsum2(y=2, x=1)

_F = typing.TypeVar("_F", bound=typing.Callable[..., typing.Any])


def cw2(_f: _F) -> _F:
    @functools.wraps(_f)
    def wrapper(*args, **kwargs):
        print(args, sorted(kwargs.items()))
        return _f(*args, **kwargs)

    # return functools.wraps(wrapper)
    return wrapper


@cw2
def printsum4(x: int = 1, y: int = 2) -> float:
    print("printsum4")
    print(x + y)
    return float(x + y)


printsum4(1, 2)
printsum4(x=1, y=2)
printsum4(y=2, x=1)

if typing.TYPE_CHECKING:
    typing.reveal_type(printsum1)
    typing.reveal_type(printsum2)
    typing.reveal_type(printsum3)
    typing.reveal_type(printsum4)


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


# decf = decorator.decorator(_decf)


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
