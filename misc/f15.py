from __future__ import annotations

from collections.abc import Callable
from types import MappingProxyType
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
_R_co = TypeVar("_R_co", covariant=True)


class Mathod(Generic[_T, _P, _R_co]):
    _f: Callable[Concatenate[_T, _P], _R_co]

    def __init__(self, func: Callable[Concatenate[_T, _P], _R_co]) -> None:
        print(f"Mathod.__init__ func: {func}")
        self._f = func

    @overload
    def __get__(self, obj: None, cls: type, /) -> Callable[Concatenate[_T, _P], _R_co]: ...
    @overload
    def __get__(self, obj: _T, cls: type[_T] | None = None, /) -> Callable[_P, _R_co]: ...
    def __get__(
        self, obj: _T | None, cls: type[_T] | None = None, /
    ) -> Callable[Concatenate[_T, _P], _R_co] | Callable[_P, _R_co]:
        print(f"Mathod.__get__ self: {self} obj: {obj} cls: {cls}")
        if obj is None:
            # fr2: Callable[Concatenate[_T, _P], _R_co] = self._f
            fr2 = self._f
            if TYPE_CHECKING:
                reveal_type(fr2)
            return fr2
        f = self._f
        fr = f.__get__(obj, cls)
        frc = cast(Callable[_P, _R_co], fr)
        if TYPE_CHECKING:
            reveal_type(f)
            reveal_type(fr)
            reveal_type(frc)
        return frc

    def __set_name__(self, owner: Any, name: Any) -> None:
        print(f"Mathod.__set_name__ self: {self} owner: {owner} name: {name}")


class call_on_me(Generic[_T, _P, _R_co]):
    _mod: str
    _qn: str
    _f: Callable[Concatenate[_T, _P], _R_co]

    def __init__(self, module: str, qualname: str, /) -> None:
        print(f"CoM.__init__ mod: {module} qn: {qualname}")
        self._mod = module
        self._qn = qualname

    @overload
    def __get__(self, obj: None, cls: type, /) -> Callable[Concatenate[_T, _P], _R_co]: ...
    @overload
    def __get__(self, obj: _T, cls: type[_T] | None = None, /) -> Callable[_P, _R_co]: ...
    def __get__(
        self, obj: _T | None, cls: type[_T] | None = None, /
    ) -> Callable[Concatenate[_T, _P], _R_co] | Callable[_P, _R_co]:
        print(f"CoM.__get__ self: {self} obj: {obj} cls: {cls}")
        if obj is None:
            # fr2: Callable[Concatenate[_T, _P], _R_co] = self._f
            fr2 = self._f
            if TYPE_CHECKING:
                reveal_type(fr2)
            return fr2
        f = self._f
        fr = f.__get__(obj, cls)
        frc = cast(Callable[_P, _R_co], fr)
        if TYPE_CHECKING:
            reveal_type(f)
            reveal_type(fr)
            reveal_type(frc)
        return frc

    def __set_name__(self, obj: Any, name: Any) -> None:
        print(f"CoM.__set_name__ self: {self} owner: {obj} name: {name}")
        if obj is None:
            raise ValueError(f"none obj? {obj}")
        if not hasattr(obj, "_infos"):
            d: dict[tuple[str, str], Any] = {}
            setattr(obj, "_infos", d)
        infos: dict[tuple[str, str], Any] = obj._infos
        key = (self._mod, self._qn)
        infos[key] = {"self": self, "name": name}

    @property
    def __func__(self) -> Callable[Concatenate[_T, _P], _R_co]:
        print(f"CoM.__func__ self: {self}")
        return self._f

    def __call__(self, func: Callable[Concatenate[_T, _P], _R_co], /) -> Self:
        print(f"CoM.__call__ self: {self} func: {func}")
        self._f = func
        return self

    if TYPE_CHECKING:
        reveal_type(__call__)
    print(__call__)


print(call_on_me.__call__)


def _fancy(self, a: int, b: int) -> int:
    print(f"_fancy() self: {self} a: {a} b: {b} infos: {self.infos}")
    return a + b


print(f"_fancy: {_fancy}")
if TYPE_CHECKING:
    reveal_type(_fancy)


class Bar:
    _n: int
    _infos: dict[tuple[str, str], Any]
    _infos_ro: MappingProxyType[tuple[str, str], Any]

    _fcom = call_on_me("pycparser.c_ast", "Union")
    fancy = _fcom(_fancy)

    def __init__(self, n: int) -> None:
        self._n = n
        self._infos_ro = MappingProxyType(self._infos)

    @property
    def infos(self) -> MappingProxyType[tuple[str, str], Any]:
        return self._infos_ro

    def plain(self, a: int, b: int) -> int:
        print(f"plain self: {self} a: {a} b: {b}")
        return a + b

    @Mathod
    def mathod(self, a: int, b: int) -> int:
        print(f"mathod self: {self} a: {a} b: {b}")
        return a + b

    print(f"_fcom: {_fcom}")
    print(f"fancy: {fancy}")
    if TYPE_CHECKING:
        reveal_type(_fcom)
        reveal_type(fancy)


b = Bar(7)
print(b.infos)
print(b.fancy(1, 2))
print(Bar.fancy(b, 1, 2))

if TYPE_CHECKING:
    reveal_type(Bar.plain)
    reveal_type(b.plain)
    reveal_type(Bar.mathod)
    reveal_type(b.mathod)
    reveal_type(Bar.fancy)
    reveal_type(b.fancy)
