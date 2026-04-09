from L1 import syntax as L1
from L2 import syntax as L2
from L2.cps_convert import cps_convert_program, cps_convert_term, cps_convert_terms
from util.sequential_name_generator import SequentialNameGenerator


def k(v: L1.Identifier) -> L1.Statement:
    return L1.Halt(value=v)


def make_fresh():
    return SequentialNameGenerator()


# ===========================================================================
# Shipped tests — kept exactly as-is
# ===========================================================================

def test_cps_convert_term_name():
    term = L2.Reference(name="x")
    fresh = make_fresh()
    actual = cps_convert_term(term, k, fresh)
    expected = L1.Halt(value="x")
    assert actual == expected


def test_cps_convert_term_immediate():
    term = L2.Immediate(value=42)
    fresh = make_fresh()
    actual = cps_convert_term(term, k, fresh)
    expected = L1.Immediate(destination="t0", value=42, then=L1.Halt(value="t0"))
    assert actual == expected


def test_cps_convert_term_primitive():
    term = L2.Primitive(operator="+", left=L2.Reference(name="x"), right=L2.Reference(name="y"))
    fresh = make_fresh()
    actual = cps_convert_term(term, k, fresh)
    expected = L1.Primitive(
        destination="t0", operator="+", left="x", right="y", then=L1.Halt(value="t0"),
    )
    assert actual == expected


def test_cps_convert_term_let():
    term = L2.Let(
        bindings=[("a", L2.Reference(name="x")), ("b", L2.Reference(name="y"))],
        body=L2.Reference(name="b"),
    )
    fresh = make_fresh()
    actual = cps_convert_term(term, k, fresh)
    expected = L1.Copy(
        destination="a", source="x",
        then=L1.Copy(destination="b", source="y", then=L1.Halt(value="b")),
    )
    assert actual == expected


def test_cps_convert_term_abstract():
    term = L2.Abstract(parameters=["x"], body=L2.Reference(name="x"))
    fresh = make_fresh()
    actual = cps_convert_term(term, k, fresh)
    expected = L1.Abstract(
        destination="t0",
        parameters=["x", "k0"],
        body=L1.Apply(target="k0", arguments=["x"]),
        then=L1.Halt(value="t0"),
    )
    assert actual == expected


def test_cps_convert_term_apply():
    term = L2.Apply(target=L2.Reference(name="f"), arguments=[L2.Reference(name="y")])
    fresh = make_fresh()
    actual = cps_convert_term(term, k, fresh)
    expected = L1.Abstract(
        destination="k0",
        parameters=["t0"],
        body=L1.Halt(value="t0"),
        then=L1.Apply(target="f", arguments=["y", "k0"]),
    )
    assert actual == expected


def test_cps_convert_term_branch():
    term = L2.Branch(
        operator="==",
        left=L2.Reference(name="x"),
        right=L2.Reference(name="y"),
        consequent=L2.Reference(name="a"),
        otherwise=L2.Reference(name="b"),
    )
    fresh = make_fresh()
    actual = cps_convert_term(term, k, fresh)
    expected = L1.Abstract(
        destination="j0",
        parameters=["t0"],
        body=L1.Halt(value="t0"),
        then=L1.Branch(
            operator="==", left="x", right="y",
            then=L1.Apply(target="j0", arguments=["a"]),
            otherwise=L1.Apply(target="j0", arguments=["b"]),
        ),
    )
    assert actual == expected


def test_cps_convert_term_allocate():
    term = L2.Allocate(count=0)
    fresh = make_fresh()
    actual = cps_convert_term(term, k, fresh)
    expected = L1.Allocate(destination="t0", count=0, then=L1.Halt(value="t0"))
    assert actual == expected


def test_cps_convert_term_load():
    term_load = L2.Load(base=L2.Reference(name="x"), index=0)
    fresh = make_fresh()
    actual = cps_convert_term(term_load, k, fresh)
    expected = L1.Load(destination="t0", base="x", index=0, then=L1.Halt(value="t0"))
    assert actual == expected


