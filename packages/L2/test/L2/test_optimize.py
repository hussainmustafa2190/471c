"""
Tests for L2/src/L2/optimize.py

Coverage targets:
  ConstantPropagation._subst       — every node type, shadowing in Let, shadowing in Abstract
  ConstantPropagation._fold        — Primitive (+, -, *), Branch (<, ==) true/false
  ConstantPropagation.run          — every node type, Let with all-constant bindings,
                                     Let with surviving non-constant bindings,
                                     Branch that folds vs Branch that stays
  DeadCodeElimination._free_names  — every node type
  DeadCodeElimination._is_pure     — Immediate/Reference/Allocate, Primitive, Load, Abstract,
                                     impure (Apply, Store)
  DeadCodeElimination.run          — every node type, dead binding dropped, live binding kept,
                                     all bindings dead → bare body
  optimize_program                 — loop runs to stability, existing test case
"""

import pytest

from L2.optimize import ConstantPropagation, DeadCodeElimination, optimize_program
from L2.syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Immediate,
    Let,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

cp = ConstantPropagation()
dce = DeadCodeElimination()


# ===========================================================================
# ConstantPropagation._subst
# ===========================================================================

class TestSubst:

    def test_reference_matching(self):
        # The name we are substituting — should be replaced
        assert cp._subst(Reference(name="x"), "x", Immediate(value=5)) == Immediate(value=5)

    def test_reference_non_matching(self):
        # A different name — should be left alone
        assert cp._subst(Reference(name="y"), "x", Immediate(value=5)) == Reference(name="y")

    def test_immediate(self):
        assert cp._subst(Immediate(value=3), "x", Immediate(value=5)) == Immediate(value=3)

    def test_allocate(self):
        assert cp._subst(Allocate(count=2), "x", Immediate(value=5)) == Allocate(count=2)

    def test_primitive(self):
        term = Primitive(operator="+", left=Reference(name="x"), right=Reference(name="x"))
        result = cp._subst(term, "x", Immediate(value=4))
        assert result == Primitive(operator="+", left=Immediate(value=4), right=Immediate(value=4))

    def test_apply(self):
        term = Apply(target=Reference(name="x"), arguments=[Reference(name="x")])
        result = cp._subst(term, "x", Immediate(value=7))
        assert result == Apply(target=Immediate(value=7), arguments=[Immediate(value=7)])

    def test_load(self):
        term = Load(base=Reference(name="x"), index=0)
        result = cp._subst(term, "x", Immediate(value=1))
        assert result == Load(base=Immediate(value=1), index=0)

    def test_store(self):
        term = Store(base=Reference(name="x"), index=0, value=Reference(name="x"))
        result = cp._subst(term, "x", Immediate(value=9))
        assert result == Store(base=Immediate(value=9), index=0, value=Immediate(value=9))

    def test_begin(self):
        term = Begin(effects=[Reference(name="x")], value=Reference(name="x"))
        result = cp._subst(term, "x", Immediate(value=2))
        assert result == Begin(effects=[Immediate(value=2)], value=Immediate(value=2))

    def test_branch(self):
        term = Branch(
            operator="==",
            left=Reference(name="x"),
            right=Reference(name="x"),
            consequent=Reference(name="x"),
            otherwise=Immediate(value=0),
        )
        result = cp._subst(term, "x", Immediate(value=3))
        assert result == Branch(
            operator="==",
            left=Immediate(value=3),
            right=Immediate(value=3),
            consequent=Immediate(value=3),
            otherwise=Immediate(value=0),
        )

    def test_abstract_shadowed(self):
        # x is a parameter of the lambda — substitution should stop at the boundary
        term = Abstract(parameters=["x"], body=Reference(name="x"))
        result = cp._subst(term, "x", Immediate(value=99))
        assert result == term  # unchanged

    def test_abstract_not_shadowed(self):
        # y is not a parameter — substitution continues into the body
        term = Abstract(parameters=["y"], body=Reference(name="x"))
        result = cp._subst(term, "x", Immediate(value=10))
        assert result == Abstract(parameters=["y"], body=Immediate(value=10))

    def test_let_shadowed(self):
        # The Let re-binds "x", so the body should NOT be substituted
        term = Let(
            bindings=[("x", Immediate(value=0))],
            body=Reference(name="x"),
        )
        result = cp._subst(term, "x", Immediate(value=99))
        # binding value substituted before shadow takes effect; body left alone
        assert result == Let(bindings=[("x", Immediate(value=0))], body=Reference(name="x"))

    def test_let_not_shadowed(self):
        # "y" is bound, not "x" — x should propagate into the body
        term = Let(
            bindings=[("y", Reference(name="x"))],
            body=Reference(name="x"),
        )
        result = cp._subst(term, "x", Immediate(value=5))
        assert result == Let(bindings=[("y", Immediate(value=5))], body=Immediate(value=5))

    def test_let_multiple_bindings_shadow_stops_early(self):
        # First binding is "a", second is "x" (shadows). Body should not be substituted.
        term = Let(
            bindings=[("a", Reference(name="x")), ("x", Immediate(value=0))],
            body=Reference(name="x"),
        )
        result = cp._subst(term, "x", Immediate(value=7))
        # "a"'s value gets substituted, "x" binding value gets substituted before shadow,
        # body left alone
        assert result == Let(
            bindings=[("a", Immediate(value=7)), ("x", Immediate(value=0))],
            body=Reference(name="x"),
        )


