# Idea: to keep compatibility with or to rewrite type aliases, abstract representation away from identity

A single type can have multiple names.
Not just in the `typing_extension.py: from typing import Any` identity that can be discovered with
`assert typing.Any is typing_extensions.Any` but also via groups of names that
are treated as a single type. e.g. `typing_extension.py: class Any: ...`.

Provide default configuration environment where sensible mappings are used and allow extension.

TODO: find good python-as-code config library


Ideally, to the extent possible, the original type alias name should be retained for a given
source location. Keep the original name enumerator of the type at a location reference and
at "rendering" time they can be reified as either their original alias or as a different alias.
