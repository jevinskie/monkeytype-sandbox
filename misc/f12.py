from __future__ import annotations

import functools
import sys
from collections.abc import Callable
from types import GenericAlias
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    Generic,
    ParamSpec,
    TypeVar,
    cast,
    overload,
    reveal_type,
)

_P = ParamSpec("_P")
_T = TypeVar("_T")
_R_co = TypeVar("_R_co", covariant=True)

if TYPE_CHECKING:
    if sys.version_info >= (3, 14):
        from _typeshed import AnnotateFunc
    else:
        AnnotateFunc = Any


class glassmethod(Generic[_T, _P, _R_co]):
    def __init__(self, f: Callable[Concatenate[type[_T], _P], _R_co], /) -> None: ...

    if sys.version_info >= (3, 14):

        def __class_getitem__(cls, item: Any, /) -> GenericAlias: ...

        __annotate__: AnnotateFunc | None

    @overload
    def __get__(self, instance: _T, owner: type[_T] | None = None, /) -> Callable[_P, _R_co]: ...
    @overload
    def __get__(self, instance: None, owner: type[_T], /) -> Callable[_P, _R_co]: ...
    @property
    def __func__(self) -> Callable[Concatenate[type[_T], _P], _R_co]: ...
    @property
    def __isabstractmethod__(self) -> bool: ...

    if sys.version_info >= (3, 10):
        __name__: str
        __qualname__: str

        @property
        def __wrapped__(self) -> Callable[Concatenate[type[_T], _P], _R_co]: ...


class glassmethod2(Generic[_T, _P, _R_co]):
    def __init__(self, f: Callable[Concatenate[type[_T], _P], _R_co], /) -> None:
        raise RuntimeError

    if sys.version_info >= (3, 14):

        def __class_getitem__(cls, item: Any, /) -> GenericAlias:
            raise RuntimeError

        __annotate__: AnnotateFunc | None

    def __get__(self, instance: _T | None, owner: type[_T] | None = None, /) -> Callable[_P, _R_co]:
        raise RuntimeError

    @property
    def __func__(self) -> Callable[Concatenate[type[_T], _P], _R_co]:
        raise RuntimeError

    @property
    def __isabstractmethod__(self) -> bool:
        raise RuntimeError

    if sys.version_info >= (3, 10):
        __name__: str
        __qualname__: str

        @property
        def __wrapped__(self) -> Callable[Concatenate[type[_T], _P], _R_co]:
            raise RuntimeError


class zlassmethod(Generic[_T, _P, _R_co]):
    def __init__(self, f: Callable[Concatenate[type[_T], _P], _R_co], /) -> None:
        raise NotImplementedError

    if sys.version_info >= (3, 14):

        def __class_getitem__(cls, item: Any, /) -> GenericAlias:
            raise NotImplementedError

        __annotate__: AnnotateFunc | None

    @overload
    def __get__(self, instance: _T, owner: type[_T] | None = None, /) -> Callable[_P, _R_co]:
        raise NotImplementedError

    @overload
    def __get__(self, instance: None, owner: type[_T], /) -> Callable[_P, _R_co]:
        return NotImplementedError

    @property
    def __func__(self) -> Callable[Concatenate[type[_T], _P], _R_co]:
        raise NotImplementedError

    @property
    def __isabstractmethod__(self) -> bool:
        raise NotImplementedError

    if sys.version_info >= (3, 10):
        __name__: str
        __qualname__: str

        @property
        def __wrapped__(self) -> Callable[Concatenate[type[_T], _P], _R_co]:
            raise NotImplementedError


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
bar = cast("classmethod[Foo, [int, int], int]", bar_raw)
bf_raw = functools.partial(bar_raw.__func__, Foo)
bf = cast(Callable[[int, int], int], bf_raw)
print(bar.__wrapped__)
# print(bar.__func__(Foo, 1000, 2000))
print(bf_raw(10_000, 20_000))
print(bf(10_000, 20_000))

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
