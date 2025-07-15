from __future__ import annotations

import importlib
import sys
import traceback
from abc import ABCMeta
from collections.abc import Callable, MutableMapping
from copy import copy
from functools import partial
from types import MappingProxyType, MethodType, ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    Generic,
    ParamSpec,
    Self,
    TypeVar,
    cast,
    overload,
)

import pdbp
import rich
import rich.console
import rich.pretty
import rich.traceback
from attrs import define, field
from dictstack import DictStack
from icecream import IceCreamDebugger

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

        print("f15.py rich.pretty.install()")
        __rpinstall()
    except ImportError:
        pass
else:

    def rinspect(*args: Any, **kwargs: Any) -> None: ...


pdbp  # keep import alive when set_trace() calls are commented out
copy  # ditto
sys  # ^

rich.pretty.install()
rich.traceback.install(show_locals=True)
traceback.print_stack.__globals__["__builtins__"]["print"] = rich.print

ic = IceCreamDebugger(outputFunction=rich.print, includeContext=True)

_T = TypeVar("_T")
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
    method: MethodType
    etc: dict[Any, Any]


AMI = AnnotatedMethodInfo
AMIS = cast(AnnotatedMethodInfo, object())


def dump_stack() -> None:
    # tb = rich.traceback.Traceback(show_locals=True)
    # print(tb)
    pass


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
    _etc: dict[Any, Any] | None = field(default=None)
    _name: str = field(init=False)
    _rnp: ResolvedNamePath = field(init=False)
    _fmeta: Callable[Concatenate[_T, _P], _R_co] = field(init=False)

    # FIXME: Need weakref?

    def __attrs_post_init__(self) -> None:
        object.__setattr__(self, "_rnp", resolve_namepath(self._namepath))
        if self._etc is None:
            object.__setattr__(self, "_etc", {})

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

    def __set_name__(self, obj: Any, name: str) -> None:
        print(f"AM.__set_name__ sid: {pid(self)} oid: {pid(obj)} name: {name}")
        object.__setattr__(self, "_name", name)
        if obj is None:
            raise ValueError(f"None obj? {obj}")
        nt = self.as_ntuple()
        traceback.print_stack()
        print(f"AM.__set_name__ obj._infos assignment obj._infos.dicts: {obj._infos.dicts}")
        obj._infos[self._rnp.namepath] = nt
        # Argument "meta" has incompatible type "AnnotatedMethodInfo"; expected "_P.kwargs"
        p = partial(self._func, meta=nt, etc=self._etc)  # type: ignore
        object.__setattr__(self, "_fmeta", cast(Callable[Concatenate[_T, _P], _R_co], p))

    def as_ntuple(self) -> AnnotatedMethodInfo:
        if self._etc is None:
            raise ValueError("self._etc is None")
        return AnnotatedMethodInfo(self._rnp, self._name, cast(MethodType, self), self._etc)


@define(auto_attribs=True, on_setattr=None, frozen=True, order=True)
class rewriter_dec:
    _module: str
    _qualname: str
    _etcz: dict[Any, Any] | None = field(default=None)
    _np: NamePath = field(init=False)

    def __attrs_post_init__(self) -> None:
        object.__setattr__(self, "_np", NamePath(self._module, self._qualname))

    def __call__(self, func: _F) -> _F:
        return cast(_F, AnnotatedMethod(func, self._np, self._etcz))


