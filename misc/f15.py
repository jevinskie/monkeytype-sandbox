from __future__ import annotations

import functools
import importlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from types import MappingProxyType, MethodType, ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Concatenate,
    Generic,
    ParamSpec,
    Protocol,
    TypeVar,
    cast,
    overload,
)

if not TYPE_CHECKING:
    try:
        from rich import print
    except ImportError:
        pass
    try:
        from rich import inspect as rinspect
    except ImportError:

        def rinspect(*args: Any, **kwargs: Any) -> None:
            print(*args)

    try:
        from rich.repr import RichReprResult
    except ImportError:
        pass
else:

    def rinspect(*args: Any, **kwargs: Any) -> None: ...

    RichReprResult = Iterable[Any | tuple[Any] | tuple[str, Any] | tuple[str, Any, Any]]


_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_F = TypeVar("_F", bound=Callable[..., Any])
_P = ParamSpec("_P")
_R_co = TypeVar("_R_co", covariant=True)


def pid(obj: Any) -> str:
    return f"{id(obj):#010x}"


@dataclass(frozen=True, order=True)
class NamePath:
    module: str
    qualname: str


@dataclass(frozen=True, order=True)
class ResolvedNamePath:
    namepath: NamePath
    module: ModuleType
    value: Any


@dataclass(frozen=True, order=True)
class AnnotatedMethodInfo:
    resolved: ResolvedNamePath
    name: str
    self_namepath: NamePath
    method: MethodType

    def __repr__(self) -> str:
        return f'<AnnotatedMethodInfo name="{self.name}" self_namepath={self.self_namepath}>'

    def __rich_repr__(self) -> RichReprResult:
        yield "name", self.name
        yield "self_namepath", self.self_namepath


AMI = AnnotatedMethodInfo
AMIS = cast(AnnotatedMethodInfo, object())  # sentinel default object for meta kwarg


class AnnotatedMethodOwner(Protocol):
    _namespaces: ClassVar[SetOnceDict[type, list[AnnotatedMethodInfo]]]
    _namespaces_ro: ClassVar[MappingProxyType[type, list[AnnotatedMethodInfo]]]
    _cls_rewrite_meths: ClassVar[SetOnceDict[NamePath, AnnotatedMethodInfo]]
    _cls_rewrite_meths_ro: ClassVar[MappingProxyType[NamePath, AnnotatedMethodInfo]]


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


@dataclass(frozen=True)
class AnnotatedMethod(Generic[_T, _P, _R_co]):
    _func: Callable[Concatenate[_T, _P], _R_co]
    _namepath: NamePath
    _name: str = field(init=False)
    _rnp: ResolvedNamePath = field(init=False)
    _fmeta: Callable[Concatenate[_T, _P], _R_co] = field(init=False)
    _self_np: NamePath = field(init=False)

    # FIXME: Need weakref?

    def __post_init__(self) -> None:
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
        p = functools.partial(self._func.__get__(obj, cls), meta=self.as_ntuple())
        return cast(Callable[_P, _R_co], p)

    def __func__(self) -> Callable[Concatenate[_T, _P], _R_co]:
        return self._func

    @property
    def __wrapped__(self) -> Callable[Concatenate[_T, _P], _R_co]:
        return self._func

    # FIXME: need prototocol to type type[_T] further with these private attrs
    def __set_name__(self, new_cls: Any, name: str) -> None:
        if not isinstance(new_cls, type):
            raise TypeError("AnnotatedMethod must be a class attribute")
        if not issubclass(new_cls, GenericTypeRewriter):
            raise TypeError(
                f"Can't set descriptor on non-GenericTypeRewriter-derived class: {new_cls}"
            )
        object.__setattr__(self, "_name", name)
        object.__setattr__(
            self, "_self_np", NamePath(new_cls.__module__, f"{new_cls.__qualname__}.{name}")
        )
        nt = self.as_ntuple()
        if new_cls not in new_cls._namespaces:
            new_cls._namespaces[new_cls] = []
        new_cls._namespaces[new_cls].append(self.as_ntuple())
        # Argument "meta" has incompatible type "AnnotatedMethodInfo"; expected "_P.kwargs"
        p = functools.partial(self._func, meta=nt)  # type: ignore
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


class register_rewrite:
    tgt_namepath: NamePath

    def __init__(self, tgt_module: str, tgt_qualname: str) -> None:
        self.tgt_namepath = NamePath(tgt_module, tgt_qualname)

    def __call__(self, func: _F) -> _F:
        return cast(_F, AnnotatedMethod(func, self.tgt_namepath))


# TODO: change _cls_rewrite_meths value type to MethodInfo?
class GenericTypeRewriter:
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
    @register_rewrite("typing", "Union")
    def rewrite_typing_Union(self, a: int, b: int, /, meta: AMI = AMIS) -> int:
        print(f"TR.rewrite_typing_Union() self: {self} a: {a} b: {b}")
        return a + b

    @register_rewrite("pycparser.c_ast", "Union")
    def rewrite_c_ast_Union(self, a: int, b: int, /, meta: AMI = AMIS) -> int:
        print(f"TR.rewrite_c_ast_Union() self: {self} a: {a} b: {b}")
        return a * b


class MuhrivedTypeRewriter(TypeRewriter):
    @register_rewrite("construct", "Union")
    def muh_rewrite_construct_Union(self, a: int, b: int, /, meta: AMI = AMIS) -> int:
        print(f"MTR.muh_rewrite_construct_Union() self: {self} a: {a} b: {b}")
        return a + b

    @register_rewrite("pycparser.c_ast", "Union")
    def muh_rewrite_c_ast_Union(self, a: int, b: int, /, meta: AMI = AMIS) -> int:
        print(f"MTR.muh_rewrite_c_ast_Union() self: {self} a: {a} b: {b}")
        return a * b
