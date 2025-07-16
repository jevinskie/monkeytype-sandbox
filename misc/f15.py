from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from copy import copy
from functools import partial
from types import MappingProxyType, MethodType, ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Concatenate,
    Generic,
    ParamSpec,
    TypeVar,
    cast,
    overload,
)

import pdbp
from attrs import define
from attrs import field as afield

try:
    import rich.repr
except ImportError:
    pass


oprint = print
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

    try:
        from rich.pretty import install as __rpinstall

        # print("f15.py rich.pretty.install()")
        # __rpinstall()
        __rpinstall
    except ImportError:
        pass
else:

    def rinspect(*args: Any, **kwargs: Any) -> None: ...


pdbp  # keep import alive when set_trace() calls are commented out
copy  # ditto
sys  # ^

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_F = TypeVar("_F", bound=Callable[..., Any])
_P = ParamSpec("_P")
_R_co = TypeVar("_R_co", covariant=True)


def pid(obj: Any) -> str:
    return f"{id(obj):#010x}"


@define(auto_attribs=True, on_setattr=None, frozen=True, order=True)
class NamePath:
    module: str
    qualname: str


@define(auto_attribs=True, on_setattr=None, frozen=True, order=True)
class ResolvedNamePath:
    namepath: NamePath
    module: ModuleType
    value: Any


@define(auto_attribs=True, on_setattr=None, frozen=True, order=True)
class AnnotatedMethodInfo:
    resolved: ResolvedNamePath
    name: str
    self_namepath: NamePath
    method: MethodType

    def __rich_repr__(self) -> rich.repr.Result:
        yield "name", self.name
        yield "self_namepath", self.self_namepath


AMI = AnnotatedMethodInfo
AMIS = cast(AnnotatedMethodInfo, object())


class SetOnceDict(dict[_KT, _VT]):
    def __setitem__(self, key: _KT, value: _VT, /) -> None:
        if key in self:
            raise ValueError(
                f"Key '{key}' already exists. Existing value: {self[key]} New value: {value}"
            )
        super().__setitem__(key, value)


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


@define(auto_attribs=True, on_setattr=None, frozen=True, order=True)
class AnnotatedMethod(Generic[_T, _P, _R_co]):
    _func: Callable[Concatenate[_T, _P], _R_co]
    _namepath: NamePath
    _name: str = afield(init=False)
    _rnp: ResolvedNamePath = afield(init=False)
    _fmeta: Callable[Concatenate[_T, _P], _R_co] = afield(init=False)
    _self_np: NamePath = afield(init=False)

    # FIXME: Need weakref?

    def __attrs_post_init__(self) -> None:
        object.__setattr__(self, "_rnp", resolve_namepath(self._namepath))
        object.__setattr__(self, "_fmeta", cast(Callable[Concatenate[_T, _P], _R_co], None))

    @overload
    def __get__(self, obj: None, cls: type[_T], /) -> Callable[Concatenate[_T, _P], _R_co]: ...
    @overload
    def __get__(self, obj: _T, cls: type[_T] | None = None, /) -> Callable[_P, _R_co]: ...
    def __get__(
        self, obj: _T | None, cls: type[_T] | None = None, /
    ) -> Callable[Concatenate[_T, _P], _R_co] | Callable[_P, _R_co]:
        if obj is None:
            return self._fmeta
        p = partial(self._func.__get__(obj, cls), meta=self.as_ntuple())
        return cast(Callable[_P, _R_co], p)

    def __func__(self) -> Callable[Concatenate[_T, _P], _R_co]:
        return self._func

    @property
    def __wrapped__(self) -> Callable[Concatenate[_T, _P], _R_co]:
        return self._func

    # FIXME: need prototocol to type type[_T] further with these private attrs
    def __set_name__(self, obj: type[_T], name: str) -> None:
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_self_np", NamePath(obj.__module__, f"{obj.__qualname__}.{name}"))
        nt = self.as_ntuple()
        if obj not in obj._namespaces:
            obj._namespaces[obj] = []
        obj._namespaces[obj].append(self)
        # Argument "meta" has incompatible type "AnnotatedMethodInfo"; expected "_P.kwargs"
        p = partial(self._func, meta=nt)  # type: ignore
        object.__setattr__(self, "_fmeta", cast(Callable[Concatenate[_T, _P], _R_co], p))

    def as_ntuple(self) -> AnnotatedMethodInfo:
        return AnnotatedMethodInfo(self._rnp, self._name, self._self_np, cast(MethodType, self))

    @property
    def name(self) -> str:
        return self._name

    @property
    def namepath(self) -> NamePath:
        return self._namepath

    @property
    def resolved_namepath(self) -> ResolvedNamePath:
        return self._rnp

    @property
    def self_namepath(self) -> NamePath:
        return self._self_np