# ===========================================================================
# ConstantPropagation._fold
# ===========================================================================

class TestFold:

    def test_fold_add(self):
        term = Primitive(operator="+", left=Immediate(value=3), right=Immediate(value=4))
        assert cp._fold(term) == Immediate(value=7)

    def test_fold_sub(self):
        term = Primitive(operator="-", left=Immediate(value=10), right=Immediate(value=3))
        assert cp._fold(term) == Immediate(value=7)

    def test_fold_mul(self):
        term = Primitive(operator="*", left=Immediate(value=3), right=Immediate(value=4))
        assert cp._fold(term) == Immediate(value=12)

    def test_fold_branch_lt_true(self):
        # 1 < 2 is true → consequent
        term = Branch(
            operator="<",
            left=Immediate(value=1),
            right=Immediate(value=2),
            consequent=Immediate(value=100),
            otherwise=Immediate(value=200),
        )
        assert cp._fold(term) == Immediate(value=100)

    def test_fold_branch_lt_false(self):
        # 5 < 2 is false → otherwise
        term = Branch(
            operator="<",
            left=Immediate(value=5),
            right=Immediate(value=2),
            consequent=Immediate(value=100),
            otherwise=Immediate(value=200),
        )
        assert cp._fold(term) == Immediate(value=200)

    def test_fold_branch_eq_true(self):
        term = Branch(
            operator="==",
            left=Immediate(value=4),
            right=Immediate(value=4),
            consequent=Immediate(value=1),
            otherwise=Immediate(value=0),
        )
        assert cp._fold(term) == Immediate(value=1)

    def test_fold_branch_eq_false(self):
        term = Branch(
            operator="==",
            left=Immediate(value=3),
            right=Immediate(value=4),
            consequent=Immediate(value=1),
            otherwise=Immediate(value=0),
        )
        assert cp._fold(term) == Immediate(value=0)

    def test_fold_no_match_returns_term(self):
        # Not both Immediates — nothing to fold
        term = Primitive(operator="+", left=Reference(name="x"), right=Immediate(value=1))
        assert cp._fold(term) is term


# ===========================================================================
# ConstantPropagation.run
# ===========================================================================

