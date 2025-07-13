from __future__ import annotations

import importlib
from abc import ABC
from collections.abc import Callable
from copy import copy
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
    try:
        from rich import inspect as rinspect
    except ImportError:

        def rinspect(*args: Any, **kwargs: Any) -> None:
            print(*args)

else:

    def rinspect(*args: Any, **kwargs: Any) -> None: ...


from dictstack import DictStack

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
    etc: dict[Any, Any]


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
    _etc: dict[Any, Any]

    # FIXME: Need weakref?

    def __init__(
        self,
        func: Callable[Concatenate[_T, _P], _R_co],
        namepath: NamePath,
        etc: dict[Any, Any] | None = None,
    ) -> None:
        self._rnp = resolve_namepath(namepath)
        self._f = func
        self._etc = etc if etc is not None else {}

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
            setattr(obj, "_infos", DictStack([{}]))
        nt = self.as_ntuple()
        obj._infos[self._rnp.namepath] = nt
        # Argument "meta" has incompatible type "AnnotatedMethodInfo"; expected "_P.kwargs"
        p = partial(self._f, meta=nt, etc=self._etc)  # type: ignore
        self._fmeta = cast(Callable[Concatenate[_T, _P], _R_co], p)

    def as_ntuple(self) -> AnnotatedMethodInfo:
        return AnnotatedMethodInfo(self._rnp, self._n, cast(MethodType, self), self._etc)


class rewriter_dec:
    _np: NamePath
    _etc: dict[Any, Any] | None

    def __init__(self, module: str, qualname: str, /, etc: dict[Any, Any] | None = None) -> None:
        self._np = NamePath(module, qualname)
        self._etc = etc

    def __call__(self, func: _F) -> _F:
        return cast(_F, AnnotatedMethod(func, self._np, etc=self._etc))


class GenericTypeRewriter(Generic[_T], ABC):
    _infos: DictStack[NamePath, AnnotatedMethodInfo]
    _infos_ro: MappingProxyType[NamePath, AnnotatedMethodInfo]

    def __init__(self) -> None:
        if not hasattr(self, "_infos"):
            self._infos = DictStack([{}])
        self._infos_ro = self._infos.mapping

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls._infos = copy(cls._infos)
        cls._infos.pushdict()

    def _call_annotated_method(
        self, method_info: AnnotatedMethodInfo, /, *args: Any, **kwargs: Any
    ) -> Any:
        m = method_info.method.__get__(self, type(self))  # type: ignore
        return m(*args, **kwargs)

    @property
    def registry(self) -> MappingProxyType[NamePath, AnnotatedMethodInfo]:
        return self._infos_ro

    def rewrite_type(self, namepath: NamePath, a: int, b: int) -> int:
        rewriter = self.registry.get(namepath)
        print(f"rewriter: {rewriter}")
        if rewriter:
            return cast(int, self._call_annotated_method(rewriter, a, b))
        raise KeyError(f"couldn't get key for namepath: {namepath}")


class TypeRewriter(GenericTypeRewriter):
    @rewriter_dec("typing", "Union", etc={"name": "TR.rewrite_typing_Union"})
    def rewrite_typing_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"TR.rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"TR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union", etc={"name": "TR.rewrite_c_ast_Union"})
    def rewrite_c_ast_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"TR.rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"TR.cast.meta: {meta}\n")
        return a * b


class DerivedTypeRewriter(TypeRewriter):
    @rewriter_dec("typing", "Union", etc={"name": "DTR.der_rewrite_typing_Union"})
    def der_rewrite_typing_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"DTR.rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"DTR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union", etc={"name": "DTR.der_rewrite_c_ast_Union"})
    def der_rewrite_c_ast_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"DTR.der_rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"DTR.cast.meta: {meta}\n")
        return a * b


if __name__ == "__main__":
    np_t = NamePath("typing", "Union")
    np_c = NamePath("pycparser.c_ast", "Union")
    print(f"np_t: {np_t}")
    print(f"np_c: {np_c}")

    print("\n" * 3)

    tr = TypeRewriter()
    print(f"rw_ty typing.Union: 10, 20: {tr.rewrite_type(np_t, 10, 20)}")
    print("\n" * 1)
    print(f"rw_ty c_ast.Union: 100, 200: {tr.rewrite_type(np_c, 100, 200)}")

    print("\n" * 7)

    dtr = DerivedTypeRewriter()
    print(f"rw_dty typing.Union: 10, 20: {dtr.rewrite_type(np_t, 10, 20)}")
    print("\n" * 1)
    print(f"rw_dty c_ast.Union: 100, 200: {dtr.rewrite_type(np_c, 100, 200)}")
