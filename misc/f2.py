from typing import Callable, TypeVar, cast

from typing_extensions import ParamSpec, Protocol

P = ParamSpec("P")
R = TypeVar("R", covariant=True)  # covariant so it can be used in return position


class CallableWithMetadata(Protocol[P, R]):
    __metadata__: tuple[str, ...]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...


def add_metadata(*meta: str) -> Callable[[Callable[P, R]], CallableWithMetadata[P, R]]:
    def decorator(func: Callable[P, R]) -> CallableWithMetadata[P, R]:
        setattr(func, "__metadata__", meta)
        return cast(CallableWithMetadata[P, R], func)

    return decorator


# === Example usage ===


@add_metadata("auth-required", "logging")
def greet(name: str, punctuation: str = "!") -> str:
    return f"Hello, {name}{punctuation}"


def demo() -> None:
    from typing import reveal_type

    reveal_type(
        greet
    )  # Revealed type: 'CallableWithMetadata[Concatenate[builtins.str, builtins.str], builtins.str]'
    reveal_type(greet.__metadata__)  # Revealed type: 'tuple[builtins.str, ...]'

    typed: CallableWithMetadata[[str, str], str] = greet
    reveal_type(
        typed
    )  # Revealed type: 'CallableWithMetadata[[builtins.str, builtins.str], builtins.str]'
    reveal_type(typed.__metadata__)  # Revealed type: 'tuple[builtins.str, ...]'

    print(greet("Alice"))
    print(greet.__metadata__)
    print(typed("Bob", "?"), typed.__metadata__)


if __name__ == "__main__":
    demo()