class TestCPRun:

    def test_immediate(self):
        assert cp.run(Immediate(value=42)) == Immediate(value=42)

    def test_reference(self):
        assert cp.run(Reference(name="x")) == Reference(name="x")

    def test_allocate(self):
        assert cp.run(Allocate(count=1)) == Allocate(count=1)

    def test_let_all_constants_inlined(self):
        # Both bindings are constants → both get inlined, Let disappears
        term = Let(
            bindings=[("x", Immediate(value=3)), ("y", Immediate(value=4))],
            body=Primitive(operator="+", left=Reference(name="x"), right=Reference(name="y")),
        )
        assert cp.run(term) == Immediate(value=7)

    def test_let_non_constant_survives(self):
        # "f" is an Allocate (not a constant) → it stays as a binding
        term = Let(
            bindings=[("f", Allocate(count=1))],
            body=Reference(name="f"),
        )
        result = cp.run(term)
        assert result == Let(bindings=[("f", Allocate(count=1))], body=Reference(name="f"))

    def test_let_reference_binding_inlined(self):
        # binding a Reference is also a constant — gets substituted
        term = Let(
            bindings=[("a", Reference(name="x"))],
            body=Reference(name="a"),
        )
        assert cp.run(term) == Reference(name="x")

    def test_let_body_branch_folds_true(self):
        # x=0, y=0 → branch (== 0 0) → consequent
        term = Let(
            bindings=[("x", Immediate(value=0)), ("y", Immediate(value=0))],
            body=Branch(
                operator="==",
                left=Reference(name="x"),
                right=Reference(name="y"),
                consequent=Immediate(value=1),
                otherwise=Immediate(value=99),
            ),
        )
        assert cp.run(term) == Immediate(value=1)

    def test_let_body_branch_folds_false(self):
        # x=1, y=2 → branch (< 2 1) is false → otherwise
        term = Let(
            bindings=[("x", Immediate(value=2)), ("y", Immediate(value=1))],
            body=Branch(
                operator="<",
                left=Reference(name="x"),
                right=Reference(name="y"),
                consequent=Immediate(value=99),
                otherwise=Immediate(value=0),
            ),
        )
        assert cp.run(term) == Immediate(value=0)

    def test_abstract(self):
        term = Abstract(
            parameters=["x"],
            body=Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=2)),
        )
        assert cp.run(term) == Abstract(parameters=["x"], body=Immediate(value=3))

    def test_apply(self):
        term = Apply(
            target=Reference(name="f"),
            arguments=[Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1))],
        )
        assert cp.run(term) == Apply(target=Reference(name="f"), arguments=[Immediate(value=2)])

    def test_primitive_folds(self):
        term = Primitive(operator="*", left=Immediate(value=3), right=Immediate(value=3))
        assert cp.run(term) == Immediate(value=9)

    def test_primitive_no_fold(self):
        term = Primitive(operator="+", left=Reference(name="x"), right=Immediate(value=1))
        assert cp.run(term) == term

    def test_branch_folds_to_consequent(self):
        term = Branch(
            operator="<",
            left=Immediate(value=1),
            right=Immediate(value=10),
            consequent=Immediate(value=42),
            otherwise=Immediate(value=0),
        )
        assert cp.run(term) == Immediate(value=42)

    def test_branch_folds_to_otherwise(self):
        term = Branch(
            operator="==",
            left=Immediate(value=1),
            right=Immediate(value=2),
            consequent=Immediate(value=42),
            otherwise=Immediate(value=0),
        )
        assert cp.run(term) == Immediate(value=0)

    def test_branch_does_not_fold(self):
        # left is not Immediate → stays as a Branch, but branches are recursed into
        term = Branch(
            operator="==",
            left=Reference(name="x"),
            right=Immediate(value=0),
            consequent=Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1)),
            otherwise=Immediate(value=99),
        )
        result = cp.run(term)
        assert result == Branch(
            operator="==",
            left=Reference(name="x"),
            right=Immediate(value=0),
            consequent=Immediate(value=2),
            otherwise=Immediate(value=99),
        )

    def test_load(self):
        term = Load(base=Reference(name="x"), index=0)
        assert cp.run(term) == Load(base=Reference(name="x"), index=0)

    def test_store(self):
        term = Store(
            base=Reference(name="x"),
            index=0,
            value=Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=2)),
        )
        assert cp.run(term) == Store(base=Reference(name="x"), index=0, value=Immediate(value=3))

    def test_begin(self):
        term = Begin(
            effects=[Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1))],
            value=Immediate(value=5),
        )
        assert cp.run(term) == Begin(effects=[Immediate(value=2)], value=Immediate(value=5))


# ===========================================================================
# DeadCodeElimination._free_names
# ===========================================================================

