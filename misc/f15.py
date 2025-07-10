from __future__ import annotations

from collections.abc import Callable
from types import MappingProxyType
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

_T = TypeVar("_T")
_F = TypeVar("_F", bound=Callable[..., Any])
_P = ParamSpec("_P")
_R_co = TypeVar("_R_co", covariant=True)


class AnnotatedMethod(Generic[_T, _P, _R_co]):
    _f: Callable[Concatenate[_T, _P], _R_co]
    _mod: str
    _qn: str

    # FIXME: Need weakref?

    def __init__(
        self, func: Callable[Concatenate[_T, _P], _R_co], module: str, qualname: str
    ) -> None:
        self._f = func
        self._mod = module
        self._qn = qualname

    @overload
    def __get__(self, obj: None, cls: type[_T], /) -> Callable[Concatenate[_T, _P], _R_co]: ...
    @overload
    def __get__(self, obj: _T, cls: type[_T] | None = None, /) -> Callable[_P, _R_co]: ...
    def __get__(
        self, obj: _T | None, cls: type[_T] | None = None, /
    ) -> Callable[Concatenate[_T, _P], _R_co] | Callable[_P, _R_co]:
        if obj is None:
            return self._f
        return cast(Callable[_P, _R_co], self._f.__get__(obj, cls))

    def __set_name__(self, obj: Any, name: str) -> None:
        if obj is None:
            raise ValueError(f"none obj? {obj}")
        if not hasattr(obj, "_infos"):
            setattr(obj, "_infos", dict[tuple[str, str], Any]())
        infos: dict[tuple[str, str], Any] = obj._infos
        key = (self._mod, self._qn)
        infos[key] = {"self": self, "name": name}

    if TYPE_CHECKING:
        reveal_type(__get__)


class rewriter:
    _mod: str
    _qn: str

    def __init__(self, module: str, qualname: str) -> None:
        self._mod = module
        self._qn = qualname

    def __call__(self, func: _F) -> _F:
        return cast(_F, AnnotatedMethod(func, self._mod, self._qn))


class TypeRewriter:
    _infos: dict[tuple[str, str], Any]
    _infos_ro: MappingProxyType[tuple[str, str], Any]

    def __init__(self) -> None:
        self._infos_ro = MappingProxyType(self._infos)

    def plain(self, a: int, b: int) -> int:
        print(f"plain() self: {self} a: {a} b: {b}")
        return a + b

    @rewriter("typing", "Union")
    def fancy(self, a: int, b: int) -> int:
        print(f"fancy() self: {self} a: {a} b: {b} infos: {self.infos}")
        return a + b

    @rewriter("pycparser.c_ast", "Union")
    def mancy(self, a: int, b: int) -> int:
        print(f"mancy() self: {self} a: {a} b: {b} infos: {self.infos}")
        return a * b

    @property
    def infos(self) -> MappingProxyType[tuple[str, str], Any]:
        return self._infos_ro

    if TYPE_CHECKING:
        reveal_type(plain)
        reveal_type(fancy)
        reveal_type(mancy)
        reveal_type(infos)


tr = TypeRewriter()
print(f"tr.infos: {tr.infos}")
print(f"TypeRewriter.fancy: {TypeRewriter.fancy}")
print(f"tr.fancy: {tr.fancy}")
print(f"tr.fancy(1, 2): {tr.fancy(1, 2)}")
print(f"TypeRewriter.fancy(b, 1, 2): {TypeRewriter.fancy(tr, 1, 2)}")
print(f"tr.mancy(7, 11): {tr.mancy(7, 11)}")
print(f"TypeRewriter.mancy(b, 7, 11): {TypeRewriter.mancy(tr, 7, 11)}")

if TYPE_CHECKING:
    reveal_type(TypeRewriter.plain)
    reveal_type(tr.plain)
    reveal_type(TypeRewriter.fancy)
    reveal_type(tr.fancy)
    reveal_type(TypeRewriter.mancy)
    reveal_type(tr.mancy)
    reveal_type(TypeRewriter.infos)
    reveal_type(tr.infos)
