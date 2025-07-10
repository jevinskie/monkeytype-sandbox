from __future__ import annotations

import sys
from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    Generic,
    ParamSpec,
    TypeVar,
    overload,
    reveal_type,
)

if not TYPE_CHECKING:
    from rich import print

if not TYPE_CHECKING:
    from rich import inspect as rinspect
else:

    def rinspect(*args: Any, **kwargs: Any) -> None: ...


_P = ParamSpec("_P")
_T = TypeVar("_T")
_R_co = TypeVar("_R_co", covariant=True)

if TYPE_CHECKING:
    if sys.version_info >= (3, 14):
        from _typeshed import AnnotateFunc
    else:
        AnnotateFunc = Any


class Mathod(Generic[_T, _P, _R_co]):
    _f: Callable[Concatenate[_T, _P], _R_co]

    def __init__(self, func: Callable[Concatenate[_T, _P], _R_co]) -> None:
        print(f"Mathod.__init__ func: {func}")
        self._f = func

    @overload
    def __get__(self, obj: None, cls: type, /) -> Callable[Concatenate[_T, _P], _R_co]: ...
    @overload
    def __get__(self, obj: _T, cls: type[_T] | None = None, /) -> Callable[_P, _R_co]: ...
    def __get__(
        self, obj: _T | None, cls: type[_T] | None = None, /
    ) -> Callable[Concatenate[_T, _P], _R_co] | Callable[_P, _R_co]:
        print(f"Mathod.__get__ self: {self} obj: {obj} cls: {cls}")
        if obj is None:
            # fr2: Callable[Concatenate[_T, _P], _R_co] = self._f
            fr2 = self._f
            if TYPE_CHECKING:
                reveal_type(fr2)
            return fr2
        f = self._f
        if TYPE_CHECKING:
            reveal_type(f)
        fr: Callable[_P, _R_co] = f.__get__(obj, cls)
        # fr = f.__get__(obj, cls)
        if TYPE_CHECKING:
            reveal_type(fr)
        return fr

    def __set_name__(self, owner: Any, name: Any) -> None:
        print(f"Mathod.__set_name__ self: {self} owner: {owner} name: {name}")


class Bar:
    _n: int

    def __init__(self, n: int) -> None:
        self._n = n

    def plain(self, a: int, b: int) -> int:
        print(f"plain self: {self} a: {a} b: {b}")
        return a + b

    @Mathod
    def mathod(self, a: int, b: int) -> int:
        print(f"mathod self: {self} a: {a} b: {b}")
        return a + b


b = Bar(7)


print(Bar.plain)
print(Bar.mathod)
print(b.plain)
print(b.mathod)
print(b.plain(1, 2))
print(b.mathod(1, 2))
print(Bar.mathod(b, 1, 2))
print(getattr(Bar, "mathod"))
print(getattr(b, "mathod"))

# rinspect(Bar.plain, all=True)
# rinspect(b.plain, all=True)
# rinspect(Bar.mathod, all=True)
# rinspect(b.mathod, all=True)

if TYPE_CHECKING:
    reveal_type(b)

    reveal_type(b.plain)
    reveal_type(Bar.plain)
    reveal_type(getattr(b, "plain"))
    reveal_type(getattr(Bar, "plain"))

    reveal_type(b.mathod)
    reveal_type(Bar.mathod)
    reveal_type(getattr(Bar, "mathod"))
    reveal_type(getattr(b, "mathod"))

    reveal_type(b.plain(1, 2))
    reveal_type(b.mathod(1, 2))
    reveal_type(Bar.mathod(b, 1, 2))
