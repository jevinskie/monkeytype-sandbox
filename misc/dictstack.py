from __future__ import annotations

import itertools
from collections.abc import Iterable, Iterator, MutableMapping
from typing import TypeVar

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


# https://github.com/jaraco/jaraco.collections
# MIT licensed Copyright 2025 Jason R. Coombs
class DictStack(MutableMapping[_KT, _VT]):
    """
    A stack of dictionaries that behaves as a view on those dictionaries,
    giving preference to the last.

    >>> stack = DictStack([dict(a=1, c=2), dict(b=2, a=2)])
    >>> stack['a']
    2
    >>> stack['b']
    2
    >>> stack['c']
    2
    >>> len(stack)
    3
    >>> list(stack)
    ['a', 'c', 'b']
    >>> stack.dicts
    [{'a': 1, 'c': 2}, {'b': 2, 'a': 2}]
    >>> stack.pushdict(dict(a=3))
    >>> stack.dicts
    [{'a': 1, 'c': 2}, {'b': 2, 'a': 2}, {'a': 3}]
    >>> dict(stack)
    {'a': 3, 'c': 2, 'b': 2}
    >>> import types
    >>> dict(types.MappingProxyType(stack))
    {'a': 3, 'c': 2, 'b': 2}
    >>> stack['a']
    3
    >>> stack['a'] = 4
    >>> set(stack.keys()) == set(['a', 'b', 'c'])
    True
    >>> set(stack.items()) == set([('a', 4), ('b', 2), ('c', 2)])
    True
    >>> dict(**stack) == dict(stack) == dict(a=4, c=2, b=2)
    True
    >>> d = stack.popdict()
    >>> stack['a']
    2
    >>> d
    {'a': 4}
    >>> d = stack.popdict()
    >>> stack['a']
    1
    >>> d
    {'b': 2, 'a': 2}
    >>> stack.get('b', None)
    >>> 'c' in stack
    True
    >>> del stack['c']
    >>> dict(stack)
    {'a': 1}
    """

    _dicts: list[MutableMapping[_KT, _VT]]

    def __init__(self, dicts: Iterable[MutableMapping[_KT, _VT]] | None = None) -> None:
        super().__init__()
        self._dicts = list(dicts) if dicts is not None else []

    @property
    def dicts(self) -> list[MutableMapping[_KT, _VT]]:
        return self._dicts

    def __iter__(self) -> Iterator[_KT]:
        return iter(dict.fromkeys(itertools.chain.from_iterable(self._dicts)))

    def __getitem__(self, key: _KT) -> _VT:
        if not self._dicts:
            raise IndexError("DictStack stack is empty")
        for scope in reversed(self._dicts):
            if key in scope:
                return scope[key]
        raise KeyError(key)

    def pushdict(self, pushed_dict: MutableMapping[_KT, _VT] | None = None) -> None:
        return self._dicts.append(pushed_dict if pushed_dict is not None else {})

    def popdict(self, index: int = -1) -> MutableMapping[_KT, _VT]:
        if not self._dicts:
            raise IndexError("DictStack stack is empty")
        return self._dicts.pop(index)

    def __len__(self) -> int:
        return len(list(iter(self)))

    def __setitem__(self, key: _KT, item: _VT) -> None:
        if not self._dicts:
            raise IndexError("DictStack stack is empty")
        self._dicts[-1][key] = item

    def __delitem__(self, key: _KT) -> None:
        if not self._dicts:
            raise IndexError("DictStack stack is empty")
        del self._dicts[-1][key]
