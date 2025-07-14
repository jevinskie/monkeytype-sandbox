from __future__ import annotations

import importlib
import sys
from abc import ABCMeta
from collections.abc import Callable
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
from attrs import define, field
from dictstack import DictStack

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
sys  # ditty

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
        # print(f"AM.__api__ id: {pid(self)} np: {self._namepath} etc: {self._etc}")

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
        # breakpoint()
        # print(f"_infos() psdo-init in AM.__set_name__ name: {name}")
        if obj is None:
            raise ValueError(f"None obj? {obj}")
            # print(f"_infos() real-init in AM.__set_name__ name: {name}")
            # setattr(obj, "_infos", DictStack(list((dict(),))))
        nt = self.as_ntuple()
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
        # print(f"RD() np: {self._np} etc: {self._etcz}")

    def __call__(self, func: _F) -> _F:
        return cast(_F, AnnotatedMethod(func, self._np, self._etcz))


class GenericTypeRewriterMetaInner(type):
    def __new__(
        cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
    ) -> GenericTypeRewriterMetaInner:
        print(f"GTRMI.__new__ name: {name} cls: {cls}")
        # print(f"GTRMI.__new__ pre-super name: {name} cls: {cls} bases: {bases} ns: {namespace}")
        # print("_infos() psdo-init GTR._infos in GTRMI.__new__ pre-super")
        if "_infos" not in namespace:
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


class GenericTypeRewriterMeta(ABCMeta, GenericTypeRewriterMetaInner):
    def __init_subclass__(cls) -> None:
        print(f"GTRM.__init_subclass__: {cls}")


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
        print("_infos() psdo-init in GTR.__init__")
        # if not hasattr(self, "_infos"):
        #     print("_infos() real-init GTR.__init__")
        #     setattr(self, "_infos", DictStack(list((dict(),))))
        #     self._infos = DictStack(list((dict(),)))
        self._infos_ro = self._infos.mapping

    def __init_subclass__(cls) -> None:
        print(f"GTR.__init_subclass__: {cls}")
        # pdbp.set_trace()
        # rinspect(cls)
        # orig = copy(cls._infos._dicts)
        # print(
        #     f"_is_() init: cls: {cls} id(cls): {pid(cls)} id(inf): {pid(cls._infos)} inf: {cls._infos}"
        # )
        # print("_is_() init: dicts:")
        # dict_id_str = " ".join([f"{pid(p)}" for p in cls._infos.dicts])
        # print(f"init d*: {dict_id_str}")
        # print(cls._infos.dicts)
        # print()

        # super().__init_subclass__()

        # print(f"_is_() midl: cls {cls} id(inf): {pid(cls._infos)} inf: {cls._infos}")
        # print("_is_() midl: dicts:")
        # dict_id_str = " ".join([f"{pid(p)}" for p in cls._infos.dicts])
        # print(f"midl d*: {dict_id_str}")
        # print(cls._infos.dicts)
        # print()

        # cls._infos = copy(cls._infos)
        # print("pushdict")
        # cls._infos.pushdict()

        # print(f"_is_() post: cls: {cls} id(inf): {pid(cls._infos)} inf: {cls._infos}")
        # print("_is_() post: dicts:")
        # dict_id_str = " ".join([f"{pid(p)}" for p in cls._infos.dicts])
        # print(f"post d*: {dict_id_str}")
        # dict_id_str = " ".join([f"{pid(p)}" for p in orig])
        # print(f"post od*: {dict_id_str}")
        # print(cls._infos.dicts)
        # print()

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


# class DerivedTypeRewriter(TypeRewriter):
#     @rewriter_dec("typing", "Union", {"name": "DTR.der_rewrite_typing_Union"})
#     def der_rewrite_typing_Union(
#         self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
#     ) -> int:
#         print(
#             f"DTR.der_rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}"
#         )
#         print(f"DTR.type.meta: {meta}\n")
#         return a + b

#     @rewriter_dec("pycparser.c_ast", "Union", {"name": "DTR.der_rewrite_c_ast_Union"})
#     def der_rewrite_c_ast_Union(
#         self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
#     ) -> int:
#         print(
#             f"DTR.der_rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}"
#         )
#         print(f"DTR.cast.meta: {meta}\n")
#         return a * b


