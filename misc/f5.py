from collections.abc import Callable
from typing import TYPE_CHECKING, Concatenate, Generic, ParamSpec, Protocol, TypeVar, reveal_type

P = ParamSpec("P")
Owner = TypeVar("Owner")
Return = TypeVar("Return")


class Runner(Generic[Owner, P, Return]):
    def __init__(self, owner: Owner, func: Callable[Concatenate[Owner, P], Return]):
        self.func = func
        self.owner = owner

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Return:
        return self.func(self.owner, *args, **kwargs)


class MyDescriptor(Generic[Owner, P, Return]):
    def __init__(self, func: Callable[Concatenate[Owner, P], Return]):
        self.func = func

    def __get__(self, owner: Owner, type: type[Owner]) -> Runner[Owner, P, Return]:
        return Runner(owner, self.func)


def with_descriptor(
    func: Callable[Concatenate[Owner, P], Return],
) -> MyDescriptor[Owner, P, Return]:
    return MyDescriptor(func)


class MyProtocol(Protocol):
    def my_method(self, i: int) -> str: ...


class MyClass:
    @with_descriptor
    def my_method(self, i: int) -> str:
        return f"hello {i}"


class PlainClass:
    def my_method(self, i: int) -> str:
        return f"hello {i}"


concrete_instance = MyClass()

if TYPE_CHECKING:
    reveal_type(
        concrete_instance.my_method
    )  # W: Type of "concrete_instance.my_method" is "Runner[MyClass, (i: int), str]"
as_callable: Callable[[int], str] = concrete_instance.my_method  # successful type checking

alias_instance: MyProtocol = concrete_instance  # type checking fails
if TYPE_CHECKING:
    reveal_type(alias_instance.my_method)  # W: Type of "my_instance.my_method" is "(i: int) -> str"

assert alias_instance.my_method(8) == "hello 8" == as_callable(8)


plain_instance = PlainClass()

if TYPE_CHECKING:
    reveal_type(
        plain_instance.my_method
    )  # W: Type of "concrete_instance.my_method" is "Runner[MyClass, (i: int), str]"
plain_as_callable: Callable[[int], str] = plain_instance.my_method  # successful type checking

plain_alias_instance: MyProtocol = plain_instance  # type checking fails
if TYPE_CHECKING:
    reveal_type(
        plain_alias_instance.my_method
    )  # W: Type of "my_instance.my_method" is "(i: int) -> str"

assert plain_alias_instance.my_method(8) == "hello 8" == plain_as_callable(8)
