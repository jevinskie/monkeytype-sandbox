from __future__ import annotations

import functools
import sys
from collections.abc import Callable
from types import GenericAlias
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    ParamSpec,
    TypeVar,
    reveal_type,
)

if not TYPE_CHECKING:
    from rich import print

from rich import inspect as rinspect

_P = ParamSpec("_P")
_T = TypeVar("_T")
_R_co = TypeVar("_R_co", covariant=True)

if TYPE_CHECKING:
    if sys.version_info >= (3, 14):
        from _typeshed import AnnotateFunc
    else:
        AnnotateFunc = Any


class zlassmethod(Generic[_T, _P, _R_co]):
    _f: Callable[_P, _R_co]
    _i: _T | None = None
    _o: type[_T] | None

    def __init__(self, f: Callable[_P, _R_co], *args: Any, **kwargs: Any) -> None:
        self._f = f
        self._i = None
        self._o = None
        print(
            f"__init__ self: {self} f: {f} f.name: {f.__name__} f.qn: {f.__qualname__} args: {args} kw: {kwargs}"
        )
        rinspect(f, all=True)
        if sys.version_info >= (3, 10):
            self.__name__ = f.__name__
            self.__qualname__ = f.__qualname__

    if sys.version_info >= (3, 14):

        def __class_getitem__(cls, item: Any, /) -> GenericAlias:
            raise NotImplementedError

    @property
    def __func__(self) -> Callable[_P, _R_co]:
        print("__func__")
        assert hasattr(self, "_f")
        return self._f

    def __get__(self, obj: _T | None, objtype: type[_T] | None = None, /) -> Callable[_P, _R_co]:
        print(f"__get__ self: {self} i: {obj} o: {objtype}")
        if obj is None:
            print("__get___ obj is None returning self!")
            return self
        if obj is not None:
            self._i = obj
        if objtype is not None:
            self._o = objtype
        self._o = objtype
        fr = self.__func__
        print(f"__get__ fr: {fr}")
        pfr = functools.partial(fr, obj)
        print(f"__get__ pfr: {pfr}")
        return pfr

    def __set_name__(self, owner: Any, name: Any) -> None:
        print(f"__set_name__ self: {self} owner: {owner} name: {name}")

    if sys.version_info >= (3, 10):
        __name__: str
        __qualname__: str

    # if sys.version_info >= (3, 14):
    #     __annotate__: AnnotateFunc | None

    # @property
    # def __isabstractmethod__(self) -> bool:
    #     print("__isabstractmethod__")
    #     if hasattr(self._f, "__isabstractmethod__"):
    #         return bool(self._f.__isabstractmethod__())
    #     else:
    #         return False

    # if sys.version_info >= (3, 10):
    # @property
    # def wrapped(self) -> Callable[_P, _R_co]:
    #     print("wrapped")
    #     return self._f

    def __repr__(self) -> str:
        return f"<zlassmethod _i: {self._i} _f: {self._f} o: {self._o} at {id(self):#010x}>"


class Bar:
    _n: int

    def __init__(self, n: int) -> None:
        self._n = n

    @zlassmethod
    def bar(self, a: int, b: int, /) -> int:
        # print(f"Bar._bar self: {self} a: {a} b: {b}")
        # print(f"Bar._bar Bar.bar: {Bar.bar}")
        # print(hasattr(getattr(Bar, "bar"), "wrapped"))
        # print(getattr(Bar, "bar").wrapped)
        # print(id(getattr(Bar.bar, "wrapped")))
        # print(f"id(Bar.bar): {id(Bar.bar):#010x}")
        # print(f"type(Bar.bar): {type(Bar.bar)}")
        # print(f"foo3: {vars(Bar)['bar'].wrapped}")
        # print(f"Bar.bar self._n: {self._n}")
        return a + b

    def plain(self, a: int, b: int) -> int:
        print(f"plain self: {self} a: {a} b: {b}")
        return a + b


b3 = Bar(7)

# print(b3)
# print(b3.bar)
# print(b3.bar(Bar, 1, 2))
print(b3.plain)
print(b3.bar(1, 2))

rinspect(Bar.plain, all=True)
rinspect(b3.plain, all=True)


if TYPE_CHECKING:
    reveal_type(b3)
    reveal_type(b3.plain)
    reveal_type(type(b3).plain)
    reveal_type(b3.plain(1, 2))
    reveal_type(b3.bar)
    reveal_type(b3.bar(1, 2))
