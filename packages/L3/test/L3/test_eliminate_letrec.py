import L2.syntax as L2
from L3.eliminate_letrec import eliminate_letrec_program, eliminate_letrec_term
from L3.syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Immediate,
    Let,
    LetRec,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
)


def test_eliminate_letrec_program_simple():
    program = Program(parameters=["x"], body=Immediate(value=1))
    result = eliminate_letrec_program(program)
    assert isinstance(result, L2.Program)
    assert list(result.parameters) == ["x"]
    assert result.body == L2.Immediate(value=1)


def test_eliminate_letrec_program_with_letrec():
    program = Program(
        parameters=["x"],
        body=LetRec(
            bindings=[("fact", Abstract(parameters=["n"], body=Reference(name="n")))],
            body=Apply(target=Reference(name="fact"), arguments=[Reference(name="x")]),
        ),
    )
    result = eliminate_letrec_program(program)
    assert isinstance(result, L2.Program)
    assert isinstance(result.body, L2.Let)


def test_eliminate_letrec_term_single_binding():
    term = LetRec(
        bindings=[
            (
                "f",
                Abstract(
                    parameters=["n"],
                    body=Apply(target=Reference(name="f"), arguments=[Reference(name="n")]),
                ),
            )
        ],
        body=Apply(target=Reference(name="f"), arguments=[Immediate(value=0)]),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    assert len(result.bindings) == 1
    name, alloc = result.bindings[0]
    assert name == "f"
    assert alloc == L2.Allocate(count=1)
    assert isinstance(result.body, L2.Begin)
    assert len(result.body.effects) == 1
    store = result.body.effects[0]
    assert isinstance(store, L2.Store)
    assert store.base == L2.Reference(name="f")
    assert store.index == 0
    assert isinstance(store.value, L2.Abstract)
    inner_apply = store.value.body
    assert isinstance(inner_apply, L2.Apply)
    assert isinstance(inner_apply.target, L2.Load)
    assert inner_apply.target.base == L2.Reference(name="f")
    body = result.body.value
    assert isinstance(body, L2.Apply)
    assert isinstance(body.target, L2.Load)
    assert body.target.base == L2.Reference(name="f")


def test_eliminate_letrec_term_multiple_bindings():
    term = LetRec(
        bindings=[
            ("f", Immediate(value=1)),
            ("g", Reference(name="f")),
        ],
        body=Reference(name="g"),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    assert len(result.bindings) == 2
    assert result.bindings[0][1] == L2.Allocate(count=1)
    assert result.bindings[1][1] == L2.Allocate(count=1)
    assert isinstance(result.body, L2.Begin)
    assert len(result.body.effects) == 2


def test_eliminate_letrec_term_empty_bindings():
    term = LetRec(bindings=[], body=Immediate(value=42))
    result = eliminate_letrec_term(term)
    assert result == L2.Immediate(value=42)


def test_eliminate_letrec_term_let():
    term = Let(bindings=[("x", Immediate(value=5))], body=Reference(name="x"))
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    assert result.bindings[0][0] == "x"
    assert result.bindings[0][1] == L2.Immediate(value=5)
    assert result.body == L2.Reference(name="x")


def test_eliminate_letrec_term_reference():
    result = eliminate_letrec_term(Reference(name="x"))
    assert result == L2.Reference(name="x")


def test_eliminate_letrec_term_abstract():
    term = Abstract(parameters=["x", "y"], body=Reference(name="x"))
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Abstract)
    assert list(result.parameters) == ["x", "y"]
    assert result.body == L2.Reference(name="x")


def test_eliminate_letrec_term_apply():
    term = Apply(target=Reference(name="f"), arguments=[Immediate(value=1), Immediate(value=2)])
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Apply)
    assert result.target == L2.Reference(name="f")
    assert list(result.arguments) == [L2.Immediate(value=1), L2.Immediate(value=2)]


def test_eliminate_letrec_term_apply_no_args():
    term = Apply(target=Reference(name="f"), arguments=[])
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Apply)
    assert list(result.arguments) == []


def test_eliminate_letrec_term_immediate():
    result = eliminate_letrec_term(Immediate(value=99))
    assert result == L2.Immediate(value=99)


def test_eliminate_letrec_term_primitive():
    term = Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=2))
    result = eliminate_letrec_term(term)
    assert result == L2.Primitive(operator="+", left=L2.Immediate(value=1), right=L2.Immediate(value=2))


