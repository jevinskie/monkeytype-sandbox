from __future__ import annotations

import importlib
from collections.abc import Callable
from functools import partial
from types import MappingProxyType, MethodType, ModuleType
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
        # pass
    except ImportError:
        pass

_T = TypeVar("_T")
_F = TypeVar("_F", bound=Callable[..., Any])
_P = ParamSpec("_P")
_R_co = TypeVar("_R_co", covariant=True)


class NamePath(NamedTuple):
    module: str
    qualname: str


class ResolvedNamePath(NamedTuple):
    namepath: NamePath
    module: ModuleType
    value: Any


class AnnotatedMethodInfo(NamedTuple):
    resolved: ResolvedNamePath
    name: str
    method: MethodType


AMI = AnnotatedMethodInfo
AMIS = cast(AnnotatedMethodInfo, object())


def dotted_getattr(obj: Any, path: str) -> Any:
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


def resolve_namepath(np: NamePath) -> ResolvedNamePath:
    mod = importlib.import_module(np.module)
    val = dotted_getattr(mod, np.qualname)
    return ResolvedNamePath(np, mod, val)


def get_namepath(val: Any) -> NamePath:
    if not hasattr(val, "__module__"):
        raise ValueError(f"Can't get NamePath: __module__ missing from val: {val}")
    if not hasattr(val, "__qualname__"):
        raise ValueError(f"Can't get NamePath: __qualname__ missing from val: {val}")
    return NamePath(val.__module__, val.__qualname__)


class AnnotatedMethod(Generic[_T, _P, _R_co]):
    _rnp: ResolvedNamePath
    _n: str
    _f: Callable[Concatenate[_T, _P], _R_co]
    _fmeta: Callable[Concatenate[_T, _P], _R_co]

    # FIXME: Need weakref?

    def __init__(self, func: Callable[Concatenate[_T, _P], _R_co], namepath: NamePath) -> None:
        self._rnp = resolve_namepath(namepath)
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

    def __func__(self) -> Callable[Concatenate[_T, _P], _R_co]:
        return self._f

    def __set_name__(self, obj: Any, name: str) -> None:
        self._n = name
        if obj is None:
            raise ValueError(f"None obj? {obj}")
        if not hasattr(obj, "_infos"):
            setattr(obj, "_infos", {})
        nt = self.as_ntuple()
        obj._infos[self._rnp.namepath] = nt
        # Argument "meta" has incompatible type "AnnotatedMethodInfo"; expected "_P.kwargs"
        p = partial(self._f, meta=nt)  # type: ignore
        self._fmeta = cast(Callable[Concatenate[_T, _P], _R_co], p)

    def as_ntuple(self) -> AnnotatedMethodInfo:
        return AnnotatedMethodInfo(self._rnp, self._n, cast(MethodType, self))


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
        if not hasattr(self, "_infos"):
            self._infos = {}
        self._infos_ro = MappingProxyType(self._infos)

    def rewrite_type(self, namepath: NamePath, a: int, b: int) -> None:
        rewriter = self.registry.get(namepath)
        print(f"rewriter: {rewriter}")
        return rewriter(self, 1, 2)

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


if __name__ == "__main__":
    tr = TypeRewriter()
    print(f"tr.fancy(1, 2): {tr.fancy(1, 2)}")
    print(f"TypeRewriter.mancy(b, 7, 11): {TypeRewriter.mancy(tr, 7, 11)}")
    print("rw_ty typing.Union:")
    np_t = NamePath("typing", "Union")
    np_c = NamePath("pycparser.c_ast", "Union")
    print(tr.rewrite_type(np_t, 10, 20))
    print("rw_ty typing.Union:")
    print(tr.rewrite_type(np_c, 100, 200))
