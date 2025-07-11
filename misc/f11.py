from __future__ import annotations

import sys

from rich import print


class Calc:
    # d: int

    def add(self, a: int, b: int) -> int:
        at = a + 0
        ot = self.permeth()
        return at + b + ot

    def mul(self, a: int, b: int) -> int:
        mt = self.permeth()
        return a * b + mt

    def permeth(self) -> int:
        f = sys._getframe(1)
        print(f)
        print(f.f_globals)
        print(f.f_locals)
        return 10


if __name__ == "__main__":

    def f():
        c = Calc()
        print(c.add(1, 2))
        print(c.mul(3, 7))

    f()
