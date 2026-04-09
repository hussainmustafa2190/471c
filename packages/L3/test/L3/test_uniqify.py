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
from L3.uniqify import Context, uniqify_program, uniqify_term
from util.sequential_name_generator import SequentialNameGenerator


def make_fresh():
    return SequentialNameGenerator()


# ===========================================================================
# Shipped tests (kept exactly as-is)
# ===========================================================================

def test_uniqify_term_reference():
    term = Reference(name="x")
    context: Context = {"x": "y"}
    fresh = make_fresh()
    actual = uniqify_term(term, context, fresh=fresh)
    expected = Reference(name="y")
    assert actual == expected


def test_uniqify_immediate():
    term = Immediate(value=42)
    context: Context = dict[str, str]()
    fresh = make_fresh()
    actual = uniqify_term(term, context, fresh)
    expected = Immediate(value=42)
    assert actual == expected


def test_uniqify_term_let():
    term = Let(
        bindings=[
            ("x", Immediate(value=1)),
            ("y", Reference(name="x")),
        ],
        body=Apply(
            target=Reference(name="x"),
            arguments=[Reference(name="y")],
        ),
    )
    context: Context = {"x": "y"}
    fresh = make_fresh()
    actual = uniqify_term(term, context, fresh)
    expected = Let(
        bindings=[
            ("x0", Immediate(value=1)),
            ("y0", Reference(name="y")),  # binding value sees outer x→"y"
        ],
        body=Apply(
            target=Reference(name="x0"),
            arguments=[Reference(name="y0")],
        ),
    )
    assert actual == expected


# ===========================================================================
# Immediate / Allocate — leaf nodes returned unchanged
# ===========================================================================

def test_immediate_unchanged():
    term = Immediate(value=0)
    assert uniqify_term(term, {}, make_fresh()) == Immediate(value=0)


def test_allocate_unchanged():
    term = Allocate(count=3)
    assert uniqify_term(term, {}, make_fresh()) == Allocate(count=3)


# ===========================================================================
# Reference
# ===========================================================================

def test_reference_looks_up_context():
    assert uniqify_term(Reference(name="a"), {"a": "a99"}, make_fresh()) == Reference(name="a99")


# ===========================================================================
# Let — scoping rules
# ===========================================================================

def test_let_single_binding_renamed():
    term = Let(bindings=[("a", Immediate(value=5))], body=Reference(name="a"))
    result = uniqify_term(term, {}, make_fresh())
    assert result == Let(bindings=[("a0", Immediate(value=5))], body=Reference(name="a0"))


def test_let_body_sees_new_names():
    term = Let(
        bindings=[("a", Immediate(value=1)), ("b", Immediate(value=2))],
        body=Primitive(operator="+", left=Reference(name="a"), right=Reference(name="b")),
    )
    result = uniqify_term(term, {}, make_fresh())
    assert result == Let(
        bindings=[("a0", Immediate(value=1)), ("b0", Immediate(value=2))],
        body=Primitive(operator="+", left=Reference(name="a0"), right=Reference(name="b0")),
    )


def test_let_binding_value_uses_outer_context():
    # "z" in binding value of "y" is resolved from the outer context,
    # not from the new bindings being created
    term = Let(
        bindings=[("x", Immediate(value=1)), ("y", Reference(name="z"))],
        body=Primitive(operator="+", left=Reference(name="x"), right=Reference(name="y")),
    )
    result = uniqify_term(term, {"z": "z_outer"}, make_fresh())
    assert result == Let(
        bindings=[("x0", Immediate(value=1)), ("y0", Reference(name="z_outer"))],
        body=Primitive(operator="+", left=Reference(name="x0"), right=Reference(name="y0")),
    )


def test_let_shadows_outer_name():
    # Re-binding "x" inside Let gives it a new unique name
    term = Let(bindings=[("x", Immediate(value=99))], body=Reference(name="x"))
    result = uniqify_term(term, {"x": "x_outer"}, make_fresh())
    assert result == Let(bindings=[("x0", Immediate(value=99))], body=Reference(name="x0"))


# ===========================================================================
# LetRec — all binders visible in values AND body
# ===========================================================================

def test_letrec_binder_visible_in_own_value():
    # The bound name "fact" must be visible inside its own binding value (self-recursion)
    term = LetRec(
        bindings=[("fact", Abstract(parameters=["n"], body=Reference(name="fact")))],
        body=Apply(target=Reference(name="fact"), arguments=[Immediate(value=5)]),
    )
    result = uniqify_term(term, {}, make_fresh())
    assert result == LetRec(
        bindings=[("fact0", Abstract(parameters=["n0"], body=Reference(name="fact0")))],
        body=Apply(target=Reference(name="fact0"), arguments=[Immediate(value=5)]),
    )


