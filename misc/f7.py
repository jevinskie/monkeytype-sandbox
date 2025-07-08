from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, reveal_type

F = TypeVar("F", bound=Callable[..., Any])
P = ParamSpec("P")
R = TypeVar("R")


def predicate(author: str, version: str, **others: Any) -> Callable[[F], F]:
    def _predicate(func: F) -> F:
        func.meta = {"author": author, "version": version}
        func.meta.update(others)
        return func

    return _predicate


# @predicate("foo", "bar")
def _myfunc(i: int, j: int) -> int:
    return i + j


print(_myfunc(1, 2))

if TYPE_CHECKING:
    reveal_type(_myfunc)

myfunc = predicate("foo", "bar")(_myfunc)

print(myfunc.meta)
print(myfunc(1, 2))

if TYPE_CHECKING:
    reveal_type(myfunc)
    reveal_type(myfunc.meta)


class predc:
    author: str
    version: str
    others: Any

    def __init__(self, author: str, version: str, **others: Any) -> None:
        print(f"predc __init__ self: {self} author: {author} ver: {version} other: {others}")
        self.author = author
        self.version = version
        self.others = others

    def __call__(self, func: F) -> F:
        print(f"predc __call__ self: {self} func: {func}")

        @wraps(func)
        def cw(*args: Any, **kwargs: Any):
            return func(*args, **kwargs)

        return cw


mfc = predc("buzz", "bazz")(_myfunc)

print(mfc(4, 3))

if TYPE_CHECKING:
    reveal_type(mfc)