class TestFreeNames:

    def test_reference(self):
        assert dce._free_names(Reference(name="x")) == frozenset({"x"})

    def test_immediate(self):
        assert dce._free_names(Immediate(value=1)) == frozenset()

    def test_allocate(self):
        assert dce._free_names(Allocate(count=1)) == frozenset()

    def test_primitive(self):
        term = Primitive(operator="+", left=Reference(name="a"), right=Reference(name="b"))
        assert dce._free_names(term) == frozenset({"a", "b"})

    def test_apply(self):
        term = Apply(target=Reference(name="f"), arguments=[Reference(name="x")])
        assert dce._free_names(term) == frozenset({"f", "x"})

    def test_branch(self):
        term = Branch(
            operator="<",
            left=Reference(name="a"),
            right=Reference(name="b"),
            consequent=Reference(name="c"),
            otherwise=Reference(name="d"),
        )
        assert dce._free_names(term) == frozenset({"a", "b", "c", "d"})

    def test_load(self):
        assert dce._free_names(Load(base=Reference(name="x"), index=0)) == frozenset({"x"})

    def test_store(self):
        term = Store(base=Reference(name="x"), index=0, value=Reference(name="y"))
        assert dce._free_names(term) == frozenset({"x", "y"})

    def test_begin(self):
        term = Begin(effects=[Reference(name="a")], value=Reference(name="b"))
        assert dce._free_names(term) == frozenset({"a", "b"})

    def test_abstract_removes_params(self):
        term = Abstract(parameters=["x"], body=Reference(name="x"))
        assert dce._free_names(term) == frozenset()

    def test_abstract_free_survives(self):
        term = Abstract(parameters=["x"], body=Reference(name="y"))
        assert dce._free_names(term) == frozenset({"y"})

    def test_let_bound_name_not_free(self):
        # x is bound inside the let, so it should not appear in free names
        term = Let(bindings=[("x", Immediate(value=1))], body=Reference(name="x"))
        assert dce._free_names(term) == frozenset()

    def test_let_value_free_names_included(self):
        # The binding value references "y" which is free
        term = Let(bindings=[("x", Reference(name="y"))], body=Reference(name="x"))
        assert dce._free_names(term) == frozenset({"y"})


# ===========================================================================
# DeadCodeElimination._is_pure
# ===========================================================================

class TestIsPure:

    def test_immediate(self):
        assert dce._is_pure(Immediate(value=1)) is True

    def test_reference(self):
        assert dce._is_pure(Reference(name="x")) is True

    def test_allocate(self):
        assert dce._is_pure(Allocate(count=1)) is True

    def test_abstract(self):
        assert dce._is_pure(Abstract(parameters=["x"], body=Reference(name="x"))) is True

    def test_primitive_pure(self):
        term = Primitive(operator="+", left=Immediate(value=1), right=Reference(name="x"))
        assert dce._is_pure(term) is True

    def test_primitive_impure_nested(self):
        # Store inside a Primitive operand makes it impure
        term = Primitive(
            operator="+",
            left=Apply(target=Reference(name="f"), arguments=[]),
            right=Immediate(value=1),
        )
        assert dce._is_pure(term) is False

    def test_load_pure(self):
        assert dce._is_pure(Load(base=Reference(name="x"), index=0)) is True

    def test_load_impure_base(self):
        assert dce._is_pure(Load(base=Apply(target=Reference(name="f"), arguments=[]), index=0)) is False

    def test_apply_impure(self):
        assert dce._is_pure(Apply(target=Reference(name="f"), arguments=[])) is False

    def test_store_impure(self):
        assert dce._is_pure(Store(base=Reference(name="x"), index=0, value=Immediate(value=1))) is False

    def test_begin_impure(self):
        assert dce._is_pure(Begin(effects=[], value=Immediate(value=1))) is False


# ===========================================================================
# DeadCodeElimination.run
# ===========================================================================