# print(
#     f"DerivedTypeRewriter: {DerivedTypeRewriter} id: {pid(DerivedTypeRewriter)} infos: {list(DerivedTypeRewriter._infos)}"
# )


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


# class DubDerTypeRewriter(DerivedTypeRewriter):
#     @rewriter_dec("typing", "Union", {"name": "DDTR.dub_rewrite_typing_Union"})
#     def dub_rewrite_typing_Union(
#         self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
#     ) -> int:
#         print(
#             f"DDTR.dub_rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}"
#         )
#         print(f"DDTR.type.meta: {meta}\n")
#         return a + b

#     @rewriter_dec("pycparser.c_ast", "Union", {"name": "DDTR.dub_rewrite_c_ast_Union"})
#     def dub_rewrite_c_ast_Union(
#         self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
#     ) -> int:
#         print(
#             f"DDTR.dub_rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}"
#         )
#         print(f"DDTR.cast.meta: {meta}\n")
#         return a * b


# print(
#     f"DubDerTypeRewriter: {DubDerTypeRewriter} id: {pid(DubDerTypeRewriter)} infos: {list(DubDerTypeRewriter._infos)}"
# )


# if __name__ == "__main__":
#     sys.exit(0)
#     np_t = NamePath("typing", "Union")
#     np_c = NamePath("pycparser.c_ast", "Union")
#     np_s = NamePath("construct", "Union")
#     print(f"np_t: {np_t}")
#     print(f"np_c: {np_c}")

#     print("\n" * 3)

#     tr = TypeRewriter()
#     print(f"rw_ty typing.Union: 10, 20: {tr.rewrite_type(np_t, 10, 20)}")
#     print("\n" * 1)
#     print(f"rw_ty c_ast.Union: 100, 200: {tr.rewrite_type(np_c, 100_000, 200_000)}")

#     print("\n" * 7)

#     dtr = DerivedTypeRewriter()
#     print(f"rw_dty typing.Union: 10, 20: {dtr.rewrite_type(np_t, 30, 40)}")
#     print("\n" * 1)
#     print(f"rw_dty c_ast.Union: 100, 200: {dtr.rewrite_type(np_c, 300_000, 400_000)}")

#     print("\n" * 7)

#     mtr = MuhrivedTypeRewriter()
#     print(f"rw_mty typing.Union: 10, 20: {mtr.rewrite_type(np_t, 50, 50)}")
#     print("\n" * 1)
#     print(f"rw_mty c_ast.Union: 100, 200: {mtr.rewrite_type(np_c, 500_000, 500_000)}")
#     print("\n" * 1)
#     print(f"rw_mty construct.Union: 10, 20: {mtr.rewrite_type(np_s, 400_000, 400_000)}")

#     print("\n" * 7)

#     ddtr = DubDerTypeRewriter()
#     print(f"rw_ddty typing.Union: 10, 20: {ddtr.rewrite_type(np_t, 60, 60)}")
#     print("\n" * 1)
#     print(f"rw_ddty c_ast.Union: 100, 200: {ddtr.rewrite_type(np_c, 600_000, 600_000)}")

#     print("\n" * 5)

#     print("tr() dicts:")
#     dict_id_str = " ".join([f"{pid(p)}" for p in tr._infos.dicts])
#     print(f"d*: {dict_id_str}")
#     print(tr._infos.dicts)

#     print("\n" * 3)

#     print("dtr() dicts:")
#     dict_id_str = " ".join([f"{pid(p)}" for p in dtr._infos.dicts])
#     print(f"d*: {dict_id_str}")
#     print(dtr._infos.dicts)

#     print("\n" * 3)

#     print("mtr() dicts:")
#     dict_id_str = " ".join([f"{pid(p)}" for p in mtr._infos.dicts])
#     print(f"d*: {dict_id_str}")
#     print(mtr._infos.dicts)

#     print("\n" * 3)

#     print("ddtr() dicts:")
#     dict_id_str = " ".join([f"{pid(p)}" for p in ddtr._infos.dicts])
#     print(f"d*: {dict_id_str}")
#     print(ddtr._infos.dicts)
