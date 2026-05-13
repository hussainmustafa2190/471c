from __future__ import annotations

from util.sequential_name_generator import SequentialNameGenerator

from L3.desugar import desugar_program, desugar_term
from L3.syntax import (
    Abstract,
    Allocate,
    And,
    Apply,
    Begin,
    BoolLiteral,
    BoolPattern,
    Branch,
    Car,
    Cdr,
    Cond,
    Cons,
    ConsPattern,
    Div,
    GreaterThan,
    GreaterThanOrEqual,
    Immediate,
    IntPattern,
    IsNil,
    LessThan,
    Let,
    LetRec,
    LessThanOrEqual,
    ListLiteral,
    Load,
    Match,
    Mod,
    NamePattern,
    Nil,
    NilPattern,
    Not,
    NotEqual,
    Or,
    Primitive,
    Program,
    Reference,
    Store,
    Tuple,
    TuplePattern,
    TupleRef,
    WildcardPattern,
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


def test_bool_literal_true_desugars_to_immediate_one() -> None:
    assert desugar_term(BoolLiteral(value=True), _fresh()) == Immediate(value=1)


def test_bool_literal_false_desugars_to_immediate_zero() -> None:
    assert desugar_term(BoolLiteral(value=False), _fresh()) == Immediate(value=0)


def test_not_zero_desugars_to_branch_equals_zero() -> None:
    assert desugar_term(Not(operand=Immediate(value=0)), _fresh()) == Branch(
        operator="==",
        left=Immediate(value=0),
        right=Immediate(value=0),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )


def test_not_one_desugars_to_branch_equals_zero() -> None:
    assert desugar_term(Not(operand=Immediate(value=1)), _fresh()) == Branch(
        operator="==",
        left=Immediate(value=1),
        right=Immediate(value=0),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )


def test_and_short_circuit_desugar() -> None:
    assert desugar_term(
        And(left=Reference(name="a"), right=Reference(name="b")),
        _fresh(),
    ) == Branch(
        operator="!=",
        left=Reference(name="a"),
        right=Immediate(value=0),
        consequent=Branch(
            operator="!=",
            left=Reference(name="b"),
            right=Immediate(value=0),
            consequent=Immediate(value=1),
            otherwise=Immediate(value=0),
        ),
        otherwise=Immediate(value=0),
    )


def test_or_short_circuit_desugar() -> None:
    assert desugar_term(
        Or(left=Reference(name="a"), right=Reference(name="b")),
        _fresh(),
    ) == Branch(
        operator="!=",
        left=Reference(name="a"),
        right=Immediate(value=0),
        consequent=Immediate(value=1),
        otherwise=Branch(
            operator="!=",
            left=Reference(name="b"),
            right=Immediate(value=0),
            consequent=Immediate(value=1),
            otherwise=Immediate(value=0),
        ),
    )


def test_cond_one_clause_and_else() -> None:
    assert desugar_term(
        Cond(
            clauses=[
                (Reference(name="x"), Immediate(value=1)),
                (None, Immediate(value=0)),
            ],
        ),
        _fresh(),
    ) == Branch(
        operator="!=",
        left=Reference(name="x"),
        right=Immediate(value=0),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )


def test_cond_multiple_clauses_and_else() -> None:
    assert desugar_term(
        Cond(
            clauses=[
                (Reference(name="x"), Immediate(value=1)),
                (Reference(name="y"), Immediate(value=2)),
                (None, Immediate(value=3)),
            ],
        ),
        _fresh(),
    ) == Branch(
        operator="!=",
        left=Reference(name="x"),
        right=Immediate(value=0),
        consequent=Immediate(value=1),
        otherwise=Branch(
            operator="!=",
            left=Reference(name="y"),
            right=Immediate(value=0),
            consequent=Immediate(value=2),
            otherwise=Immediate(value=3),
        ),
    )


def test_cond_no_else_fallback_zero() -> None:
    assert desugar_term(
        Cond(clauses=[(Reference(name="x"), Immediate(value=1))]),
        _fresh(),
    ) == Branch(
        operator="!=",
        left=Reference(name="x"),
        right=Immediate(value=0),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )


def test_cond_empty_clauses_desugar_to_zero() -> None:
    assert desugar_term(Cond(clauses=[]), _fresh()) == Immediate(value=0)


def test_cond_else_only_clause() -> None:
    assert desugar_term(Cond(clauses=[(None, Immediate(value=42))]), _fresh()) == Immediate(value=42)


def test_div_desugars_to_primitive_div() -> None:
    assert desugar_term(
        Div(left=Reference(name="a"), right=Reference(name="b")),
        _fresh(),
    ) == Primitive(operator="/", left=Reference(name="a"), right=Reference(name="b"))


def test_mod_desugars_to_primitive_mod() -> None:
    assert desugar_term(
        Mod(left=Reference(name="a"), right=Reference(name="b")),
        _fresh(),
    ) == Primitive(operator="%", left=Reference(name="a"), right=Reference(name="b"))


def test_greater_than_desugar() -> None:
    assert desugar_term(
        GreaterThan(left=Reference(name="a"), right=Reference(name="b")),
        _fresh(),
    ) == Branch(
        operator="<",
        left=Reference(name="b"),
        right=Reference(name="a"),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )


def test_greater_than_or_equal_desugar() -> None:
    assert desugar_term(
        GreaterThanOrEqual(left=Reference(name="a"), right=Reference(name="b")),
        _fresh(),
    ) == Branch(
        operator="<",
        left=Reference(name="a"),
        right=Reference(name="b"),
        consequent=Immediate(value=0),
        otherwise=Immediate(value=1),
    )


def test_less_than_or_equal_desugar() -> None:
    assert desugar_term(
        LessThanOrEqual(left=Reference(name="a"), right=Reference(name="b")),
        _fresh(),
    ) == Branch(
        operator="<",
        left=Reference(name="b"),
        right=Reference(name="a"),
        consequent=Immediate(value=0),
        otherwise=Immediate(value=1),
    )


def test_less_than_desugars_to_branch_lt() -> None:
    assert desugar_term(
        LessThan(left=Reference(name="a"), right=Reference(name="b")),
        _fresh(),
    ) == Branch(
        operator="<",
        left=Reference(name="a"),
        right=Reference(name="b"),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )


def test_not_equal_desugar() -> None:
    assert desugar_term(
        NotEqual(left=Reference(name="a"), right=Reference(name="b")),
        _fresh(),
    ) == Branch(
        operator="==",
        left=Reference(name="a"),
        right=Reference(name="b"),
        consequent=Immediate(value=0),
        otherwise=Immediate(value=1),
    )


def test_match_int_pattern_binds_scrutinee() -> None:
    gen = _fresh()
    out = desugar_term(
        Match(
            scrutinee=Immediate(value=5),
            clauses=[(IntPattern(value=7), Immediate(value=1))],
        ),
        gen,
    )
    assert out == Let(
        bindings=[("s0", Immediate(value=5))],
        body=Branch(
            operator="==",
            left=Reference(name="s0"),
            right=Immediate(value=7),
            consequent=Immediate(value=1),
            otherwise=Immediate(value=0),
        ),
    )


def test_match_bool_pattern_true() -> None:
    gen = _fresh()
    out = desugar_term(
        Match(
            scrutinee=Reference(name="x"),
            clauses=[(BoolPattern(value=True), Immediate(value=1))],
        ),
        gen,
    )
    assert out == Let(
        bindings=[("s0", Reference(name="x"))],
        body=Branch(
            operator="!=",
            left=Reference(name="s0"),
            right=Immediate(value=0),
            consequent=Immediate(value=1),
            otherwise=Immediate(value=0),
        ),
    )


def test_match_bool_pattern_false() -> None:
    gen = _fresh()
    out = desugar_term(
        Match(
            scrutinee=Reference(name="x"),
            clauses=[(BoolPattern(value=False), Immediate(value=0))],
        ),
        gen,
    )
    assert out == Let(
        bindings=[("s0", Reference(name="x"))],
        body=Branch(
            operator="==",
            left=Reference(name="s0"),
            right=Immediate(value=0),
            consequent=Immediate(value=0),
            otherwise=Immediate(value=0),
        ),
    )


def test_match_nil_pattern() -> None:
    gen = _fresh()
    out = desugar_term(
        Match(
            scrutinee=Reference(name="x"),
            clauses=[(NilPattern(), Immediate(value=0))],
        ),
        gen,
    )
    assert out == Let(
        bindings=[("s0", Reference(name="x"))],
        body=Branch(
            operator="==",
            left=Reference(name="s0"),
            right=Immediate(value=0),
            consequent=Immediate(value=0),
            otherwise=Immediate(value=0),
        ),
    )


def test_match_cons_pattern() -> None:
    gen = _fresh()
    out = desugar_term(
        Match(
            scrutinee=Reference(name="x"),
            clauses=[(ConsPattern(head="h", tail="t"), Reference(name="h"))],
        ),
        gen,
    )
    assert out == Let(
        bindings=[("s0", Reference(name="x"))],
        body=Branch(
            operator="!=",
            left=Reference(name="s0"),
            right=Immediate(value=0),
            consequent=Let(
                bindings=[
                    ("h", Load(base=Reference(name="s0"), index=0)),
                    ("t", Load(base=Reference(name="s0"), index=1)),
                ],
                body=Reference(name="h"),
            ),
            otherwise=Immediate(value=0),
        ),
    )


def test_match_tuple_pattern() -> None:
    gen = _fresh()
    out = desugar_term(
        Match(
            scrutinee=Reference(name="x"),
            clauses=[(TuplePattern(elements=["a", "b"]), Reference(name="a"))],
        ),
        gen,
    )
    assert out == Let(
        bindings=[("s0", Reference(name="x"))],
        body=Let(
            bindings=[
                ("a", Load(base=Reference(name="s0"), index=0)),
                ("b", Load(base=Reference(name="s0"), index=1)),
            ],
            body=Reference(name="a"),
        ),
    )


def test_match_wildcard_pattern() -> None:
    gen = _fresh()
    out = desugar_term(
        Match(
            scrutinee=Reference(name="x"),
            clauses=[(WildcardPattern(), Immediate(value=42))],
        ),
        gen,
    )
    assert out == Let(
        bindings=[("s0", Reference(name="x"))],
        body=Immediate(value=42),
    )


def test_match_name_pattern() -> None:
    gen = _fresh()
    out = desugar_term(
        Match(
            scrutinee=Reference(name="x"),
            clauses=[(NamePattern(name="n"), Reference(name="n"))],
        ),
        gen,
    )
    assert out == Let(
        bindings=[("s0", Reference(name="x"))],
        body=Let(
            bindings=[("n", Reference(name="s0"))],
            body=Reference(name="n"),
        ),
    )


def test_match_empty_clauses() -> None:
    assert desugar_term(Match(scrutinee=Immediate(value=1), clauses=[]), _fresh()) == Immediate(value=0)


def test_match_multiple_clauses_chain() -> None:
    gen = _fresh()
    out = desugar_term(
        Match(
            scrutinee=Reference(name="x"),
            clauses=[
                (IntPattern(value=1), Immediate(value=10)),
                (WildcardPattern(), Immediate(value=20)),
            ],
        ),
        gen,
    )
    assert out == Let(
        bindings=[("s0", Reference(name="x"))],
        body=Branch(
            operator="==",
            left=Reference(name="s0"),
            right=Immediate(value=1),
            consequent=Immediate(value=10),
            otherwise=Immediate(value=20),
        ),
    )
