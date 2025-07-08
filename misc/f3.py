from types import MethodType
from typing import Any, Callable, Generic, ParamSpec, Protocol, TypeVar, cast, overload

P = ParamSpec("P")
R = TypeVar("R", covariant=True)
P_Method = ParamSpec("P_Method")
Self = TypeVar("Self")


class CallableWithMetadata(Protocol[P, R]):
    __metadata__: tuple[str, ...]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...


class BoundMetadataMethod:
    def __init__(self, method: Callable[..., Any], metadata: tuple[str, ...]) -> None:
        self._method = method
        self.__metadata__ = metadata

    def __call__(self, a: int, b: int) -> int:  # type: ignore
        return self._method(a, b)


class MetadataFunction(Generic[P, R]):
    def __init__(self, func: Callable[P, R], metadata: tuple[str, ...]) -> None:
        self._func = func
        self.__metadata__ = metadata

    @overload
    def __get__(self, instance: None, owner: Any) -> CallableWithMetadata[P, R]: ...

    @overload
    def __get__(self, instance: Any, owner: Any) -> CallableWithMetadata[..., R]: ...

    def __get__(self, instance: Any, owner: Any) -> Any:
        if instance is None:
            return cast(CallableWithMetadata[P, R], self)
        bound = MethodType(self._func, instance)
        result = BoundMetadataMethod(bound, self.__metadata__)
        return result
        # update_wrapper(self, func)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._func(*args, **kwargs)


def add_metadata(*meta: str) -> Callable[[Callable[P, R]], CallableWithMetadata[P, R]]:
    def decorator(func: Callable[P, R]) -> CallableWithMetadata[P, R]:
        r = MetadataFunction(func, meta)
        return cast(CallableWithMetadata[P, R], r)

    return decorator


# Test cases
def test_function_metadata() -> None:
    @add_metadata("foo", "bar")
    def multiply(x: int, y: int) -> int:
        return x * y

    assert multiply(2, 3) == 6
    assert multiply.__metadata__ == ("foo", "bar")


def test_method_metadata() -> None:
    class Calculator:
        @add_metadata("method", "test")
        def add(self, a: int, b: int) -> int:
            return a + b

    calc = Calculator()
    result = calc.add(5, 7)
    metadata = calc.add.__metadata__

    assert result == 12
    assert metadata == ("method", "test")


def run_tests() -> None:
    test_function_metadata()
    test_method_metadata()
    print("All tests passed.")


if __name__ == "__main__":
    run_tests()
