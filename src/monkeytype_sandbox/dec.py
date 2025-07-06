from __future__ import annotations

import typing
from typing import Any
from typing import Any as TEAny

import typing_extensions

if typing_extensions.Any is not typing.Any:
    raise TypeError
if TEAny is not Any:
    raise TypeError


class MQN(typing_extensions.Protocol):
    m: str
    qn: str


class MQNR:
    m: str
    qn: str


if typing_extensions.TYPE_CHECKING:
    typing_extensions.reveal_type(MQN)
    typing_extensions.reveal_type(MQNR)
    # typing_extensions.reveal_type(MQN())
    typing_extensions.reveal_type(MQNR())
    if hasattr(MQN, "m"):
        typing_extensions.reveal_type(MQN.m)
    if hasattr(MQNR, "m"):
        typing_extensions.reveal_type(MQNR.m)
    if hasattr(MQNR(), "m"):
        typing_extensions.reveal_type(MQNR().m)

_F = typing_extensions.TypeVar("_F", bound=typing_extensions.Callable[..., typing_extensions.Any])


class register:
    def __init__(self, mod: str, qualname: str):
        print(f"register __init__ self: {self} mod: {mod} qualname: {qualname}")
        self.m = mod
        self.qn = qualname

    def __call__(self, func: _F) -> _F:
        print(f"register __call__ self: {self} func: {func}")
        setattr(func, "m", self.m)
        setattr(func, "qn", self.qn)
        return func


class TypeRewriter:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        print(f"TypeRewriter __init__ self: {self} args: {args} kwargs: {kwargs}")


class BasicTypeRewriter(TypeRewriter):
    def rewrite(self) -> None:
        print(f"BasicTypeRewriter rewrite self: {self}")
        self.rewrite_typing_extensions_union()
        self.rewrite_pycp_union()

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