def test_letrec_mutual_recursion():
    term = LetRec(
        bindings=[
            ("even", Abstract(parameters=["n"], body=Reference(name="odd"))),
            ("odd",  Abstract(parameters=["n"], body=Reference(name="even"))),
        ],
        body=Apply(target=Reference(name="even"), arguments=[Immediate(value=4)]),
    )
    result = uniqify_term(term, {}, make_fresh())
    assert result == LetRec(
        bindings=[
            ("even0", Abstract(parameters=["n0"], body=Reference(name="odd0"))),
            ("odd0",  Abstract(parameters=["n1"], body=Reference(name="even0"))),
        ],
        body=Apply(target=Reference(name="even0"), arguments=[Immediate(value=4)]),
    )


def test_letrec_body_sees_new_names():
    term = LetRec(
        bindings=[("f", Immediate(value=0))],
        body=Reference(name="f"),
    )
    result = uniqify_term(term, {}, make_fresh())
    assert result == LetRec(
        bindings=[("f0", Immediate(value=0))],
        body=Reference(name="f0"),
    )


# ===========================================================================
# Abstract
# ===========================================================================

def test_abstract_parameter_renamed():
    term = Abstract(parameters=["x"], body=Reference(name="x"))
    result = uniqify_term(term, {}, make_fresh())
    assert result == Abstract(parameters=["x0"], body=Reference(name="x0"))


def test_abstract_parameter_shadows_outer():
    term = Abstract(parameters=["x"], body=Reference(name="x"))
    result = uniqify_term(term, {"x": "x_outer"}, make_fresh())
    assert result == Abstract(parameters=["x0"], body=Reference(name="x0"))


def test_abstract_free_variable_from_outer():
    term = Abstract(parameters=["x"], body=Reference(name="y"))
    result = uniqify_term(term, {"y": "y_outer"}, make_fresh())
    assert result == Abstract(parameters=["x0"], body=Reference(name="y_outer"))


def test_abstract_multiple_parameters():
    term = Abstract(
        parameters=["a", "b"],
        body=Primitive(operator="+", left=Reference(name="a"), right=Reference(name="b")),
    )
    result = uniqify_term(term, {}, make_fresh())
    assert result == Abstract(
        parameters=["a0", "b0"],
        body=Primitive(operator="+", left=Reference(name="a0"), right=Reference(name="b0")),
    )


# ===========================================================================
# Apply
# ===========================================================================

def test_apply_renames_target_and_arguments():
    term = Apply(
        target=Reference(name="f"),
        arguments=[Reference(name="x"), Reference(name="y")],
    )
    result = uniqify_term(term, {"f": "f0", "x": "x0", "y": "y0"}, make_fresh())
    assert result == Apply(
        target=Reference(name="f0"),
        arguments=[Reference(name="x0"), Reference(name="y0")],
    )


def test_apply_no_arguments():
    term = Apply(target=Reference(name="f"), arguments=[])
    result = uniqify_term(term, {"f": "f0"}, make_fresh())
    assert result == Apply(target=Reference(name="f0"), arguments=[])


# ===========================================================================
# Primitive
# ===========================================================================

def test_primitive_renames_operands():
    term = Primitive(operator="*", left=Reference(name="a"), right=Reference(name="b"))
    result = uniqify_term(term, {"a": "a0", "b": "b0"}, make_fresh())
    assert result == Primitive(operator="*", left=Reference(name="a0"), right=Reference(name="b0"))


def test_primitive_immediate_operands_unchanged():
    term = Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=2))
    result = uniqify_term(term, {}, make_fresh())
    assert result == term


def test_primitive_sub_operator():
    term = Primitive(operator="-", left=Reference(name="x"), right=Immediate(value=1))
    result = uniqify_term(term, {"x": "x0"}, make_fresh())
    assert result == Primitive(operator="-", left=Reference(name="x0"), right=Immediate(value=1))


# ===========================================================================
# Branch
# ===========================================================================

def test_branch_lt_all_parts_renamed():
    term = Branch(
        operator="<",
        left=Reference(name="a"),
        right=Reference(name="b"),
        consequent=Reference(name="c"),
        otherwise=Reference(name="d"),
    )
    result = uniqify_term(term, {"a": "a0", "b": "b0", "c": "c0", "d": "d0"}, make_fresh())
    assert result == Branch(
        operator="<",
        left=Reference(name="a0"),
        right=Reference(name="b0"),
        consequent=Reference(name="c0"),
        otherwise=Reference(name="d0"),
    )


def test_branch_eq_operator():
    term = Branch(
        operator="==",
        left=Immediate(value=0),
        right=Immediate(value=0),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=2),
    )
    result = uniqify_term(term, {}, make_fresh())
    assert result == term


# ===========================================================================
# Load
# ===========================================================================

def test_load_base_renamed():
    term = Load(base=Reference(name="x"), index=0)
    result = uniqify_term(term, {"x": "x0"}, make_fresh())
    assert result == Load(base=Reference(name="x0"), index=0)