class GenericTypeRewriterMetaInner(type):
    def __new__(
        cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
    ) -> GenericTypeRewriterMetaInner:
        print(f"GTRMI.__new__ name: {name} cls: {cls}")
        ic("GTRMI.__init__" and pid(cls))
        # print(f"GTRMI.__new__ pre-super name: {name} cls: {cls} bases: {bases} ns: {namespace}")
        # print("_infos() psdo-init GTR._infos in GTRMI.__new__ pre-super")
        if "_infos" not in namespace:
            dump_stack()
            print("_infos() real-init GTR._infos in GTRMI.__new__ pre-super")
            namespace["_infos"] = DictStack(list((dict(),)))
        # print("pushdict")
        # namespace["_infos"] = copy(namespace["_infos"])
        # namespace["_infos"].pushdict()
        new_cls = super().__new__(cls, name, bases, namespace)
        # print("_infos() psdo-init GTR._infos in GTRMI.__new__ post-super")
        # if not hasattr(new_cls, "_infos"):
        #     print("_infos() real-init GTR._infos in GTRMI.__new__ post-super")
        #     setattr(new_cls, "_infos", DictStack(list((dict(),))))
        dump_stack()
        print("pushdict")
        setattr(new_cls, "_infos", copy(getattr(new_cls, "_infos")))
        getattr(new_cls, "_infos").pushdict()
        # print(
        #     f"GTRMI.__new__ post-super cls: {cls} new_cls: {new_cls} cid: {pid(cls)} ncid: {pid(new_cls)}"
        # )
        return new_cls

    def __init__(
        self, name: str, bases: tuple[type, ...], namespace: dict[str, Any], /, **kwds: Any
    ) -> None:
        print(f"GTRMI.__init__ name: {name}")
        # print(
        #     f"GTRMI.__init__ sid: {pid(self)} self: {self} name: {name} ns: {namespace} kw: {kwds}"
        # )
        # pdbp.set_trace()
        # print("_infos() psdo-init GTR._infos in GTRMI.__init__ pre-super")
        # if "_infos" not in namespace:
        #     print("_infos() real-init GTR._infos in GTRMI.__init__ pre-super")
        #     namespace["_infos"] =  DictStack(list((dict(),)))
        # print("pushdict")
        # namespace["_infos"] = copy(namespace["_infos"])
        # namespace["_infos"].pushdict()
        # print(f"GTRMI.__init__ pre-super self: {self} id: {pid(self)}")
        super().__init__(name, bases, namespace)
        # print("_infos() psdo-init GTR._infos in GTRMI.__init__ post-super")
        # if "_infos" not in namespace:
        #     print("_infos() real-init GTR._infos in GTRMI.__init__ post-super")
        #     namespace["_infos"] =  DictStack(list((dict(),)))
        # print("pushdict")
        # namespace["_infos"] = copy(namespace["_infos"])
        # namespace["_infos"].pushdict()
        # setattr(self, "_infos", copy(getattr(self, "_infos")))
        # getattr(self, "_infos").pushdict()
        # print(f"GTRMI.__init__ post-super self: {self} id: {pid(self)}")

    def __init_subclass__(cls) -> None:
        print(f"GTRMI.__init_subclass__: {cls}")

    @classmethod
    def __prepare__(
        metacls, name: str, bases: tuple[type, ...], /, **kwds: Any
    ) -> MutableMapping[str, object]:
        print(f"GTRMI.__prepare__ metacls: {metacls} name: {name} bases: {bases} kw: {kwds}")
        r = super().__prepare__(name, bases, **kwds)
        print(f"GTRMI.__prepare__ result: {r}")
        return r


class GenericTypeRewriterMeta(ABCMeta, GenericTypeRewriterMetaInner):
    pass


class GenericTypeRewriter(Generic[_T], metaclass=GenericTypeRewriterMeta):
    _infos: DictStack[NamePath, AnnotatedMethodInfo]
    _infos_ro: MappingProxyType[NamePath, AnnotatedMethodInfo]

    def __new__(cls) -> Self:
        print(f"GTR.__new__ cls: {cls}")
        new_cls = super().__new__(cls)
        print("_infos() psdo-init GTR._infos in GTR.__new__")
        # if not hasattr(new_cls, "_infos"):
        #     print("_infos() real-init GTR._infos in GTR.__new__")
        #     setattr(new_cls, "_infos", DictStack(list((dict(),))))
        #     new_cls._infos = DictStack(list((dict(),)))  # type: ignore
        return new_cls

    def __init__(self) -> None:
        # pdbp.set_trace()
        print(f"GTR.__init__ self: {self}")
        super().__init__()
        self._infos_ro = self._infos.mapping

    def __init_subclass__(cls) -> None:
        print(f"GTR.__init_subclass__: {cls}")

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


print("_infos() psdo-init GTR._infos in top level")
# if not hasattr(GenericTypeRewriter, "_infos"):
#     print("_infos() real-init GTR._infos in top level")
#     setattr(GenericTypeRewriter, "_infos", DictStack(list((dict(),))))
#     GenericTypeRewriter._infos = DictStack(list((dict(),)))
print(
    f"GenericTypeRewriter: {GenericTypeRewriter} id: {pid(GenericTypeRewriter)} infos: {list(GenericTypeRewriter._infos)}"
)


class TypeRewriter(GenericTypeRewriter):
    @rewriter_dec("typing", "Union", {"name": "TR.rewrite_typing_Union"})
    def rewrite_typing_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(f"TR.rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}")
        print(f"TR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union", {"name": "TR.rewrite_c_ast_Union"})
    def rewrite_c_ast_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(f"TR.rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}")
        print(f"TR.cast.meta: {meta}\n")
        return a * b


print(f"TypeRewriter: {TypeRewriter} id: {pid(TypeRewriter)} infos: {list(TypeRewriter._infos)}")


class MuhrivedTypeRewriter(TypeRewriter):
    @rewriter_dec("construct", "Union", {"name": "MTR.muh_rewrite_construct_Union"})
    def muh_rewrite_construct_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"MTR.muh_rewrite_construct_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}"
        )
        print(f"MTR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union", {"name": "MTR.der_rewrite_c_ast_Union"})
    def muh_rewrite_c_ast_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"MTR.muh_rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}"
        )
        print(f"MTR.cast.meta: {meta}\n")
        return a * b


print(
    f"MuhrivedTypeRewriter: {MuhrivedTypeRewriter} id: {pid(MuhrivedTypeRewriter)} infos: {list(MuhrivedTypeRewriter._infos)}"
)
