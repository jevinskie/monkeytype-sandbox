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

import pdbp
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

else:

    def rinspect(*args: Any, **kwargs: Any) -> None: ...


pdbp  # keep import alive when set_trace() calls are commented out


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
        print(f"AM() np: {namepath} etc: {etc}")

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
        print(f"_infos() psdo-init in AM.__set_name__ name: {name}")
        if not hasattr(obj, "_infos"):
            print(f"_infos() real-init in AM.__set_name__ name: {name}")
            setattr(obj, "_infos", DictStack(list((dict(),))))
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

    def __init__(self, module: str, qualname: str, /, etcz: dict[Any, Any] | None = None) -> None:
        self._np = NamePath(module, qualname)
        self._etc = etcz
        print(f"RD() np: {self._np} etc: {self._etc}")

    def __call__(self, func: _F) -> _F:
        return cast(_F, AnnotatedMethod(func, self._np, etc=self._etc))


class GenericTypeRewriter(Generic[_T], ABC):
    _infos: DictStack[NamePath, AnnotatedMethodInfo]
    _infos_ro: MappingProxyType[NamePath, AnnotatedMethodInfo]

    def __init__(self) -> None:
        # pdbp.set_trace()
        print("_infos() psdo-init in GTR.__init__")
        if not hasattr(self, "_infos"):
            print("_infos() real-init GTR.__init__")
            self._infos = DictStack(list((dict(),)))
        self._infos_ro = self._infos.mapping

    def __init_subclass__(cls) -> None:
        # pdbp.set_trace()
        orig = copy(cls._infos._dicts)
        print(f"_is_() init: cls: {cls} id(inf): {id(cls._infos):#010x} inf: {cls._infos}")
        print("_is_() init: dicts:")
        dict_id_str = " ".join([f"{id(p):#010x}" for p in cls._infos.dicts])
        print(f"init d*: {dict_id_str}")
        print(cls._infos.dicts)
        print()
        super().__init_subclass__()
        print(f"_is_() midl: cls {cls} id(inf): {id(cls._infos):#010x} inf: {cls._infos}")
        print("_is_() midl: dicts:")
        dict_id_str = " ".join([f"{id(p):#010x}" for p in cls._infos.dicts])
        print(f"midl d*: {dict_id_str}")
        print(cls._infos.dicts)
        print()
        cls._infos = copy(cls._infos)
        cls._infos.pushdict()
        print(f"_is_() post: cls: {cls} id(inf): {id(cls._infos):#010x} inf: {cls._infos}")
        print("_is_() post: dicts:")
        dict_id_str = " ".join([f"{id(p):#010x}" for p in cls._infos.dicts])
        print(f"post d*: {dict_id_str}")
        dict_id_str = " ".join([f"{id(p):#010x}" for p in orig])
        print(f"post od*: {dict_id_str}")
        print(cls._infos.dicts)
        print()

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
print("_infos() real-init GTR._infos in top level")
GenericTypeRewriter._infos = DictStack(list((dict(),)))


class TypeRewriter(GenericTypeRewriter):
    @rewriter_dec("typing", "Union", etcz={"name": "TR.rewrite_typing_Union"})
    def rewrite_typing_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"TR.rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"TR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union", etcz={"name": "TR.rewrite_c_ast_Union"})
    def rewrite_c_ast_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"TR.rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"TR.cast.meta: {meta}\n")
        return a * b


class DerivedTypeRewriter(TypeRewriter):
    @rewriter_dec("typing", "Union", etcz={"name": "DTR.der_rewrite_typing_Union"})
    def der_rewrite_typing_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"DTR.der_rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"DTR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union", etcz={"name": "DTR.der_rewrite_c_ast_Union"})
    def der_rewrite_c_ast_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"DTR.der_rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"DTR.cast.meta: {meta}\n")
        return a * b


class MuhrivedTypeRewriter(TypeRewriter):
    @rewriter_dec("typing", "Union", etcz={"name": "MTR.muh_rewrite_typing_Union"})
    def muh_rewrite_typing_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"MTR.muh_rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"MTR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union", etcz={"name": "MTR.der_rewrite_c_ast_Union"})
    def muh_rewrite_c_ast_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"MTR.muh_rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"MTR.cast.meta: {meta}\n")
        return a * b


class DubDerTypeRewriter(DerivedTypeRewriter):
    @rewriter_dec("typing", "Union", etcz={"name": "DDTR.dub_rewrite_typing_Union"})
    def dub_rewrite_typing_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"DDTR.dub_rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"DDTR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union", etcz={"name": "DDTR.dub_rewrite_c_ast_Union"})
    def dub_rewrite_c_ast_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"DDTR.dub_rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {id(meta):#010x}"
        )
        print(f"DDTR.cast.meta: {meta}\n")
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
    print(f"rw_ty c_ast.Union: 100, 200: {tr.rewrite_type(np_c, 100_000, 200_000)}")

    print("\n" * 7)

    dtr = DerivedTypeRewriter()
    print(f"rw_dty typing.Union: 10, 20: {dtr.rewrite_type(np_t, 30, 40)}")
    print("\n" * 1)
    print(f"rw_dty c_ast.Union: 100, 200: {dtr.rewrite_type(np_c, 300_000, 400_000)}")

    print("\n" * 7)

    mtr = MuhrivedTypeRewriter()
    print(f"rw_mty typing.Union: 10, 20: {mtr.rewrite_type(np_t, 50, 50)}")
    print("\n" * 1)
    print(f"rw_mty c_ast.Union: 100, 200: {mtr.rewrite_type(np_c, 500_000, 500_000)}")

    print("\n" * 7)

    ddtr = DubDerTypeRewriter()
    print(f"rw_ddty typing.Union: 10, 20: {ddtr.rewrite_type(np_t, 60, 60)}")
    print("\n" * 1)
    print(f"rw_ddty c_ast.Union: 100, 200: {ddtr.rewrite_type(np_c, 600_000, 600_000)}")

    print("\n" * 5)

    print("tr() dicts:")
    dict_id_str = " ".join([f"{id(p):#010x}" for p in tr._infos.dicts])
    print(f"d*: {dict_id_str}")
    print(tr._infos.dicts)

    print("\n" * 3)

    print("dtr() dicts:")
    dict_id_str = " ".join([f"{id(p):#010x}" for p in dtr._infos.dicts])
    print(f"d*: {dict_id_str}")
    print(dtr._infos.dicts)
