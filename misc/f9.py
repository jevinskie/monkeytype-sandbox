from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar, reveal_type

F = TypeVar("F", bound=Callable[..., Any])


def route(url: str) -> Callable[[F], F]: ...


# def route[F: Callable[..., Any]](url: str) -> Callable[[F], F]: ...


@route(url="/")
def index(request: Any) -> str:
    return "Hello world"


if TYPE_CHECKING:
    # reveal_type(F)
    reveal_type(route)
    reveal_type(index)
