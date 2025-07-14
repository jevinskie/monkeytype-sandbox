from types import MappingProxyType as MPT
from typing import Any


def pid(obj: Any) -> str:
    return f"{id(obj):#010x}"


class Base:
    d: dict
    dp: MPT
    n: str

    def __init__(self, name: str):
        self.n = name
        self.d = dict()
        self.dp = MPT(self.d)

    def __repr__(self) -> str:
        return f"<Base n: {self.n} d: {self.d} dp: {self.dp} at {pid(self)}>"


b = Base("base")
print(b)
b.d["a"] = 1
print(b)
