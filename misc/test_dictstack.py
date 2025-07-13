#!/usr/bin/env python3

from collections.abc import MutableMapping, MutableSequence
from types import MappingProxyType

import pytest
from dictstack import DictStack
from rich import print
from rich import print as rprint

MutableMapping._dump_registry.__globals__["__builtins__"]["print"] = rprint
MutableSequence._dump_registry.__globals__["__builtins__"]["print"] = rprint


class TestDictStack:
    def test_ds_simple(self):
        stack = DictStack([dict(a=1, c=2), dict(b=2, a=2)])
        assert stack["a"] == 2
        assert stack["b"] == 2
        assert stack["c"] == 2


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__])
    MutableMapping._dump_registry()
    MutableSequence._dump_registry()
    print(MappingProxyType(DictStack([dict(a=1, c=2), dict(b=2, a=2)])))