def test_cps_convert_term_store():
    term = L2.Store(base=L2.Reference(name="x"), index=0, value=L2.Reference(name="y"))
    fresh = make_fresh()
    actual = cps_convert_term(term, k, fresh)
    expected = L1.Store(
        base="x", index=0, value="y",
        then=L1.Immediate(destination="t0", value=0, then=L1.Halt(value="t0")),
    )
    assert actual == expected


def test_cps_convert_term_begin():
    term = L2.Begin(effects=[L2.Reference(name="x")], value=L2.Reference(name="y"))
    fresh = make_fresh()
    actual = cps_convert_term(term, k, fresh)
    expected = L1.Halt(value="y")
    assert actual == expected


def test_cps_convert_program():
    program = L2.Program(parameters=["x"], body=L2.Reference(name="x"))
    fresh = make_fresh()
    actual = cps_convert_program(program, fresh)
    expected = L1.Program(parameters=["x"], body=L1.Halt(value="x"))
    assert actual == expected


# ===========================================================================
# Additional tests for full branch coverage
# ===========================================================================

# ---------------------------------------------------------------------------
# Reference
# ---------------------------------------------------------------------------

def test_reference_passes_name_to_continuation():
    # The continuation receives the name unchanged
    results = []
    cps_convert_term(L2.Reference(name="abc"), lambda n: results.append(n) or L1.Halt(value=n), make_fresh())
    assert results == ["abc"]


# ---------------------------------------------------------------------------
# Immediate — different values
# ---------------------------------------------------------------------------

def test_immediate_negative_value():
    term = L2.Immediate(value=-7)
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Immediate(destination="t0", value=-7, then=L1.Halt(value="t0"))


def test_immediate_zero():
    term = L2.Immediate(value=0)
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Immediate(destination="t0", value=0, then=L1.Halt(value="t0"))


# ---------------------------------------------------------------------------
# Primitive — all three operators
# ---------------------------------------------------------------------------

def test_primitive_sub():
    term = L2.Primitive(operator="-", left=L2.Reference(name="a"), right=L2.Reference(name="b"))
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Primitive(destination="t0", operator="-", left="a", right="b", then=L1.Halt(value="t0"))


def test_primitive_mul():
    term = L2.Primitive(operator="*", left=L2.Reference(name="a"), right=L2.Reference(name="b"))
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Primitive(destination="t0", operator="*", left="a", right="b", then=L1.Halt(value="t0"))


