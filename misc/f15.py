from __future__ import annotations

from collections.abc import Callable
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    Generic,
    ParamSpec,
    TypeVar,
    cast,
    overload,
    reveal_type,
)

if not TYPE_CHECKING:
    from rich import print

if not TYPE_CHECKING:
    from rich import inspect as rinspect
else:

    def rinspect(*args: Any, **kwargs: Any) -> None: ...


_P = ParamSpec("_P")
_T = TypeVar("_T")
_F = TypeVar("_F", bound=Callable[..., Any])
_TT = TypeVar("_TT", bound=type[Any])
_TO = TypeVar("_TO")
_R_co = TypeVar("_R_co", covariant=True)


class call_on_me_inner(Generic[_T, _P, _R_co]):
    _f: Callable[Concatenate[_T, _P], _R_co]
    _mod: str
    _qn: str

    def __init__(
        self, func: Callable[Concatenate[_T, _P], _R_co], module: str, qualname: str, /
    ) -> None:
        print(f"CoMI.__init__ func: {func} module: {module} qualname: {qualname}")
        self._f = func
        self._mod = module
        self._qn = qualname

    @overload
    def __get__(self, obj: None, cls: type[_T], /) -> Callable[Concatenate[_T, _P], _R_co]: ...
    @overload
    def __get__(self, obj: _T, cls: type[_T] | None = None, /) -> Callable[_P, _R_co]: ...
    def __get__(
        self, obj: _T | None, cls: type[_T] | None = None, /
    ) -> Callable[Concatenate[_T, _P], _R_co] | Callable[_P, _R_co]:
        # def __get__(
        #     self, obj: _T | None, cls: type[_T] | None = None, /
        # ) -> Callable[Concatenate[_T, _P], _R_co] | Callable[_P, _R_co]:
        print(f"CoMI.__get__ self: {self} obj: {obj} cls: {cls}")
        if obj is None:
            # fr2: Callable[Concatenate[_T, _P], _R_co] = self._f
            fr2 = self._f
            if TYPE_CHECKING:
                reveal_type(fr2)
            print("CoMI.__get__ returning function")
            return fr2
        f = self._f
        fr = f.__get__(obj, cls)
        frc = cast(Callable[_P, _R_co], fr)
        if TYPE_CHECKING:
            reveal_type(f)
            reveal_type(fr)
            reveal_type(frc)
        print("CoMI.__get__ returning bound method")
        return frc

    def __set_name__(self, obj: Any, name: Any) -> None:
        print(f"CoMI.__set_name__ self: {self} owner: {obj} name: {name}")
        if obj is None:
            raise ValueError(f"none obj? {obj}")
        if not hasattr(obj, "_infos"):
            d: dict[tuple[str, str], Any] = {}
            setattr(obj, "_infos", d)
        infos: dict[tuple[str, str], Any] = obj._infos
        # infos = {}
        key = (self._mod, self._qn)
        infos[key] = {"self": self, "name": name}

    if TYPE_CHECKING:
        reveal_type(__get__)


class call_on_me:
    _mod: str
    _qn: str

    def __init__(self, module: str, qualname: str) -> None:
        print(f"CoM.__init__ mod: {module} qn: {qualname}")
        self._mod = module
        self._qn = qualname

    def __call__(self, func: _F, /) -> _F:
        comi = call_on_me_inner(func, self._mod, self._qn)
        print(f"CoM.__call__ self: {self} func: {func} comi: {comi}")
        comr = cast(_F, comi)
        if TYPE_CHECKING:
            reveal_type(comi)
            reveal_type(comr)
        return comr


class Bar:
    _n: int
    _infos: dict[tuple[str, str], Any]
    _infos_ro: MappingProxyType[tuple[str, str], Any]

    def __init__(self, n: int) -> None:
        self._n = n
        self._infos_ro = MappingProxyType(self._infos)

    @property
    def infos(self) -> MappingProxyType[tuple[str, str], Any]:
        return self._infos_ro

    def plain(self, a: int, b: int, /) -> int:
        print(f"plain() self: {self} a: {a} b: {b}")
        return a + b

    @call_on_me("typing", "Union")
    def fancy(self, a: int, b: int, /) -> int:
        print(f"fancy() self: {self} a: {a} b: {b} infos: {self.infos}")
        return a + b

    @call_on_me("pycparser.c_ast", "Union")
    def mancy(self, a: int, b: int) -> int:
        print(f"mancy() self: {self} a: {a} b: {b} infos: {self.infos}")
        return a * b

    if TYPE_CHECKING:
        reveal_type(plain)
        reveal_type(fancy)
        reveal_type(infos)
        reveal_type(mancy)


b = Bar(7)
print(f"b.infos: {b.infos}")
print(f"Bar.fancy: {Bar.fancy}")
print(f"b.fancy: {b.fancy}")
print(f"b.fancy(1, 2): {b.fancy(1, 2)}")
print(f"Bar.fancy(b, 1, 2): {Bar.fancy(b, 1, 2)}")
print(f"b.mancy(7, 11): {b.fancy(7, 11)}")
print(f"Bar.mancy(b, 7, 11): {Bar.fancy(b, 7, 11)}")

if TYPE_CHECKING:
    reveal_type(Bar.plain)
    reveal_type(b.plain)
    reveal_type(Bar.fancy)
    reveal_type(b.fancy)
    reveal_type(Bar.mancy)
    reveal_type(b.mancy)
    reveal_type(Bar.infos)
    reveal_type(b.infos)
