from __future__ import annotations

from util.sequential_name_generator import SequentialNameGenerator

from L3.desugar import desugar_program, desugar_term
from L3.syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Car,
    Cdr,
    Cons,
    Immediate,
    IsNil,
    Let,
    LetRec,
    ListLiteral,
    Load,
    Nil,
    Primitive,
    Program,
    Reference,
    Store,
    Tuple,
    TupleRef,
)


def _fresh() -> SequentialNameGenerator:
    return SequentialNameGenerator()


def test_nil_desugars_to_immediate_zero() -> None:
    assert desugar_term(Nil(), _fresh()) == Immediate(value=0)


def test_cons_desugars_to_let_allocate_begin_two_stores() -> None:
    gen = _fresh()
    out = desugar_term(Cons(head=Immediate(value=1), tail=Immediate(value=2)), gen)
    c0 = "c0"
    assert out == Let(
        bindings=[(c0, Allocate(count=2))],
        body=Begin(
            effects=[
                Store(base=Reference(name=c0), index=0, value=Immediate(value=1)),
                Store(base=Reference(name=c0), index=1, value=Immediate(value=2)),
            ],
            value=Reference(name=c0),
        ),
    )


def test_car_desugars_to_load_index_zero() -> None:
    assert desugar_term(Car(base=Reference(name="x")), _fresh()) == Load(
        base=Reference(name="x"),
        index=0,
    )


def test_cdr_desugars_to_load_index_one() -> None:
    assert desugar_term(Cdr(base=Reference(name="x")), _fresh()) == Load(
        base=Reference(name="x"),
        index=1,
    )


def test_is_nil_desugars_to_branch_equals() -> None:
    assert desugar_term(IsNil(base=Reference(name="b")), _fresh()) == Branch(
        operator="==",
        left=Reference(name="b"),
        right=Immediate(value=0),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )


def test_list_literal_empty_desugars_to_immediate_zero() -> None:
    assert desugar_term(ListLiteral(elements=[]), _fresh()) == Immediate(value=0)


def test_list_literal_single_desugars_via_cons_nil() -> None:
    gen = _fresh()
    out = desugar_term(ListLiteral(elements=[Immediate(value=7)]), gen)
    c0 = "c0"
    assert out == Let(
        bindings=[(c0, Allocate(count=2))],
        body=Begin(
            effects=[
                Store(base=Reference(name=c0), index=0, value=Immediate(value=7)),
                Store(base=Reference(name=c0), index=1, value=Immediate(value=0)),
            ],
            value=Reference(name=c0),
        ),
    )


def test_list_literal_three_elements_nested_cons() -> None:
    gen = _fresh()
    out = desugar_term(
        ListLiteral(elements=[Immediate(value=i) for i in (1, 2, 3)]),
        gen,
    )
    c0, c1, c2 = "c0", "c1", "c2"
    assert out == Let(
        bindings=[(c0, Allocate(count=2))],
        body=Begin(
            effects=[
                Store(base=Reference(name=c0), index=0, value=Immediate(value=1)),
                Store(
                    base=Reference(name=c0),
                    index=1,
                    value=Let(
                        bindings=[(c1, Allocate(count=2))],
                        body=Begin(
                            effects=[
                                Store(base=Reference(name=c1), index=0, value=Immediate(value=2)),
                                Store(
                                    base=Reference(name=c1),
                                    index=1,
                                    value=Let(
                                        bindings=[(c2, Allocate(count=2))],
                                        body=Begin(
                                            effects=[
                                                Store(
                                                    base=Reference(name=c2),
                                                    index=0,
                                                    value=Immediate(value=3),
                                                ),
                                                Store(
                                                    base=Reference(name=c2),
                                                    index=1,
                                                    value=Immediate(value=0),
                                                ),
                                            ],
                                            value=Reference(name=c2),
                                        ),
                                    ),
                                ),
                            ],
                            value=Reference(name=c1),
                        ),
                    ),
                ),
            ],
            value=Reference(name=c0),
        ),
    )


def test_tuple_empty_allocate_zero_no_stores() -> None:
    gen = _fresh()
    out = desugar_term(Tuple(elements=[]), gen)
    assert out == Let(
        bindings=[("t0", Allocate(count=0))],
        body=Begin(effects=[], value=Reference(name="t0")),
    )


def test_tuple_two_elements_two_stores() -> None:
    gen = _fresh()
    out = desugar_term(Tuple(elements=[Immediate(value=0), Immediate(value=1)]), gen)
    assert out == Let(
        bindings=[("t0", Allocate(count=2))],
        body=Begin(
            effects=[
                Store(base=Reference(name="t0"), index=0, value=Immediate(value=0)),
                Store(base=Reference(name="t0"), index=1, value=Immediate(value=1)),
            ],
            value=Reference(name="t0"),
        ),
    )


