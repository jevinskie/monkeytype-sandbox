import ast


def parsemod_inner(foo):
    return ast.dump(ast.parse(foo["src"]), indent=2)


def parsemod(src):
    return parsemod_inner({"src": src})


def make_dict():
    c1 = ast.Constant(1)
    c100 = ast.Constant(100)
    d = ast.Dict([c1], [c100])
    return ast.dump(d, indent=2)


class Union(ast.AST):
    def __init__(self):
        super().__init__()
        # print("Union(ast.Expr) __init__")


def get_union_inner():
    return Union()


def get_union():
    return get_union_inner()
