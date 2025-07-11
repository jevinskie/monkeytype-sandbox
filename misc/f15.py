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
    Protocol,
    Self,
    TypeVar,
    cast,
    overload,
    reveal_type,
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


class AnnotatedMethodFunctionCall(Protocol, Generic[_P, _R_co]):
    @staticmethod
    def __call__(meta: AnnotatedMethodInfo, *args: _P.args, **kwargs: _P.kwargs) -> _R_co: ...


class AnnotatedMethodMethodCall(Protocol, Generic[_P, _R_co]):
    def __call__(self, meta: AnnotatedMethodInfo, *args: _P.args, **kwargs: _P.kwargs) -> _R_co: ...


if TYPE_CHECKING:
    reveal_type(AnnotatedMethodFunctionCall)
    reveal_type(AnnotatedMethodFunctionCall.__call__)
    reveal_type(AnnotatedMethodMethodCall)
    reveal_type(AnnotatedMethodMethodCall.__call__)


class A:
    def a(self) -> int: ...
    def b(self, x): ...
    def c(self: Self, x: int) -> int: ...
    def d(self, x: int, *args: Any, i: int | None = None, **kwargs: Any) -> int: ...
    def e(self, x: int, *, i: int | None = None, **kwargs) -> int: ...
    def f(self, x: int, /, *, i: int | None = None, **kwargs) -> int: ...
    def f2(self, x: int, /, i: int | None = None, **kwargs) -> int: ...
    def g(self, x: int, /, *args: Any, i: int | None = None, **kwargs) -> int: ...
    def h(self, x: int, /, *args: Any, i: int | None = None) -> int: ...
    def i(self, x: int, /, *args: Any) -> int: ...


if TYPE_CHECKING:
    a = A()
    # reveal_type(A.a)
    # reveal_type(a.a)
    # reveal_type(A.b)
    # reveal_type(a.b)
    # reveal_type(A.c)
    # reveal_type(a.c)
    # reveal_type(A.d)
    # reveal_type(a.d)
    reveal_type(A.e)
    reveal_type(a.e)
    reveal_type(A.f)
    reveal_type(a.f)
    reveal_type(A.f2)
    reveal_type(a.f2)
    # reveal_type(A.g)
    # reveal_type(a.g)
    # reveal_type(A.h)
    # reveal_type(a.h)
    # reveal_type(A.i)
    # reveal_type(a.i)


class AnnotatedMethod(Generic[_T, _P, _R_co]):
    _np: NamePath
    _n: str
    _f: Callable[Concatenate[_T, _P], _R_co]
    _fmeta: Callable[Concatenate[_T, _P], _R_co]
    # _mmeta:

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
        meta = self.as_ntuple()
        if obj is None:
            return partial(self._f, meta=meta)
        return cast(Callable[_P, _R_co], self._f.__get__(obj, cls))

    def __set_name__(self, obj: Any, name: str) -> None:
        self._n = name
        if obj is None:
            raise ValueError(f"None obj? {obj}")
        if not hasattr(obj, "_infos"):
            setattr(obj, "_infos", {})
        obj._infos[self._np] = self.as_ntuple()

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
