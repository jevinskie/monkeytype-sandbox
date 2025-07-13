import itertools
from collections import UserList
from collections.abc import Callable, Mapping, MutableMapping
from typing import Any, ParamSpec, TypeVar

_T = TypeVar("_T")
_F = TypeVar("_F", bound=Callable[..., Any])
_P = ParamSpec("_P")
_R_co = TypeVar("_R_co", covariant=True)


# https://github.com/jaraco/jaraco.collections
# MIT licensed
class DictStack(UserList, MutableMapping):
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
    >>> d = stack.pop()
    >>> stack['a']
    1
    >>> stack.get('b', None)
    >>> 'c' in stack
    True
    >>> del stack['c']
    >>> dict(stack)
    {'a': 1}
    """

    @property
    def dicts(self):
        return self.data

    def __iter__(self):
        return iter(dict.fromkeys(itertools.chain.from_iterable(c.keys() for c in self.data)))

    def __getitem__(self, key):
        for scope in reversed(tuple(self.data)):
            if key in scope:
                return scope[key]
        raise KeyError(key)

    push = UserList.append

    def __contains__(self, other):
        return Mapping.__contains__(self, other)

    def __len__(self):
        return len(list(iter(self)))

    def __setitem__(self, key, item):
        last_dict = self.data[-1]
        return last_dict.__setitem__(key, item)

    def __delitem__(self, key):
        last_dict = self.data[-1]
        return last_dict.__delitem__(key)

    # workaround for mypy confusion
    def pop(self, *args, **kwargs):
        return list.pop(self.data, *args, **kwargs)


MutableMapping.register(DictStack)
