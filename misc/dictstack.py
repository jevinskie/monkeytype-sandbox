import itertools
from collections import UserList
from collections.abc import Mapping, MutableMapping
from typing import TypeVar, cast

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_KTP = TypeVar("_KTP")
_VTP = TypeVar("_VTP")


# https://github.com/jaraco/jaraco.collections
# MIT licensed
class DictStack(UserList[MutableMapping[_KT, _VT]], MutableMapping[_KT, _VT]):
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
    >>> stack.push(dict(a=3))
    >>> stack['a']
    3
    >>> stack['a'] = 4
    >>> set(stack.keys()) == set(['a', 'b', 'c'])
    True
    >>> set(stack.items()) == set([('a', 4), ('b', 2), ('c', 2)])
    True
    >>> dict(**stack) == dict(stack) == dict(a=4, c=2, b=2)
    True
    >>> d = stack.pop()
    >>> stack['a']
    2
    >>> d
    {'a': 4}
    >>> d = stack.pop()
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

    @property
    def dicts(self) -> list[MutableMapping[_KT, _VT]]:
        return cast(list[MutableMapping[_KT, _VT]], self.data)

    def __iter__(self):
        return iter(dict.fromkeys(itertools.chain.from_iterable(c.keys() for c in self.dicts)))

    def __getitem__(self, key):
        for scope in reversed(tuple(self.dicts)):
            if key in scope:
                return scope[key]
        raise KeyError(key)

    push = UserList.append

    def __contains__(self, other):
        return Mapping.__contains__(self, other)

    def __len__(self):
        return len(list(iter(self)))

    def __setitem__(self, key, item):
        last_dict = self.dicts[-1]
        return last_dict.__setitem__(key, item)

    def __delitem__(self, key):
        last_dict = self.dicts[-1]
        return last_dict.__delitem__(key)

    # @overload
    # def pop(self, key: _KT, /) -> _VT:
    #     assert_never(cast(Never, None))
    # @overload
    # def pop(self, key: _KT, /, default: _VT) -> _VT: ...
    # @overload
    # def pop(self, _KT, /, default: _T) -> _VT | _T: ...
    # workaround for mypy confusion
    # def pop(self, index: int = 0) -> MutableMapping[_KT, _VT]:
    #     return self.dicts.pop(index)
    def pop(self, *args, **kwargs):
        return self.dicts.pop(*args, **kwargs)


MutableMapping.register(DictStack)  # type: ignore
