#!/usr/bin/env python3

import pytest
from dictstack import DictStack


class TestDictStack:
    def test_ds_simple(self):
        stack = DictStack([dict(a=1, c=2), dict(b=2, a=2)])
        assert stack["a"] == 2
        assert stack["b"] == 2
        assert stack["c"] == 2


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__])
