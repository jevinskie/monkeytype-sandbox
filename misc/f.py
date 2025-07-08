from typing import Callable, TypeVar, cast

from typing_extensions import ParamSpec, Protocol

P = ParamSpec("P")
R = TypeVar("R", covariant=True)


class CallableWithMetadata(Protocol[P, R]):
    __metadata__: tuple[str, ...]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...


def add_metadata(*meta: str) -> Callable[[Callable[P, R]], CallableWithMetadata[P, R]]:
    def decorator(func: Callable[P, R]) -> CallableWithMetadata[P, R]:
        setattr(func, "__metadata__", meta)
        return cast(CallableWithMetadata[P, R], func)

    return decorator


# Example usage:


@add_metadata("auth-required", "logging")
def greet(name: str, punctuation: str = "!") -> str:
    return f"Hello, {name}{punctuation}"


def demo() -> None:
    print(greet("Alice"))
    print(greet.__metadata__)  # statically valid

    reveal: CallableWithMetadata[[str, str], str] = greet
    print(reveal("Bob", "?"), reveal.__metadata__)


if __name__ == "__main__":
    demo()