def test_primitive_non_reference_operands():
    # dest is allocated eagerly (t0), then _terms evaluates left (t1) and right (t2)
    term = L2.Primitive(
        operator="+",
        left=L2.Immediate(value=1),
        right=L2.Immediate(value=2),
    )
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Immediate(
        destination="t1", value=1,
        then=L1.Immediate(
            destination="t2", value=2,
            then=L1.Primitive(
                destination="t0", operator="+", left="t1", right="t2",
                then=L1.Halt(value="t0"),
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Let — empty bindings and multiple bindings
# ---------------------------------------------------------------------------

def test_let_empty_bindings():
    term = L2.Let(bindings=[], body=L2.Reference(name="x"))
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    # No bindings → just convert the body
    assert result == L1.Halt(value="x")


def test_let_three_bindings():
    term = L2.Let(
        bindings=[
            ("a", L2.Reference(name="x")),
            ("b", L2.Reference(name="y")),
            ("c", L2.Reference(name="z")),
        ],
        body=L2.Reference(name="c"),
    )
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Copy(
        destination="a", source="x",
        then=L1.Copy(
            destination="b", source="y",
            then=L1.Copy(
                destination="c", source="z",
                then=L1.Halt(value="c"),
            ),
        ),
    )


def test_let_non_reference_binding_value():
    # Binding value that requires a temp (Immediate)
    term = L2.Let(
        bindings=[("x", L2.Immediate(value=5))],
        body=L2.Reference(name="x"),
    )
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Immediate(
        destination="t0", value=5,
        then=L1.Copy(destination="x", source="t0", then=L1.Halt(value="x")),
    )


# ---------------------------------------------------------------------------
# Abstract — multiple parameters
# ---------------------------------------------------------------------------

def test_abstract_no_parameters():
    term = L2.Abstract(parameters=[], body=L2.Immediate(value=0))
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Abstract(
        destination="t0",
        parameters=["k0"],
        body=L1.Immediate(destination="t1", value=0, then=L1.Apply(target="k0", arguments=["t1"])),
        then=L1.Halt(value="t0"),
    )


def test_abstract_multiple_parameters():
    term = L2.Abstract(
        parameters=["a", "b"],
        body=L2.Primitive(operator="+", left=L2.Reference(name="a"), right=L2.Reference(name="b")),
    )
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Abstract(
        destination="t0",
        parameters=["a", "b", "k0"],
        body=L1.Primitive(
            destination="t1", operator="+", left="a", right="b",
            then=L1.Apply(target="k0", arguments=["t1"]),
        ),
        then=L1.Halt(value="t0"),
    )


# ---------------------------------------------------------------------------
# Apply — no arguments, multiple arguments
# ---------------------------------------------------------------------------

def test_apply_no_arguments():
    term = L2.Apply(target=L2.Reference(name="f"), arguments=[])
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Abstract(
        destination="k0",
        parameters=["t0"],
        body=L1.Halt(value="t0"),
        then=L1.Apply(target="f", arguments=["k0"]),
    )


def test_apply_multiple_arguments():
    term = L2.Apply(
        target=L2.Reference(name="f"),
        arguments=[L2.Reference(name="a"), L2.Reference(name="b")],
    )
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Abstract(
        destination="k0",
        parameters=["t0"],
        body=L1.Halt(value="t0"),
        then=L1.Apply(target="f", arguments=["a", "b", "k0"]),
    )


def test_apply_non_reference_target():
    # k_name=k0, result=t0 allocated eagerly, then _terms evaluates target → t1
    term = L2.Apply(
        target=L2.Immediate(value=99),
        arguments=[L2.Reference(name="x")],
    )
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Immediate(
        destination="t1", value=99,
        then=L1.Abstract(
            destination="k0",
            parameters=["t0"],
            body=L1.Halt(value="t0"),
            then=L1.Apply(target="t1", arguments=["x", "k0"]),
        ),
    )


# ---------------------------------------------------------------------------
# Branch — lt operator, non-reference operands
# ---------------------------------------------------------------------------

def test_branch_lt_operator():
    term = L2.Branch(
        operator="<",
        left=L2.Reference(name="x"),
        right=L2.Reference(name="y"),
        consequent=L2.Reference(name="a"),
        otherwise=L2.Reference(name="b"),
    )
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Abstract(
        destination="j0",
        parameters=["t0"],
        body=L1.Halt(value="t0"),
        then=L1.Branch(
            operator="<", left="x", right="y",
            then=L1.Apply(target="j0", arguments=["a"]),
            otherwise=L1.Apply(target="j0", arguments=["b"]),
        ),
    )


def test_branch_non_reference_consequent_and_otherwise():
    # Consequent and otherwise are Immediates — they each need a temp before Apply
    term = L2.Branch(
        operator="==",
        left=L2.Reference(name="x"),
        right=L2.Reference(name="y"),
        consequent=L2.Immediate(value=1),
        otherwise=L2.Immediate(value=0),
    )
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Abstract(
        destination="j0",
        parameters=["t0"],
        body=L1.Halt(value="t0"),
        then=L1.Branch(
            operator="==", left="x", right="y",
            then=L1.Immediate(destination="t1", value=1, then=L1.Apply(target="j0", arguments=["t1"])),
            otherwise=L1.Immediate(destination="t2", value=0, then=L1.Apply(target="j0", arguments=["t2"])),
        ),
    )


# ---------------------------------------------------------------------------
# Allocate — non-zero count
# ---------------------------------------------------------------------------

def test_allocate_nonzero():
    term = L2.Allocate(count=3)
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Allocate(destination="t0", count=3, then=L1.Halt(value="t0"))


# ---------------------------------------------------------------------------
# Load — non-zero index, non-reference base
# ---------------------------------------------------------------------------

def test_load_nonzero_index():
    term = L2.Load(base=L2.Reference(name="arr"), index=2)
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Load(destination="t0", base="arr", index=2, then=L1.Halt(value="t0"))


def test_load_non_reference_base():
    # dest=t0 allocated eagerly, then _term(base) evaluates Allocate → t1
    term = L2.Load(base=L2.Allocate(count=1), index=0)
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Allocate(
        destination="t1", count=1,
        then=L1.Load(destination="t0", base="t1", index=0, then=L1.Halt(value="t0")),
    )


# ---------------------------------------------------------------------------
# Store — non-reference base and value
# ---------------------------------------------------------------------------

def test_store_non_reference_value():
    # dummy=t0 allocated eagerly, then _terms evaluates base (Reference, no temp),
    # value (Immediate → t1), then Store uses t1, dummy t0 returned
    term = L2.Store(base=L2.Reference(name="x"), index=1, value=L2.Immediate(value=42))
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Immediate(
        destination="t1", value=42,
        then=L1.Store(
            base="x", index=1, value="t1",
            then=L1.Immediate(destination="t0", value=0, then=L1.Halt(value="t0")),
        ),
    )


def test_store_nonzero_index():
    term = L2.Store(base=L2.Reference(name="arr"), index=3, value=L2.Reference(name="v"))
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Store(
        base="arr", index=3, value="v",
        then=L1.Immediate(destination="t0", value=0, then=L1.Halt(value="t0")),
    )


# ---------------------------------------------------------------------------
# Begin — empty effects, multiple effects
# ---------------------------------------------------------------------------

def test_begin_no_effects():
    term = L2.Begin(effects=[], value=L2.Reference(name="x"))
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    assert result == L1.Halt(value="x")


def test_begin_multiple_effects():
    # Two effects, both References (so their results are just discarded)
    term = L2.Begin(
        effects=[L2.Reference(name="a"), L2.Reference(name="b")],
        value=L2.Reference(name="c"),
    )
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    # Both effects evaluated and discarded, then value returned
    assert result == L1.Halt(value="c")


def test_begin_effect_with_side_effect():
    # Effect is a Store (has actual side effect), value is a Reference
    term = L2.Begin(
        effects=[L2.Store(base=L2.Reference(name="x"), index=0, value=L2.Reference(name="v"))],
        value=L2.Reference(name="x"),
    )
    fresh = make_fresh()
    result = cps_convert_term(term, k, fresh)
    # Store emits its code, dummy Immediate result is discarded, then value
    assert result == L1.Store(
        base="x", index=0, value="v",
        then=L1.Immediate(destination="t0", value=0, then=L1.Halt(value="x")),
    )


# ---------------------------------------------------------------------------
# cps_convert_terms — empty list and multi-element list
# ---------------------------------------------------------------------------

def test_cps_convert_terms_empty():
    results = []
    cps_convert_terms([], lambda vs: results.append(vs) or L1.Halt(value="x"), make_fresh())
    assert results == [[]]


def test_cps_convert_terms_single():
    fresh = make_fresh()
    result = cps_convert_terms(
        [L2.Reference(name="x")],
        lambda vs: L1.Halt(value=vs[0]),
        fresh,
    )
    assert result == L1.Halt(value="x")


def test_cps_convert_terms_multiple():
    fresh = make_fresh()
    result = cps_convert_terms(
        [L2.Reference(name="a"), L2.Reference(name="b"), L2.Reference(name="c")],
        lambda vs: L1.Apply(target=vs[0], arguments=list(vs[1:])),
        fresh,
    )
    assert result == L1.Apply(target="a", arguments=["b", "c"])


# ---------------------------------------------------------------------------
# cps_convert_program — multiple parameters
# ---------------------------------------------------------------------------

def test_cps_convert_program_no_parameters():
    program = L2.Program(parameters=[], body=L2.Immediate(value=0))
    fresh = make_fresh()
    result = cps_convert_program(program, fresh)
    assert result == L1.Program(
        parameters=[],
        body=L1.Immediate(destination="t0", value=0, then=L1.Halt(value="t0")),
    )


def test_cps_convert_program_multiple_parameters():
    program = L2.Program(
        parameters=["a", "b"],
        body=L2.Primitive(operator="+", left=L2.Reference(name="a"), right=L2.Reference(name="b")),
    )
    fresh = make_fresh()
    result = cps_convert_program(program, fresh)
    assert result == L1.Program(
        parameters=["a", "b"],
        body=L1.Primitive(
            destination="t0", operator="+", left="a", right="b",
            then=L1.Halt(value="t0"),
        ),
    )