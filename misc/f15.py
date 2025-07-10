from __future__ import annotations

from collections.abc import Callable
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

if not TYPE_CHECKING:
    from rich import print

if not TYPE_CHECKING:
    from rich import inspect as rinspect
else:

    def rinspect(*args: Any, **kwargs: Any) -> None: ...


_P = ParamSpec("_P")
_T = TypeVar("_T")
_R_co = TypeVar("_R_co", covariant=True)


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
        fr = f.__get__(obj, cls)
        frc = cast(Callable[_P, _R_co], fr)
        if TYPE_CHECKING:
            reveal_type(f)
            reveal_type(fr)
            reveal_type(frc)
        return frc

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
print(b.mathod(1, 2))
print(Bar.mathod(b, 1, 2))
