from __future__ import annotations

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


class zlassmethod(Generic[_T, _P, _R_co]):
    _f: Callable[Concatenate[type[_T], _P], _R_co]
    _i: _T
    _o: type[_T] | None

    def __init__(self, f: Callable[Concatenate[type[_T], _P], _R_co], /) -> None:
        print(f"__init__ self: {self} f: {f} f.name: {f.__name__} f.qn: {f.__qualname__}")
        self._f = f
        if sys.version_info >= (3, 10):
            self.__name__ = f.__name__
            self.__qualname__ = f.__qualname__

    if sys.version_info >= (3, 14):

        def __class_getitem__(cls, item: Any, /) -> GenericAlias:
            raise NotImplementedError

    def __get__(
        self, instance: _T, owner: type[_T] | None = None, /
    ) -> Callable[Concatenate[type[_T], _P], _R_co]:
        print(f"__get__ self: {self} i: {instance} o: {owner}")
        self._i = instance
        self._o = owner
        return self._f

    if sys.version_info >= (3, 10):
        __name__: str
        __qualname__: str

    if sys.version_info >= (3, 14):
        __annotate__: AnnotateFunc | None

    @property
    def __func__(self) -> Callable[_P, _R_co]:
        print("__func__")
        assert hasattr(self, "_f")
        return self._f

    @property
    def __isabstractmethod__(self) -> bool:
        print("__isabstractmethod__")
        if hasattr(self._f, "__isabstractmethod__"):
            return bool(self._f.__isabstractmethod__())
        else:
            return False

    if sys.version_info >= (3, 10):

        @property
        def __wrapped__(self) -> Callable[Concatenate[type[_T], _P], _R_co]:
            print("__wrapped__")
            return self._f


class Bar:
    @zlassmethod
    def bar(cls: type[Bar], a: int, b: int, /) -> int:
        print(f"Bar._bar cls: {cls} a: {a} b: {b}")
        print(hasattr(Bar.bar, "__wrapped__"))
        print(getattr(Bar.bar, "__wrapped__"))
        print(id(getattr(Bar.bar, "__wrapped__")))
        print(id(Bar.bar))
        return a + b


b3 = Bar()

print(b3)
print(b3.bar)
# print(b3.bar(Bar, 1, 2))
print(b3.bar(1, 2, 3))

if TYPE_CHECKING:
    reveal_type(b3)
    reveal_type(b3.bar)
    reveal_type(b3.bar(1, 2))
