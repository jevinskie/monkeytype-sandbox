from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
)

import rich.pretty
from f15 import (
    AMI,
    AMIS,
    GenericTypeRewriter,
    MuhrivedTypeRewriter,
    NamePath,
    TypeRewriter,
    pid,
    rewriter_dec,
)

if not TYPE_CHECKING:
    try:
        from rich import print
        # pass
    except ImportError:
        pass
    try:
        from rich import inspect as rinspect
    except ImportError:

        def rinspect(*args: Any, **kwargs: Any) -> None:
            print(*args)

else:

    def rinspect(*args: Any, **kwargs: Any) -> None: ...


class DerivedTypeRewriter(TypeRewriter):
    @rewriter_dec("typing", "Union", {"name": "DTR.der_rewrite_typing_Union"})
    def der_rewrite_typing_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"DTR.der_rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}"
        )
        # print(f"DTR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union", {"name": "DTR.der_rewrite_c_ast_Union"})
    def der_rewrite_c_ast_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"DTR.der_rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}"
        )
        # print(f"DTR.cast.meta: {meta}\n")
        return a * b


class DubDerTypeRewriter(DerivedTypeRewriter):
    @rewriter_dec("typing", "Union", {"name": "DDTR.dub_rewrite_typing_Union"})
    def dub_rewrite_typing_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"DDTR.dub_rewrite_typing_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}"
        )
        # print(f"DDTR.type.meta: {meta}\n")
        return a + b

    @rewriter_dec("pycparser.c_ast", "Union", {"name": "DDTR.dub_rewrite_c_ast_Union"})
    def dub_rewrite_c_ast_Union(
        self, a: int, b: int, /, meta: AMI = AMIS, etc: dict[Any, Any] | None = None
    ) -> int:
        print(
            f"DDTR.dub_rewrite_c_ast_Union() self: {self} a: {a} b: {b} etc: {etc} id(m): {pid(meta)}"
        )
        # print(f"DDTR.cast.meta: {meta}\n")
        return a * b


print("GenericTypeRewriter._namespaces")
rich.pretty.pprint(GenericTypeRewriter)

if __name__ == "__main__":
    np_t = NamePath("typing", "Union")
    np_c = NamePath("pycparser.c_ast", "Union")
    np_s = NamePath("construct", "Union")
    print(f"np_t: {np_t}")
    print(f"np_c: {np_c}")
    print(f"np_s: {np_s}")
    # sys.exit()

    print("\n" * 3)

    tr = TypeRewriter()
    print(f"rw_ty typing.Union: 10, 20: {tr.rewrite_type(np_t, 10, 20)}")
    print("\n" * 1)
    print(f"rw_ty c_ast.Union: 100, 200: {tr.rewrite_type(np_c, 100_000, 200_000)}")

    print("\n" * 7)

    dtr = DerivedTypeRewriter()
    print(f"rw_dty typing.Union: 10, 20: {dtr.rewrite_type(np_t, 30, 40)}")
    print("\n" * 1)
    print(f"rw_dty c_ast.Union: 100, 200: {dtr.rewrite_type(np_c, 300_000, 400_000)}")

    print("\n" * 7)

    mtr = MuhrivedTypeRewriter()
    print(f"rw_mty typing.Union: 10, 20: {mtr.rewrite_type(np_t, 50, 50)}")
    print("\n" * 1)
    print(f"rw_mty c_ast.Union: 100, 200: {mtr.rewrite_type(np_c, 500_000, 500_000)}")
    print("\n" * 1)
    print(f"rw_mty construct.Union: 10, 20: {mtr.rewrite_type(np_s, 400_000, 400_000)}")

    print("\n" * 7)

    ddtr = DubDerTypeRewriter()
    print(f"rw_ddty typing.Union: 10, 20: {ddtr.rewrite_type(np_t, 60, 60)}")
    print("\n" * 1)
    print(f"rw_ddty c_ast.Union: 100, 200: {ddtr.rewrite_type(np_c, 600_000, 600_000)}")

    print("\n" * 5)
