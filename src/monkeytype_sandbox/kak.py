from functools import wraps

from rich import print


def decp(a=object(), b=object(), **kwargs):
    print(f"a: {a} b: {b} kw: {kwargs}")

    def _z(n):
        @wraps(n)
        def w(*args, **kwargs2):
            print(f"args: {args} kw: {kwargs2}")
            return n(*args, **kwargs2)

        return w

    return _z


@decp()
class Foo:
    @decp(a=2, b=3, c=4, d="5")
    def foo(self):
        print("foo")


f = Foo()
f.foo()