def test_tuple_ref_load_index_zero() -> None:
    assert desugar_term(TupleRef(base=Reference(name="b"), index=0), _fresh()) == Load(
        base=Reference(name="b"),
        index=0,
    )


def test_tuple_ref_load_index_two() -> None:
    assert desugar_term(TupleRef(base=Reference(name="b"), index=2), _fresh()) == Load(
        base=Reference(name="b"),
        index=2,
    )


def test_existing_nodes_recurse() -> None:
    gen = _fresh()
    inner = Tuple(elements=[])
    body = Let(
        bindings=[("x", inner)],
        body=Reference(name="x"),
    )
    out = desugar_term(body, gen)
    assert out == Let(
        bindings=[
            (
                "x",
                Let(
                    bindings=[("t0", Allocate(count=0))],
                    body=Begin(effects=[], value=Reference(name="t0")),
                ),
            )
        ],
        body=Reference(name="x"),
    )

    ref = Reference(name="p")
    assert desugar_term(ref, gen) == ref
    assert desugar_term(Immediate(value=9), gen) == Immediate(value=9)
    assert desugar_term(Allocate(count=3), gen) == Allocate(count=3)

    lr = LetRec(
        bindings=[("f", Abstract(parameters=[], body=Immediate(value=0)))],
        body=Apply(target=Reference(name="f"), arguments=[]),
    )
    assert desugar_term(lr, gen) == lr

    ab = Abstract(parameters=["a"], body=Immediate(value=1))
    assert desugar_term(ab, gen) == Abstract(parameters=["a"], body=Immediate(value=1))

    ap = Apply(target=Reference(name="g"), arguments=[Immediate(value=2)])
    assert desugar_term(ap, gen) == Apply(
        target=Reference(name="g"),
        arguments=[Immediate(value=2)],
    )

    pr = Primitive(operator="+", left=Reference(name="a"), right=Reference(name="b"))
    assert desugar_term(pr, gen) == pr

    br = Branch(
        operator="<",
        left=Reference(name="a"),
        right=Reference(name="b"),
        consequent=Immediate(value=0),
        otherwise=Immediate(value=1),
    )
    assert desugar_term(br, gen) == br

    ld = Load(base=Reference(name="m"), index=1)
    assert desugar_term(ld, gen) == ld

    st = Store(base=Reference(name="m"), index=0, value=Immediate(value=3))
    assert desugar_term(st, gen) == st

    bg = Begin(effects=[Immediate(value=0)], value=Reference(name="x"))
    assert desugar_term(bg, gen) == bg


def test_nested_cons_car_nil() -> None:
    gen = _fresh()
    out = desugar_term(Cons(head=Car(base=Reference(name="x")), tail=Nil()), gen)
    c0 = "c0"
    assert out == Let(
        bindings=[(c0, Allocate(count=2))],
        body=Begin(
            effects=[
                Store(
                    base=Reference(name=c0),
                    index=0,
                    value=Load(base=Reference(name="x"), index=0),
                ),
                Store(base=Reference(name=c0), index=1, value=Immediate(value=0)),
            ],
            value=Reference(name=c0),
        ),
    )


def test_desugar_program_preserves_parameters() -> None:
    p = Program(parameters=["a", "b"], body=Immediate(value=0))
    out = desugar_program(p)
    assert out.parameters == p.parameters
    assert out.body == Immediate(value=0)


def test_branch_arms_desugar_sugar() -> None:
    gen = _fresh()
    term = Branch(
        operator="==",
        left=Immediate(value=0),
        right=Immediate(value=0),
        consequent=Nil(),
        otherwise=Tuple(elements=[]),
    )
    out = desugar_term(term, gen)
    assert out.consequent == Immediate(value=0)
    assert out.otherwise.tag == "let"


def test_abstract_body_desugars_sugar() -> None:
    gen = _fresh()
    term = Abstract(parameters=["x"], body=ListLiteral(elements=[]))
    out = desugar_term(term, gen)
    assert out == Abstract(parameters=["x"], body=Immediate(value=0))


def test_tuple_ref_desugars_base_expression() -> None:
    gen = _fresh()
    out = desugar_term(TupleRef(base=Tuple(elements=[Immediate(value=5)]), index=0), gen)
    assert out == Load(
        base=Let(
            bindings=[("t0", Allocate(count=1))],
            body=Begin(
                effects=[Store(base=Reference(name="t0"), index=0, value=Immediate(value=5))],
                value=Reference(name="t0"),
            ),
        ),
        index=0,
    )


def test_list_literal_two_elements_uses_list_tail_not_nil_only() -> None:
    gen = _fresh()
    out = desugar_term(ListLiteral(elements=[Immediate(value=1), Immediate(value=2)]), gen)
    assert out.tag == "let"
    assert out.body.effects[1].value.tag == "let"