class TestDCERun:

    def test_immediate(self):
        assert dce.run(Immediate(value=5)) == Immediate(value=5)

    def test_reference(self):
        assert dce.run(Reference(name="x")) == Reference(name="x")

    def test_allocate(self):
        assert dce.run(Allocate(count=2)) == Allocate(count=2)

    def test_dead_binding_dropped(self):
        # "x" is never used in body — drop it
        term = Let(
            bindings=[("x", Immediate(value=99))],
            body=Immediate(value=0),
        )
        assert dce.run(term) == Immediate(value=0)

    def test_live_binding_kept(self):
        term = Let(
            bindings=[("x", Immediate(value=5))],
            body=Reference(name="x"),
        )
        assert dce.run(term) == Let(bindings=[("x", Immediate(value=5))], body=Reference(name="x"))

    def test_impure_dead_binding_kept(self):
        # Even though "f" is unused, the Apply has side effects — must keep it
        term = Let(
            bindings=[("f", Apply(target=Reference(name="g"), arguments=[]))],
            body=Immediate(value=0),
        )
        assert dce.run(term) == Let(
            bindings=[("f", Apply(target=Reference(name="g"), arguments=[]))],
            body=Immediate(value=0),
        )

    def test_all_bindings_dead_returns_body(self):
        # Two dead pure bindings → both dropped, bare body returned
        term = Let(
            bindings=[("x", Immediate(value=1)), ("y", Immediate(value=2))],
            body=Immediate(value=42),
        )
        assert dce.run(term) == Immediate(value=42)

    def test_abstract(self):
        term = Abstract(
            parameters=["x"],
            body=Let(bindings=[("y", Immediate(value=0))], body=Reference(name="x")),
        )
        # "y" is dead inside the abstract's body
        assert dce.run(term) == Abstract(parameters=["x"], body=Reference(name="x"))

    def test_apply(self):
        term = Apply(
            target=Reference(name="f"),
            arguments=[Reference(name="x")],
        )
        assert dce.run(term) == term

    def test_primitive(self):
        term = Primitive(operator="+", left=Reference(name="a"), right=Reference(name="b"))
        assert dce.run(term) == term

    def test_branch(self):
        term = Branch(
            operator="<",
            left=Reference(name="a"),
            right=Reference(name="b"),
            consequent=Reference(name="c"),
            otherwise=Reference(name="d"),
        )
        assert dce.run(term) == term

    def test_load(self):
        term = Load(base=Reference(name="x"), index=0)
        assert dce.run(term) == term

    def test_store(self):
        term = Store(base=Reference(name="x"), index=0, value=Reference(name="y"))
        assert dce.run(term) == term

    def test_begin(self):
        term = Begin(effects=[Reference(name="a")], value=Reference(name="b"))
        assert dce.run(term) == term

    def test_partial_dead(self):
        # "x" used, "y" dead — only y dropped
        term = Let(
            bindings=[("x", Immediate(value=1)), ("y", Immediate(value=2))],
            body=Reference(name="x"),
        )
        assert dce.run(term) == Let(bindings=[("x", Immediate(value=1))], body=Reference(name="x"))


# ===========================================================================
# optimize_program — integration / loop tests
# ===========================================================================

class TestOptimizeProgram:

    def test_existing_test_case(self):
        # The test that ships with the repo
        program = Program(
            parameters=[],
            body=Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1)),
        )
        assert optimize_program(program) == Program(parameters=[], body=Immediate(value=2))

    def test_already_optimal_is_stable(self):
        # Running on something already optimal should return it unchanged
        program = Program(parameters=["x"], body=Reference(name="x"))
        assert optimize_program(program) == program

    def test_loop_runs_multiple_passes(self):
        # CP inlines "x=1" and "y=x" → Primitive(+, 1, 1)
        # Then fold turns that into Immediate(2)
        # Then DCE drops any dead Let wrappers
        # All of this may need more than one pass
        program = Program(
            parameters=[],
            body=Let(
                bindings=[
                    ("x", Immediate(value=1)),
                    ("y", Reference(name="x")),  # y = x = 1
                ],
                body=Primitive(operator="+", left=Reference(name="x"), right=Reference(name="y")),
            ),
        )
        assert optimize_program(program) == Program(parameters=[], body=Immediate(value=2))

    def test_dead_code_after_fold(self):
        # Branch folds away → one branch is dead, Let around it becomes dead too
        program = Program(
            parameters=[],
            body=Let(
                bindings=[("unused", Immediate(value=99))],
                body=Branch(
                    operator="==",
                    left=Immediate(value=0),
                    right=Immediate(value=0),
                    consequent=Immediate(value=1),
                    otherwise=Immediate(value=0),
                ),
            ),
        )
        assert optimize_program(program) == Program(parameters=[], body=Immediate(value=1))

    def test_parameters_preserved(self):
        program = Program(
            parameters=["a", "b"],
            body=Primitive(operator="+", left=Immediate(value=2), right=Immediate(value=3)),
        )
        result = optimize_program(program)
        assert result.parameters == ["a", "b"]
        assert result.body == Immediate(value=5)

    def test_propagation_then_fold_then_dce(self):
        # Let x=3, y=4 in (x * y) → fold to 12, both bindings become dead → Immediate(12)
        program = Program(
            parameters=[],
            body=Let(
                bindings=[("x", Immediate(value=3)), ("y", Immediate(value=4))],
                body=Primitive(operator="*", left=Reference(name="x"), right=Reference(name="y")),
            ),
        )
        assert optimize_program(program) == Program(parameters=[], body=Immediate(value=12))
