import functools
from typing import TYPE_CHECKING, reveal_type


# https://github.com/jaraco/jaraco.functools/blob/main/jaraco/functools/__init__.py
def once(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(wrapper, "saved_result"):
            wrapper.saved_result = func(*args, **kwargs)
        return wrapper.saved_result

    wrapper.reset = lambda: vars(wrapper).__delitem__("saved_result")
    return wrapper


add_three = once(lambda a: a + 3)
print(add_three(3))
print(add_three(9))
del add_three.saved_result
print(add_three(9))
print(add_three(6))

if TYPE_CHECKING:
    reveal_type(once)
    reveal_type(once.wrapper)
    reveal_type(add_three)
    reveal_type(add_three.saved_result)