def test_load_index_preserved():
    term = Load(base=Reference(name="x"), index=5)
    result = uniqify_term(term, {"x": "x0"}, make_fresh())
    assert result == Load(base=Reference(name="x0"), index=5)


# ===========================================================================
# Store
# ===========================================================================

def test_store_base_and_value_renamed():
    term = Store(base=Reference(name="x"), index=0, value=Reference(name="y"))
    result = uniqify_term(term, {"x": "x0", "y": "y0"}, make_fresh())
    assert result == Store(base=Reference(name="x0"), index=0, value=Reference(name="y0"))


# ===========================================================================
# Begin
# ===========================================================================

def test_begin_effects_and_value_renamed():
    term = Begin(
        effects=[Reference(name="a"), Reference(name="b")],
        value=Reference(name="c"),
    )
    result = uniqify_term(term, {"a": "a0", "b": "b0", "c": "c0"}, make_fresh())
    assert result == Begin(
        effects=[Reference(name="a0"), Reference(name="b0")],
        value=Reference(name="c0"),
    )


def test_begin_no_effects():
    term = Begin(effects=[], value=Reference(name="x"))
    result = uniqify_term(term, {"x": "x0"}, make_fresh())
    assert result == Begin(effects=[], value=Reference(name="x0"))


# ===========================================================================
# uniqify_program
# ===========================================================================

def test_program_parameter_renamed():
    program = Program(parameters=["x"], body=Reference(name="x"))
    _, result = uniqify_program(program)
    new_name = result.parameters[0]
    assert new_name != "x"
    assert result.body == Reference(name=new_name)


def test_program_returns_fresh_callable():
    program = Program(parameters=[], body=Immediate(value=0))
    fresh, _ = uniqify_program(program)
    assert fresh("t") == "t0"


def test_program_multiple_parameters():
    program = Program(
        parameters=["a", "b"],
        body=Primitive(operator="+", left=Reference(name="a"), right=Reference(name="b")),
    )
    _, result = uniqify_program(program)
    a_new, b_new = result.parameters
    assert a_new != "a" and b_new != "b" and a_new != b_new
    assert result.body == Primitive(
        operator="+",
        left=Reference(name=a_new),
        right=Reference(name=b_new),
    )


def test_program_body_uses_renamed_parameters():
    program = Program(
        parameters=["n"],
        body=Let(
            bindings=[("m", Reference(name="n"))],
            body=Reference(name="m"),
        ),
    )
    _, result = uniqify_program(program)
    n_new = result.parameters[0]
    assert result.body == Let(
        bindings=[("m0", Reference(name=n_new))],
        body=Reference(name="m0"),
    )


def test_all_names_globally_unique():
    # Two nested Lets both binding "x" — must produce two different unique names
    program = Program(
        parameters=[],
        body=Let(
            bindings=[("x", Immediate(value=1))],
            body=Let(
                bindings=[("x", Immediate(value=2))],
                body=Primitive(operator="+", left=Reference(name="x"), right=Reference(name="x")),
            ),
        ),
    )
    _, result = uniqify_program(program)
    outer_let = result.body
    assert isinstance(outer_let, Let)
    x_outer = outer_let.bindings[0][0]
    inner_let = outer_let.body
    assert isinstance(inner_let, Let)
    x_inner = inner_let.bindings[0][0]
    assert x_outer != x_inner
    assert inner_let.body == Primitive(
        operator="+",
        left=Reference(name=x_inner),
        right=Reference(name=x_inner),
    )


def test_program_letrec_factorial():
    # Full factorial program matching the L3 example
    program = Program(
        parameters=["x"],
        body=LetRec(
            bindings=[
                ("fact", Abstract(
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
                ))
            ],
            body=Apply(target=Reference(name="fact"), arguments=[Reference(name="x")]),
        ),
    )
    _, result = uniqify_program(program)

    x_new = result.parameters[0]
    letrec = result.body
    assert isinstance(letrec, LetRec)
    fact_new, abstract = letrec.bindings[0]
    assert isinstance(abstract, Abstract)
    n_new = abstract.parameters[0]

    # All three names are distinct
    assert len({x_new, fact_new, n_new}) == 3

    # Self-reference inside the function body uses fact_new
    branch = abstract.body
    assert isinstance(branch, Branch)
    otherwise = branch.otherwise
    assert isinstance(otherwise, Primitive)
    apply = otherwise.right
    assert isinstance(apply, Apply)
    assert apply.target == Reference(name=fact_new)

    # Call in the letrec body uses fact_new and x_new
    body_apply = letrec.body
    assert isinstance(body_apply, Apply)
    assert body_apply.target == Reference(name=fact_new)
    assert body_apply.arguments[0] == Reference(name=x_new)