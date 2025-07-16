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
    Self,
    TypeVar,
    cast,
    overload,
)

import pdbp
import rich
import rich.pretty
import rich.repr
import rich.traceback
from attrs import define, field
from dictstack import DictStack

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

# rich.pretty.install()
# rich.traceback.install(show_locals=True)
# traceback.print_stack.__globals__["__builtins__"]["print"] = rich.print

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

    def __rich_repr__(self) -> rich.repr.Result:
        yield "name", self.name
        yield "etc", self.etc


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
        object.__setattr__(self, "_fmeta", cast(Callable[Concatenate[_T, _P], _R_co], None))
        if self._etc is None:
            object.__setattr__(self, "_etc", {})
        print(f"AM.__init__() exit self: {pid(self)}")

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
        print(f"AM.__set_name__() entry name: {name} self: {self} sid: {pid(self)} oid: {pid(obj)}")
        object.__setattr__(self, "_name", name)
        if obj is None:
            raise ValueError(f"None obj? {obj}")
        nt = self.as_ntuple()
        # dump_stack()
        # print(f"AM.__set_name__() obj._infos assignment obj._infos.dicts: {obj._infos.dicts}")
        obj._infos[self._rnp.namepath] = nt
        if obj not in obj._namespaces:
            obj._namespaces[obj] = []
        obj._namespaces[obj].append(self)
        # Argument "meta" has incompatible type "AnnotatedMethodInfo"; expected "_P.kwargs"
        p = partial(self._func, meta=nt, etc=self._etc)  # type: ignore
        object.__setattr__(self, "_fmeta", cast(Callable[Concatenate[_T, _P], _R_co], p))
        print(f"AM.__set_name__() exit name: {name} self: {pid(self)} obj: {pid(self)}")

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


class GenericTypeRewriter(Generic[_T]):
    print("_infos() psdo-init GTR._infos in GTR body")
    print("_infos() real-init GTR._infos in GTR body")
    _infos: DictStack[NamePath, AnnotatedMethodInfo] = DictStack(name="GTRRoot")
    _infos.pushdict()
    _infos_ro: MappingProxyType[NamePath, AnnotatedMethodInfo]
    _namespaces: ClassVar[dict[type, list[AnnotatedMethodInfo]]] = {}

    # def __new__(cls) -> Self:
    #     raise RuntimeError("ffff")
    #     print(f"GTR.__new__() entry cls: {pid(cls)} {cls}")
    #     new_cls = super().__new__(cls)
    #     print("_infos() psdo-init GTR._infos in GTR.__new__")
    #     # if not hasattr(new_cls, "_infos"):
    #     #     print("_infos() real-init GTR._infos in GTR.__new__")
    #     #     setattr(new_cls, "_infos", DictStack(list((dict(),))))
    #     #     new_cls._infos = DictStack(list((dict(),)))  # type: ignore
    #     print(f"GTR.__new__() exit cls: {pid(cls)} {cls}")
    #     return new_cls

    def __new__(cls) -> Self:
        print(f"GenericTypeRewriter.__new__() entry cls: {cls}")
        r = super().__new__(cls)
        print(f"GenericTypeRewriter.__new__() entry cls: {cls} res: {r}")
        return r

    def __init__(self) -> None:
        # pdbp.set_trace()
        print(f"GTR.__init__() entry self: {pid(self)} {self}")
        super().__init__()
        self._infos_ro = self._infos.mapping
        print(f"GTR.__init__() exit self: {pid(self)} {self}")

    def __init_subclass__(cls) -> None:
        print(f"GTR.__init_subclass__() entry cls: {pid(cls)} {cls}")
        print("pushdict")
        setattr(
            cls,
            "_infos",
            DictStack([copy(d) for d in getattr(cls, "_infos").dicts], name=cls.__name__),
        )
        getattr(cls, "_infos").pushdict()
        print(f"GTR.__init_subclass__() exit cls: {pid(cls)} {cls}")

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


# print("_infos() psdo-init GTR._infos in top level")
# if not hasattr(GenericTypeRewriter, "_infos"):
#     print("_infos() real-init GTR._infos in top level")
#     setattr(GenericTypeRewriter, "_infos", DictStack(name="GTRRoot"))
#     getattr(GenericTypeRewriter, "_infos").pushdict()
print(
    f"GenericTypeRewriter: {GenericTypeRewriter} id: {pid(GenericTypeRewriter)} infos: {list(GenericTypeRewriter._infos)}"
)

# print("DictStack.all_instances()")
# rich.pretty.pprint(DictStack.all_instances())
# rich.pretty.pprint([ds._dicts for ds in DictStack.all_instances()])


class TypeRewriter(GenericTypeRewriter):
    def __new__(cls) -> Self:
        print(f"TypeRewriter.__new__() entry cls: {cls}")
        r = super().__new__(cls)
        print(f"TypeRewriter.__new__() entry cls: {cls} res: {r}")
        return r

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
    def __new__(cls) -> Self:
        print(f"MuhrivedTypeRewriter.__new__() entry cls: {cls}")
        r = super().__new__(cls)
        print(f"MuhrivedTypeRewriter.__new__() entry cls: {cls} res: {r}")
        return r

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


# print("DictStack.all_instances()")
# rich.pretty.pprint(DictStack.all_instances())
# rich.pretty.pprint([ds._dicts for ds in DictStack.all_instances()])

mtr = MuhrivedTypeRewriter()
