import typing

_F = typing.TypeVar("_F", bound=typing.Callable[..., typing.Any])


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
    def __init__(self, *args, **kwargs) -> None:
        print(f"TypeRewriter __init__ self: {self} args: {args} kwargs: {kwargs}")


class BasicTypeRewriter(TypeRewriter):
    def rewrite(self) -> None:
        print(f"BasicTypeRewriter rewrite self: {self}")
        self.rewrite_typing_union()
        self.rewrite_pycp_union()

    @register("typing", "Union")
    def rewrite_typing_union(self) -> None:
        print(f"rewrite_typing_union self: {self}")
        print(f"rewrite_typing_union.m: {self.rewrite_typing_union.m}")
        print(f"rewrite_typing_union.qn: {self.rewrite_typing_union.qn}")

    @register("pycparser.c_ast", "Union")
    def rewrite_pycp_union(self) -> None:
        print(f"rewrite_pycp_union self: {self}")
        print(f"rewrite_typing_union.m: {self.rewrite_pycp_union.m}")
        print(f"rewrite_typing_union.qn: {self.rewrite_pycp_union.qn}")
        if typing.TYPE_CHECKING:
            typing.reveal_type(self.rewrite_pycp_union.qn)


tr = TypeRewriter()
btr = BasicTypeRewriter()

btr.rewrite()

if typing.TYPE_CHECKING:
    typing.reveal_type(register)
    typing.reveal_type(register.__init__)
    typing.reveal_type(register.__call__)
    typing.reveal_type(TypeRewriter)
    typing.reveal_type(BasicTypeRewriter)
    typing.reveal_type(tr)
    typing.reveal_type(btr)
