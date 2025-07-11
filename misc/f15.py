from __future__ import annotations

from collections.abc import Callable
from functools import partial
from types import MappingProxyType, MethodType
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    Generic,
    NamedTuple,
    ParamSpec,
    TypeVar,
    cast,
    overload,
)

if not TYPE_CHECKING:
    try:
        from rich import print
    except ImportError:
        pass

_T = TypeVar("_T")
_F = TypeVar("_F", bound=Callable[..., Any])
_P = ParamSpec("_P")
_R_co = TypeVar("_R_co", covariant=True)


class NamePath(NamedTuple):
    module: str
    qualname: str


class AnnotatedMethodInfo(NamedTuple):
    namepath: NamePath
    name: str
    method: MethodType


AMI = AnnotatedMethodInfo
AMIS = cast(AnnotatedMethodInfo, None)


class AnnotatedMethod(Generic[_T, _P, _R_co]):
    _np: NamePath
    _n: str
    _f: Callable[Concatenate[_T, _P], _R_co]
    _fmeta: Callable[Concatenate[_T, _P], _R_co]

    # FIXME: Need weakref?

    def __init__(self, func: Callable[Concatenate[_T, _P], _R_co], namepath: NamePath) -> None:
        self._np = namepath
        self._f = func

    @overload
    def __get__(self, obj: None, cls: type[_T], /) -> Callable[Concatenate[_T, _P], _R_co]: ...
    @overload
    def __get__(self, obj: _T, cls: type[_T] | None = None, /) -> Callable[_P, _R_co]: ...
    def __get__(
        self, obj: _T | None, cls: type[_T] | None = None, /
    ) -> Callable[Concatenate[_T, _P], _R_co] | Callable[_P, _R_co]:
        if obj is None:
            return self._fmeta
        p = partial(self._f.__get__(obj, cls), meta=self.as_ntuple())
        return cast(Callable[_P, _R_co], p)

    def __set_name__(self, obj: Any, name: str) -> None:
        self._n = name
        if obj is None:
            raise ValueError(f"None obj? {obj}")
        if not hasattr(obj, "_infos"):
            setattr(obj, "_infos", {})
        nt = self.as_ntuple()
        obj._infos[self._np] = nt
        # Argument "meta" has incompatible type "AnnotatedMethodInfo"; expected "_P.kwargs"
        p = partial(self._f, meta=nt)  # type: ignore
        self._fmeta = cast(Callable[Concatenate[_T, _P], _R_co], p)

    def as_ntuple(self) -> AnnotatedMethodInfo:
        return AnnotatedMethodInfo(self._np, self._n, cast(MethodType, self))


class rewriter:
    _np: NamePath

    def __init__(self, module: str, qualname: str) -> None:
        self._np = NamePath(module, qualname)

    def __call__(self, func: _F) -> _F:
        return cast(_F, AnnotatedMethod(func, self._np))


class TypeRewriter:
    _infos: dict[NamePath, AnnotatedMethodInfo]
    _infos_ro: MappingProxyType[NamePath, AnnotatedMethodInfo]

    def __init__(self) -> None:
        self._infos_ro = MappingProxyType(self._infos)

    @rewriter("typing", "Union")
    def fancy(self, a: int, b: int, /, meta: AMI = AMIS) -> int:
        print(f"fancy() self: {self} a: {a} b: {b} meta: {meta}")
        return a + b

    @rewriter("pycparser.c_ast", "Union")
    def mancy(self, a: int, b: int, /, meta: AMI = AMIS) -> int:
        print(f"mancy() self: {self} a: {a} b: {b} meta: {meta}")
        return a * b

    @property
    def registry(self) -> MappingProxyType[NamePath, AnnotatedMethodInfo]:
        return self._infos_ro

    @property
    def meth_info(self) -> AnnotatedMethodInfo:
        return cast(AMI, None)


if __name__ == "__main__":
    tr = TypeRewriter()
    print(f"tr.fancy(1, 2): {tr.fancy(1, 2)}")
    print(f"TypeRewriter.mancy(b, 7, 11): {TypeRewriter.mancy(tr, 7, 11)}")