def test_eliminate_letrec_term_branch():
    term = Branch(
        operator="<",
        left=Immediate(value=1),
        right=Immediate(value=2),
        consequent=Immediate(value=10),
        otherwise=Immediate(value=20),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Branch)
    assert result.operator == "<"
    assert result.left == L2.Immediate(value=1)
    assert result.right == L2.Immediate(value=2)
    assert result.consequent == L2.Immediate(value=10)
    assert result.otherwise == L2.Immediate(value=20)


def test_eliminate_letrec_term_allocate():
    result = eliminate_letrec_term(Allocate(count=3))
    assert result == L2.Allocate(count=3)


def test_eliminate_letrec_term_load():
    term = Load(base=Reference(name="arr"), index=2)
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Load)
    assert result.base == L2.Reference(name="arr")
    assert result.index == 2


def test_eliminate_letrec_term_store():
    term = Store(base=Reference(name="arr"), index=1, value=Immediate(value=7))
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Store)
    assert result.base == L2.Reference(name="arr")
    assert result.index == 1
    assert result.value == L2.Immediate(value=7)


def test_eliminate_letrec_term_begin():
    term = Begin(effects=[Immediate(value=0), Immediate(value=1)], value=Immediate(value=2))
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Begin)
    assert list(result.effects) == [L2.Immediate(value=0), L2.Immediate(value=1)]
    assert result.value == L2.Immediate(value=2)


def test_eliminate_letrec_term_begin_empty_effects():
    term = Begin(effects=[], value=Immediate(value=5))
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Begin)
    assert list(result.effects) == []


