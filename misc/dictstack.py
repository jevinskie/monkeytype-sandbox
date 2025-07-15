from __future__ import annotations

import itertools
import traceback
from collections.abc import Iterable, Iterator, MutableMapping
from copy import copy
from types import MappingProxyType
from typing import ClassVar, TypeVar

import rich
import rich.pretty
import rich.repr
import rich.traceback

rich.pretty.install()
rich.traceback.install(show_locals=True)
traceback.print_stack.__globals__["__builtins__"]["print"] = rich.print

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
    >>> dict(stack.mapping)
    {'a': 3, 'c': 2, 'b': 2}
    >>> isinstance(stack.mapping, MappingProxyType)
    True
    >>> stack['a']
    3
    >>> stack['a'] = 4
    >>> stack.dicts
    [{'a': 1, 'c': 2}, {'b': 2, 'a': 2}, {'a': 4}]
    >>> dict(stack)
    {'a': 4, 'c': 2, 'b': 2}
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
    _all_instances: ClassVar[list[DictStack]] = []
    _name: str | None

    def __init__(
        self, dicts: Iterable[MutableMapping[_KT, _VT]] | None = None, name: str | None = None
    ) -> None:
        # traceback.print_stack()
        self._name = name
        self._dicts = list(dicts) if dicts is not None else []
        DictStack._all_instances.append(self)
        print("DictStack.__init__() all_instances:")
        rich.pretty.pprint(DictStack._all_instances)

    @property
    def dicts(self) -> list[MutableMapping[_KT, _VT]]:
        return self._dicts

    @property
    def mapping(self) -> MappingProxyType[_KT, _VT]:
        return MappingProxyType(dict(self))

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
        print(f"DictStack.__setitem__() name: {self._name} key: {key}")
        if not self._dicts:
            raise IndexError("DictStack stack is empty")
        self._dicts[-1][key] = item

    def __delitem__(self, key: _KT) -> None:
        if not self._dicts:
            raise IndexError("DictStack stack is empty")
        del self._dicts[-1][key]

    def __copy__(self) -> DictStack[_KT, _VT]:
        return DictStack(copy(self._dicts))

    def __rich_repr__(self) -> rich.repr.Result:
        yield "name", self._name
        yield "id", id(self)
        yield "keys", dict(self).keys()

    @property
    def name(self) -> str:
        if self._name is None:
            raise ValueError(f"DictStack name is none self: {self}")
        return self._name

    @staticmethod
    def all_instances() -> list[DictStack]:
        return DictStack._all_instances
