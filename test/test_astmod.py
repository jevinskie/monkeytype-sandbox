#!/usr/bin/env python3

import inspect

from monkeytype_sandbox.astmod import get_union, make_dict, parsemod

print(parsemod(open(inspect.getfile(parsemod)).read()))

print(make_dict())

print(get_union())
