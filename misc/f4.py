from __future__ import annotations

import inspect
from typing import Any, Callable, Generic, ParamSpec, TypeVar, cast

import pytest

P = ParamSpec("P")
R = TypeVar("R")


class _BoundInstanceMethod(Generic[P, R]):
    def __init__(self, fn: Callable[P, R], instance: Any, meta: tuple[str, str]) -> None:
        self._fn = fn
        self._inst = instance
        self.meta: tuple[str, str] = meta
        orig = inspect.signature(fn)
        params = list(orig.parameters.values())[1:]
        self.__signature__ = inspect.Signature(
            parameters=params, return_annotation=orig.return_annotation
        )

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._fn(self._inst, *args, **kwargs)


class MethodMeta(Generic[P, R]):
    def __init__(self, fn: Callable[P, R], meta: tuple[str, str]) -> None:
        self._fn = fn
        self.meta: tuple[str, str] = meta
        self.__signature__ = inspect.signature(fn)

    def __get__(self, instance: Any, owner: Any) -> Callable[P, R] | _BoundInstanceMethod[P, R]:
        if instance is None:
            return cast(Callable[P, R], self)
        return _BoundInstanceMethod(self._fn, instance, self.meta)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._fn(*args, **kwargs)


def attach_meta(meta: tuple[str, str]) -> Callable[[Callable[P, R]], MethodMeta[P, R]]:
    def wrap(fn: Callable[P, R]) -> MethodMeta[P, R]:
        return MethodMeta(fn, meta)

    return wrap


# --- Tests ---


def test_basic_metadata_and_call() -> None:
    class A:
        @attach_meta(("hello", "world"))
        def f(self, x: int) -> int:
            return x + 1

    a = A()
    b = cast(_BoundInstanceMethod[[A, int], int], a)
    assert A.f.meta == ("hello", "world")
    assert a.f.meta == ("hello", "world")
    assert a.f(5) == 6
    assert b.f.meta == ("hello", "world")
    assert b.f(5) == 6


def test_default_parameters_and_signature() -> None:
    class B:
        @attach_meta(("d", "p"))
        def g(self, a: int, b: str = "x") -> str:
            return b * a

    b = B()
    sig_unbound = inspect.signature(B.g)
    params = sig_unbound.parameters
    assert params["a"].annotation is int
    assert params["b"].default == "x"
    sig_bound = inspect.signature(b.g)
    assert list(sig_bound.parameters.keys()) == ["a", "b"]
    assert sig_bound.return_annotation is str
    assert b.g(3) == "xxx"


def test_direct_unbound_call() -> None:
    class C:
        @attach_meta(("u", "v"))
        def h(self, x, y):
            return (self, x, y)

    result = C.h(C(), 7, 8)
    assert isinstance(result[0], C) and result[1:] == (7, 8)


def test_metadata_immutable() -> None:
    class D:
        @attach_meta(("i", "j"))
        def m(self):
            pass

    mval = D().m.meta
    import pytest

    with pytest.raises(TypeError):
        mval[0] = "changed"


def test_multiple_methods_independent() -> None:
    class E:
        @attach_meta(("a", "b"))
        def x(self):
            return 1

        @attach_meta(("c", "d"))
        def y(self):
            return 2

    e = E()
    assert E.x.meta == ("a", "b")
    assert E.y.meta == ("c", "d")
    assert e.x() == 1 and e.y() == 2


def test_overwrite_meta() -> None:
    class F:
        def z(self):
            return 0

    F.z = attach_meta(("one", "two"))(F.z)
    assert F.z.meta == ("one", "two")
    F.z = attach_meta(("new", "meta"))(F.z)
    assert F.z.meta == ("new", "meta")


def test_inheritance_preserves_meta() -> None:
    class G:
        @attach_meta(("orig", "val"))
        def m(self):
            return "g"

    class H(G):
        pass

    assert G.m.meta == ("orig", "val")
    assert H.m.meta == ("orig", "val")


def test_annotation_and_return_type() -> None:
    class II:
        @attach_meta(("a", "b"))
        def foo(self, x: float) -> float:
            return x * 2

    i = II()
    sig = inspect.signature(i.foo)
    assert sig.return_annotation is float
    assert sig.parameters["x"].annotation is float


def test_multiple_instances_meta_share() -> None:
    class J:
        @attach_meta(("one", "two"))
        def k(self):
            pass

    j1, j2 = J(), J()
    assert j1.k.meta is j2.k.meta


def test_meta_on_descriptor_only() -> None:
    class K:
        @attach_meta(("m", "n"))
        def k(self):
            pass

    # underlying function has no .meta
    desc = K.__dict__["k"]
    assert hasattr(desc, "meta")
    assert not hasattr(desc._fn, "meta")


if __name__ == "__main__":
    import sys

    pytest.main(sys.argv)