def test_subst_reference_not_in_names():
    term = LetRec(
        bindings=[("f", Immediate(value=1))],
        body=Reference(name="other"),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    begin = result.body
    assert isinstance(begin, L2.Begin)
    assert begin.value == L2.Reference(name="other")


def test_subst_empty_names_via_let_shadowing():
    term = LetRec(
        bindings=[("f", Immediate(value=1))],
        body=Let(bindings=[("f", Immediate(value=2))], body=Reference(name="f")),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    begin = result.body
    assert isinstance(begin, L2.Begin)
    inner_let = begin.value
    assert isinstance(inner_let, L2.Let)
    assert inner_let.body == L2.Reference(name="f")


def test_subst_empty_names_via_abstract_shadowing():
    term = LetRec(
        bindings=[("f", Immediate(value=1))],
        body=Abstract(parameters=["f"], body=Reference(name="f")),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    begin = result.body
    assert isinstance(begin, L2.Begin)
    inner_abstract = begin.value
    assert isinstance(inner_abstract, L2.Abstract)
    assert inner_abstract.body == L2.Reference(name="f")


def test_subst_empty_names_via_inner_letrec_shadowing():
    term = LetRec(
        bindings=[("f", Immediate(value=1))],
        body=LetRec(bindings=[("f", Immediate(value=2))], body=Reference(name="f")),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    outer_begin = result.body
    assert isinstance(outer_begin, L2.Begin)
    inner_let = outer_begin.value
    assert isinstance(inner_let, L2.Let)
    inner_begin = inner_let.body
    assert isinstance(inner_begin, L2.Begin)
    assert isinstance(inner_begin.value, L2.Load)


def test_subst_allocate_in_binding():
    term = LetRec(
        bindings=[("f", Allocate(count=2))],
        body=Reference(name="f"),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    begin = result.body
    assert isinstance(begin, L2.Begin)
    store = begin.effects[0]
    assert isinstance(store, L2.Store)
    assert store.value == L2.Allocate(count=2)


def test_subst_load_in_body():
    term = LetRec(
        bindings=[("f", Immediate(value=1))],
        body=Load(base=Reference(name="f"), index=0),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    begin = result.body
    assert isinstance(begin, L2.Begin)
    body_load = begin.value
    assert isinstance(body_load, L2.Load)
    assert isinstance(body_load.base, L2.Load)
    assert body_load.base.base == L2.Reference(name="f")


def test_subst_store_in_body():
    term = LetRec(
        bindings=[("f", Immediate(value=1))],
        body=Store(base=Reference(name="f"), index=0, value=Reference(name="f")),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    begin = result.body
    assert isinstance(begin, L2.Begin)
    body_store = begin.value
    assert isinstance(body_store, L2.Store)
    assert isinstance(body_store.base, L2.Load)
    assert isinstance(body_store.value, L2.Load)


def test_subst_primitive_in_body():
    term = LetRec(
        bindings=[("f", Immediate(value=1))],
        body=Primitive(operator="+", left=Reference(name="f"), right=Immediate(value=0)),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    begin = result.body
    assert isinstance(begin, L2.Begin)
    prim = begin.value
    assert isinstance(prim, L2.Primitive)
    assert isinstance(prim.left, L2.Load)
    assert prim.right == L2.Immediate(value=0)


def test_subst_branch_in_body():
    term = LetRec(
        bindings=[("f", Immediate(value=0))],
        body=Branch(
            operator="<",
            left=Reference(name="f"),
            right=Immediate(value=10),
            consequent=Reference(name="f"),
            otherwise=Immediate(value=0),
        ),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    begin = result.body
    assert isinstance(begin, L2.Begin)
    branch = begin.value
    assert isinstance(branch, L2.Branch)
    assert isinstance(branch.left, L2.Load)
    assert isinstance(branch.consequent, L2.Load)
    assert branch.right == L2.Immediate(value=10)


def test_subst_begin_in_body():
    term = LetRec(
        bindings=[("f", Immediate(value=1))],
        body=Begin(effects=[Reference(name="f")], value=Reference(name="f")),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    begin = result.body
    assert isinstance(begin, L2.Begin)
    inner_begin = begin.value
    assert isinstance(inner_begin, L2.Begin)
    assert isinstance(inner_begin.effects[0], L2.Load)
    assert isinstance(inner_begin.value, L2.Load)


def test_subst_apply_in_body():
    term = LetRec(
        bindings=[("f", Immediate(value=1))],
        body=Apply(target=Reference(name="f"), arguments=[Reference(name="f"), Immediate(value=0)]),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    begin = result.body
    assert isinstance(begin, L2.Begin)
    apply = begin.value
    assert isinstance(apply, L2.Apply)
    assert isinstance(apply.target, L2.Load)
    assert isinstance(apply.arguments[0], L2.Load)
    assert apply.arguments[1] == L2.Immediate(value=0)


def test_fact_example():
    program = Program(
        parameters=["x"],
        body=LetRec(
            bindings=[
                (
                    "fact",
                    Abstract(
                        parameters=["n"],
                        body=Branch(
                            operator="==",
                            left=Reference(name="n"),
                            right=Immediate(value=0),
                            consequent=Immediate(value=1),
                            otherwise=Primitive(
                                operator="*",
                                left=Reference(name="n"),
                                right=Apply(
                                    target=Reference(name="fact"),
                                    arguments=[
                                        Primitive(operator="-", left=Reference(name="n"), right=Immediate(value=1))
                                    ],
                                ),
                            ),
                        ),
                    ),
                )
            ],
            body=Apply(target=Reference(name="fact"), arguments=[Reference(name="x")]),
        ),
    )
    result = eliminate_letrec_program(program)
    assert isinstance(result, L2.Program)
    assert list(result.parameters) == ["x"]
    assert isinstance(result.body, L2.Let)
    assert result.body.bindings[0] == ("fact", L2.Allocate(count=1))
    begin = result.body.body
    assert isinstance(begin, L2.Begin)
    assert len(begin.effects) == 1
    store = begin.effects[0]
    assert isinstance(store, L2.Store)
    assert store.base == L2.Reference(name="fact")
    assert store.index == 0
    assert isinstance(store.value, L2.Abstract)
    body_apply = begin.value
    assert isinstance(body_apply, L2.Apply)
    assert isinstance(body_apply.target, L2.Load)
    assert body_apply.target.base == L2.Reference(name="fact")
    assert body_apply.arguments[0] == L2.Reference(name="x")


def test_nested_letrec():
    term = LetRec(
        bindings=[("outer", Immediate(value=1))],
        body=LetRec(
            bindings=[("inner", Reference(name="outer"))],
            body=Reference(name="inner"),
        ),
    )
    result = eliminate_letrec_term(term)
    assert isinstance(result, L2.Let)
    outer_begin = result.body
    assert isinstance(outer_begin, L2.Begin)
    inner_let = outer_begin.value
    assert isinstance(inner_let, L2.Let)
    inner_begin = inner_let.body
    assert isinstance(inner_begin, L2.Begin)
    assert isinstance(inner_begin.value, L2.Load)
