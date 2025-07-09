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
    Self,
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
    _f: Callable[Concatenate[_T, _P], _R_co]
    _fg: Callable[Concatenate[_T, _P], _R_co] | None
    _i: _T | None = None
    _o: type[_T] | None

    def __init__(self, f: Callable[Concatenate[_T, _P], _R_co], /) -> None:
        self._f = f
        self._fg = None
        self._i = None
        self._o = None
        print(f"__init__ self: {self} f: {f} f.name: {f.__name__} f.qn: {f.__qualname__}")
        if sys.version_info >= (3, 10):
            self.__name__ = f.__name__
            self.__qualname__ = f.__qualname__

    if sys.version_info >= (3, 14):

        def __class_getitem__(cls, item: Any, /) -> GenericAlias:
            raise NotImplementedError

    @property
    def __func__(self) -> Callable[Concatenate[_T, _P], _R_co]:
        print("__func__")
        assert hasattr(self, "_f")
        if self._fg is None:
            print("__func__ init _fg")
            assert self._i is not None

            def fg(*args: _P.args, **kwargs: _P.kwargs) -> _R_co:
                print(f"fg() self: {self} args: {args} kw: {kwargs}")
                assert self._i is not None
                return self._f(self._i, *args, **kwargs)

            print(f"__func__ init _fg fg: {fg} id(fg): {id(fg):#010x}")

            self._fg = fg
        return self._fg

    def __get__(
        self, instance: _T, owner: type[_T] | None = None, /
    ) -> Callable[Concatenate[_T, _P], _R_co]:
        print(f"__get__ self: {self} i: {instance} o: {owner}")
        self._i = instance
        self._o = owner
        fr = self.__func__
        print(f"__get__ fr: {fr}")
        return fr

    if sys.version_info >= (3, 10):
        __name__: str
        __qualname__: str

    if sys.version_info >= (3, 14):
        __annotate__: AnnotateFunc | None

    @property
    def __isabstractmethod__(self) -> bool:
        print("__isabstractmethod__")
        if hasattr(self._f, "__isabstractmethod__"):
            return bool(self._f.__isabstractmethod__())
        else:
            return False

    # if sys.version_info >= (3, 10):
    @property
    def wrapped(self) -> Callable[Concatenate[_T, _P], _R_co]:
        print("wrapped")
        return self._f

    def __repr__(self) -> str:
        return f"<zlassmethod _i: {self._i} _f: {self._f} o: {self._o} at {id(self):#010x}>"


class Bar:
    _n: int

    def __init__(self, n: int) -> None:
        self._n = n

    @zlassmethod
    def bar(self: Self, a: int, b: int, /) -> int:
        print(f"Bar._bar self: {self} a: {a} b: {b}")
        print(f"Bar._bar Bar.bar: {Bar.bar}")
        print(hasattr(Bar.bar, "wrapped"))
        # print(getattr(Bar.bar, "wrapped"))
        # print(id(getattr(Bar.bar, "wrapped")))
        print(f"id(Bar.bar): {id(Bar.bar):#010x}")
        print(f"type(Bar.bar): {type(Bar.bar)}")
        print(f"foo3: {vars(Bar)['bar'].wrapped}")
        print(f"Bar.bar self._n: {self._n}")
        return a + b


b3 = Bar(2)

print(b3)
print(b3.bar)
# print(b3.bar(Bar, 1, 2))
print(b3.bar(1, 2))

if TYPE_CHECKING:
    reveal_type(b3)
    reveal_type(b3.bar)
    reveal_type(b3.bar(1, 2))
