import pytest
from L3.parse import parse_program, parse_term
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

# ── parse_program ─────────────────────────────────────────────────────────────


def test_parse_program_with_parameters():
    result = parse_program("(l3 (m n) (+ m n))")
    assert result == Program(
        parameters=["m", "n"],
        body=Primitive(operator="+", left=Reference(name="m"), right=Reference(name="n")),
    )


def test_parse_program_no_parameters():
    # Covers the empty branch of the parameters list comprehension.
    result = parse_program("(l3 () 0)")
    assert result == Program(parameters=[], body=Immediate(value=0))


# ── reference ────────────────────────────────────────────────────────────────


def test_parse_reference():
    assert parse_term("x") == Reference(name="x")


# ── immediate ────────────────────────────────────────────────────────────────


def test_parse_immediate_positive():
    assert parse_term("42") == Immediate(value=42)


def test_parse_immediate_zero():
    assert parse_term("0") == Immediate(value=0)


def test_parse_immediate_negative():
    assert parse_term("-7") == Immediate(value=-7)


# ── let ───────────────────────────────────────────────────────────────────────


def test_parse_let_with_bindings():
    result = parse_term("(let ((x 1) (y 2)) x)")
    assert result == Let(
        bindings=[("x", Immediate(value=1)), ("y", Immediate(value=2))],
        body=Reference(name="x"),
    )


def test_parse_let_empty_bindings():
    # Covers the empty bindings list branch.
    result = parse_term("(let () 0)")
    assert result == Let(bindings=[], body=Immediate(value=0))


# ── letrec ────────────────────────────────────────────────────────────────────


def test_parse_letrec_with_binding():
    result = parse_term("(letrec ((f (\\ (n) n))) (f 0))")
    assert result == LetRec(
        bindings=[("f", Abstract(parameters=["n"], body=Reference(name="n")))],
        body=Apply(target=Reference(name="f"), arguments=[Immediate(value=0)]),
    )


def test_parse_letrec_empty_bindings():
    result = parse_term("(letrec () 0)")
    assert result == LetRec(bindings=[], body=Immediate(value=0))


# ── abstract ──────────────────────────────────────────────────────────────────


def test_parse_abstract_backslash():
    result = parse_term("(\\ (x y) (+ x y))")
    assert result == Abstract(
        parameters=["x", "y"],
        body=Primitive(operator="+", left=Reference(name="x"), right=Reference(name="y")),
    )


def test_parse_abstract_lambda_keyword():
    result = parse_term("(lambda (x) x)")
    assert result == Abstract(parameters=["x"], body=Reference(name="x"))


def test_parse_abstract_no_parameters():
    # Covers the empty branch of the parameters list comprehension.
    result = parse_term("(\\ () 0)")
    assert result == Abstract(parameters=[], body=Immediate(value=0))


# ── apply ─────────────────────────────────────────────────────────────────────


def test_parse_apply_with_arguments():
    # Covers non-empty arguments: children[1:] is non-empty.
    result = parse_term("(f x y)")
    assert result == Apply(
        target=Reference(name="f"),
        arguments=[Reference(name="x"), Reference(name="y")],
    )


def test_parse_apply_no_arguments():
    # Covers empty arguments: children[1:] == [].
    result = parse_term("(loop)")
    assert result == Apply(target=Reference(name="loop"), arguments=[])


# ── primitive ─────────────────────────────────────────────────────────────────


def test_parse_primitive_add():
    assert parse_term("(+ 1 2)") == Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=2))


def test_parse_primitive_sub():
    assert parse_term("(- n 1)") == Primitive(operator="-", left=Reference(name="n"), right=Immediate(value=1))


def test_parse_primitive_mul():
    assert parse_term("(* n n)") == Primitive(operator="*", left=Reference(name="n"), right=Reference(name="n"))


# ── branch ────────────────────────────────────────────────────────────────────


def test_parse_branch_less_than():
    result = parse_term("(if (< n 2) n 0)")
    assert result == Branch(
        operator="<",
        left=Reference(name="n"),
        right=Immediate(value=2),
        consequent=Reference(name="n"),
        otherwise=Immediate(value=0),
    )


def test_parse_branch_equal():
    result = parse_term("(if (== n 0) 1 n)")
    assert result == Branch(
        operator="==",
        left=Reference(name="n"),
        right=Immediate(value=0),
        consequent=Immediate(value=1),
        otherwise=Reference(name="n"),
    )


# ── allocate ──────────────────────────────────────────────────────────────────


def test_parse_allocate():
    assert parse_term("(allocate 1)") == Allocate(count=1)


# ── load ──────────────────────────────────────────────────────────────────────


def test_parse_load():
    assert parse_term("(load i 0)") == Load(base=Reference(name="i"), index=0)


# ── store ─────────────────────────────────────────────────────────────────────


def test_parse_store():
    assert parse_term("(store i 0 42)") == Store(base=Reference(name="i"), index=0, value=Immediate(value=42))


# ── begin ─────────────────────────────────────────────────────────────────────


def test_parse_begin_with_effects():
    # Covers non-empty effects: children[:-1] is non-empty.
    result = parse_term("(begin (store i 0 0) (store acc 0 0) acc)")
    assert result == Begin(
        effects=[
            Store(base=Reference(name="i"), index=0, value=Immediate(value=0)),
            Store(base=Reference(name="acc"), index=0, value=Immediate(value=0)),
        ],
        value=Reference(name="acc"),
    )


def test_parse_begin_single_term():
    # Covers empty effects: children[:-1] == [].
    result = parse_term("(begin 0)")
    assert result == Begin(effects=[], value=Immediate(value=0))


# ── comments ──────────────────────────────────────────────────────────────────


def test_parse_ignores_comments():
    result = parse_term("(+ 1 2) ; this is a comment")
    assert result == Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=2))


# ── integration ───────────────────────────────────────────────────────────────


def test_parse_program_fact():
    src = """
    (l3 (x)
      (letrec
        ((fact
           (\\ (n)
             (if
                (== n 0)
                1
                (* n (fact (- n 1)))))))
        (fact x)))
    """
    result = parse_program(src)
    assert result == Program(
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
                                        Primitive(
                                            operator="-",
                                            left=Reference(name="n"),
                                            right=Immediate(value=1),
                                        )
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


def test_parse_program_sum():
    src = """
    (l3 (n)
      (let ((i   (allocate 1))
            (acc (allocate 1)))
        (begin
          (store i 0 0)
          (store acc 0 0)
          (letrec
            ((loop
              (\\ ()
                (if
                  (< (load i 0) (+ n 1))
                  (begin
                    (store acc 0 (+ (load acc 0) (load i 0)))
                    (store i 0 (+ (load i 0) 1))
                    (loop))
                  (load acc 0)))))
            (loop)))))
    """
    result = parse_program(src)
    assert isinstance(result, Program)
    assert result.parameters == ["n"]
    assert isinstance(result.body, Let)
    assert len(result.body.bindings) == 2
    assert result.body.bindings[0][0] == "i"
    assert result.body.bindings[1][0] == "acc"


# ── syntax errors ─────────────────────────────────────────────────────────────


def test_parse_term_syntax_error():
    with pytest.raises(Exception):
        parse_term("(let")


def test_parse_program_syntax_error():
    with pytest.raises(Exception):
        parse_program("(l2 (x) x)")
