from __future__ import annotations

import typing
from typing import TYPE_CHECKING, Callable

import typing_extensions
from typing_extensions import Any, ParamSpec, Protocol, TypeVar, reveal_type
from typing_extensions import Any as TEAny

if typing_extensions.Any is not typing.Any:
    raise TypeError
if TEAny is not Any:
    raise TypeError

_F = TypeVar("_F", bound=typing.Callable[..., typing.Any])
_P = ParamSpec("_P")
_R = TypeVar("_R", covariant=True)  # covariant so it can be used in return position


class _CallableWithMetadata(Protocol[_P, _R]):
    m: str
    qn: str

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R: ...


# def register(
#     mod: str, qualname: str
# ) -> Callable[[Callable[_P, _R]], _CallableWithMetadata[_P, _R]]:
#     def decorator(func: Callable[_P, _R]) -> _CallableWithMetadata[_P, _R]:
#         setattr(func, "m", mod)
#         setattr(func, "qn", qualname)
#         return cast(_CallableWithMetadata[_P, _R], func)

#     return decorator


class register:
    def __init__(self, mod: str, qualname: str):
        print(f"register __init__ self: {self} mod: {mod} qualname: {qualname}")
        self.m = mod
        self.qn = qualname

    def __call__(self, func: _F) -> _F:
        print(f"register __call__ self: {self} func: {func}")
        setattr(func, "m", self.m)
        setattr(func, "qn", self.qn)
        # return cast(_CallableWithMetadata[_P, _R], func)
        return func


@register("foo", "bar")
def cool(a: int, b: int) -> int:
    r = a + b
    print(f"a: {a} b: {b} a + b: {r} m: {cool.m} qn: {cool.qn}")
    return r


print(f"cool.m: {cool.m} cool.qn: {cool.qn}")
print(f"cool(3, 5): {cool(3, 5)}")

if TYPE_CHECKING:
    reveal_type(cool)
    reveal_type(cool.m)
    reveal_type(cool.qn)


class CoolClass:
    @register("foo", "bar")
    def cool_meth(self, a: int, b: int) -> int:
        r = a + b
        print(f"a: {a} b: {b} a + b: {r} m: {cool.m} qn: {cool.qn}")
        return r


cc = CoolClass()

if TYPE_CHECKING:
    reveal_type(CoolClass.cool_meth)
    reveal_type(CoolClass.cool_meth.m)
    reveal_type(CoolClass.cool_meth.qn)
    reveal_type(cc.cool_meth)
    reveal_type(cc.cool_meth.m)

_F = TypeVar("_F", bound=Callable[..., Any])


class register2:
    def __init__(self, mod: str, qualname: str):
        print(f"register2 __init__ self: {self} mod: {mod} qualname: {qualname}")
        self.m = mod
        self.qn = qualname

    def __call__(self, func: _F) -> _F:
        print(f"register2 __call__ self: {self} func: {func}")
        setattr(func, "m", self.m)
        setattr(func, "qn", self.qn)
        return func


class TypeRewriter:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        print(f"TypeRewriter __init__ self: {self} args: {args} kwargs: {kwargs}")


class BasicTypeRewriter(TypeRewriter):
    @register("typing_extensions", "Union")
    def rewrite_typing_extensions_union(self) -> None:
        print(f"rewrite_typing_extensions_union self: {self}")
        print(f"rewrite_typing_extensions_union.m: {self.rewrite_typing_extensions_union.m}")
        print(f"rewrite_typing_extensions_union.qn: {self.rewrite_typing_extensions_union.qn}")

    @register("pycparser.c_ast", "Union")
    def rewrite_pycp_union(self) -> None:
        print(f"rewrite_pycp_union self: {self}")
        print(f"rewrite_typing_extensions_union.m: {self.rewrite_pycp_union.m}")
        print(f"rewrite_typing_extensions_union.qn: {self.rewrite_pycp_union.qn}")
        if typing_extensions.TYPE_CHECKING:
            typing_extensions.reveal_type(self.rewrite_pycp_union.qn)

    def rewrite(self) -> None:
        print(f"BasicTypeRewriter rewrite self: {self}")
        if TYPE_CHECKING:
            reveal_type(self.rewrite_typing_extensions_union)
            reveal_type(self.rewrite_pycp_union)
        self.rewrite_typing_extensions_union()
        self.rewrite_pycp_union()


tr = TypeRewriter()
btr = BasicTypeRewriter()

btr.rewrite()

if typing_extensions.TYPE_CHECKING:
    typing_extensions.reveal_type(register)
    typing_extensions.reveal_type(register.__init__)
    typing_extensions.reveal_type(register.__call__)
    typing_extensions.reveal_type(TypeRewriter)
    typing_extensions.reveal_type(BasicTypeRewriter)
    typing_extensions.reveal_type(tr)
    typing_extensions.reveal_type(btr)