class rewriter_dec:
    tgt_namepath: NamePath

    def __init__(self, tgt_module: str, tgt_qualname: str) -> None:
        self.tgt_namepath = NamePath(tgt_module, tgt_qualname)

    def __call__(self, func: _F) -> _F:
        return cast(_F, AnnotatedMethod(func, self.tgt_namepath))

    def __repr__(self) -> str:
        return f'rewriter_dec("{self.tgt_namepath.module}", "{self.tgt_namepath.qualname}")'

    def __rich_repr__(self) -> rich.repr.Result:
        yield "tgt_namepath", self.tgt_namepath


# TODO: change _cls_rewrite_meths value type to MethodInfo?
class GenericTypeRewriter(Generic[_T]):
    _namespaces: ClassVar[SetOnceDict[type, list[AnnotatedMethodInfo]]] = SetOnceDict()
    _namespaces_ro: ClassVar[MappingProxyType[type, list[AnnotatedMethodInfo]]] = MappingProxyType(
        _namespaces
    )
    _cls_rewrite_meths: ClassVar[SetOnceDict[NamePath, AnnotatedMethodInfo]]
    _cls_rewrite_meths_ro: ClassVar[MappingProxyType[NamePath, AnnotatedMethodInfo]]

    def __init_subclass__(cls) -> None:
        cls._cls_rewrite_meths = SetOnceDict()
        cls._cls_rewrite_meths_ro = MappingProxyType(cls._cls_rewrite_meths)
        for val in vars(cls).values():
            if isinstance(val, AnnotatedMethod):
                cls._cls_rewrite_meths[val.namepath] = val.as_ntuple()

    def _call_annotated_method(
        self, method_info: AnnotatedMethodInfo, /, *args: Any, **kwargs: Any
    ) -> Any:
        # get a bound methhod from the function (yes the attribute is misnamed "method")
        m = method_info.method.__get__(self, type(self))  # type: ignore
        return m(*args, **kwargs)

    @classmethod
    def rewrite_methods(cls) -> MappingProxyType[NamePath, AnnotatedMethodInfo]:
        return cls._cls_rewrite_meths_ro

    @classmethod
    def rewrite_method_for(cls, namepath: NamePath) -> AnnotatedMethodInfo:
        for mcls in cls.mro():
            if not issubclass(mcls, GenericTypeRewriter):
                continue
            rewriter = mcls.rewrite_methods().get(namepath, None)
            if rewriter is not None:
                return rewriter
        raise KeyError(f"No rewrite method for NP: {namepath} methods: {cls.registry}")

    @property
    def registry(self) -> MappingProxyType[type, list[AnnotatedMethodInfo]]:
        return self._namespaces_ro

    def rewrite_type(self, namepath: NamePath, a: int, b: int) -> int:
        rewriter = self.rewrite_method_for(namepath)
        if rewriter is not None:
            print(f"rewriter: NP: {rewriter.self_namepath} target type NP: {namepath}")
            return cast(int, self._call_annotated_method(rewriter, a, b))
        else:
            raise KeyError(f"couldn't get key for namepath: {namepath}")


class TypeRewriter(GenericTypeRewriter):
    @rewriter_dec("typing", "Union")
    def rewrite_typing_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(f"TR.rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}")
        # print(f"TR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union")
    def rewrite_c_ast_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(f"TR.rewrite_c_ast_Union() self: {self} a: {a} b: {b} id(m): {pid(meta)}")
        # print(f"TR.cast.meta: {meta}\n")
        return a * b


class MuhrivedTypeRewriter(TypeRewriter):
    @rewriter_dec("construct", "Union")
    def muh_rewrite_construct_Union(self, a: int, b: int, /, meta: AMI = AMIS) -> int:
        print(f"MTR.muh_rewrite_construct_Union() self: {self} a: {a} b: {b} id(m): {pid(meta)}")
        # print(f"MTR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union")
    def muh_rewrite_c_ast_Union(self, a: int, b: int, /, meta: AMI = AMIS) -> int:
        print(f"MTR.muh_rewrite_c_ast_Union() self: {self} a: {a} b: {b} id(m): {pid(meta)}")
        # print(f"MTR.cast.meta: {meta}\n")
        return a * b
