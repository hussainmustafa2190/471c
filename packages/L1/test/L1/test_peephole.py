from __future__ import annotations

from L1.peephole import peephole_program, peephole_statement
from L1.syntax import (
    Abstract,
    Allocate,
    Apply,
    Branch,
    Copy,
    Halt,
    Immediate,
    Load,
    Primitive,
    Program,
    Store,
)


def test_rule1_self_copy_eliminates_to_halt() -> None:
    s = Copy(destination="x", source="x", then=Halt(value="x"))
    assert peephole_statement(s) == Halt(value="x")


def test_rule1_self_copy_non_trivial_then() -> None:
    inner = Copy(destination="y", source="z", then=Halt(value="y"))
    s = Copy(destination="x", source="x", then=inner)
    assert peephole_statement(s) == Halt(value="z")


def test_rule2_copy_then_halt_returns_source() -> None:
    s = Copy(destination="x", source="y", then=Halt(value="x"))
    assert peephole_statement(s) == Halt(value="y")


def test_rule2_does_not_fire_when_halt_value_differs() -> None:
    s = Copy(destination="x", source="y", then=Halt(value="z"))
    out = peephole_statement(s)
    assert out == Copy(destination="x", source="y", then=Halt(value="z"))


def test_rule1_does_not_fire_copy_different_source_rule2_applies() -> None:
    s = Copy(destination="x", source="y", then=Halt(value="x"))
    assert peephole_statement(s) == Halt(value="y")


def test_copy_passthrough_recurses_then() -> None:
    s = Copy(destination="x", source="y", then=Halt(value="z"))
    out = peephole_statement(s)
    assert out == Copy(destination="x", source="y", then=Halt(value="z"))


def test_immediate_recurses_then() -> None:
    s = Immediate(
        destination="a",
        value=1,
        then=Copy(destination="x", source="x", then=Halt(value="a")),
    )
    assert peephole_statement(s) == Immediate(
        destination="a",
        value=1,
        then=Halt(value="a"),
    )


def test_primitive_plus_recurses_then() -> None:
    s = Primitive(
        destination="d",
        operator="+",
        left="a",
        right="b",
        then=Copy(destination="x", source="y", then=Halt(value="x")),
    )
    assert peephole_statement(s) == Primitive(
        destination="d",
        operator="+",
        left="a",
        right="b",
        then=Halt(value="y"),
    )


def test_primitive_minus_recurses_then() -> None:
    s = Primitive(
        destination="d",
        operator="-",
        left="a",
        right="b",
        then=Halt(value="k"),
    )
    assert peephole_statement(s) == s


def test_primitive_star_recurses_then() -> None:
    s = Primitive(
        destination="d",
        operator="*",
        left="a",
        right="b",
        then=Copy(destination="u", source="u", then=Halt(value="u")),
    )
    assert peephole_statement(s) == Primitive(
        destination="d",
        operator="*",
        left="a",
        right="b",
        then=Halt(value="u"),
    )


def test_branch_recurses_both_arms_independently() -> None:
    s = Branch(
        operator="<",
        left="a",
        right="b",
        then=Copy(destination="x", source="x", then=Halt(value="t")),
        otherwise=Copy(destination="p", source="q", then=Halt(value="p")),
    )
    assert peephole_statement(s) == Branch(
        operator="<",
        left="a",
        right="b",
        then=Halt(value="t"),
        otherwise=Halt(value="q"),
    )


def test_abstract_recurses_body_and_then() -> None:
    s = Abstract(
        destination="f",
        parameters=["a"],
        body=Copy(destination="x", source="x", then=Halt(value="a")),
        then=Copy(destination="y", source="y", then=Halt(value="y")),
    )
    assert peephole_statement(s) == Abstract(
        destination="f",
        parameters=["a"],
        body=Halt(value="a"),
        then=Halt(value="y"),
    )


def test_allocate_recurses_then() -> None:
    s = Allocate(
        destination="m",
        count=2,
        then=Copy(destination="x", source="y", then=Halt(value="x")),
    )
    assert peephole_statement(s) == Allocate(
        destination="m",
        count=2,
        then=Halt(value="y"),
    )


def test_load_recurses_then() -> None:
    s = Load(
        destination="d",
        base="m",
        index=0,
        then=Copy(destination="x", source="x", then=Halt(value="d")),
    )
    assert peephole_statement(s) == Load(
        destination="d",
        base="m",
        index=0,
        then=Halt(value="d"),
    )


def test_store_recurses_then() -> None:
    s = Store(
        base="m",
        index=1,
        value="v",
        then=Copy(destination="x", source="y", then=Halt(value="x")),
    )
    assert peephole_statement(s) == Store(
        base="m",
        index=1,
        value="v",
        then=Halt(value="y"),
    )


def test_apply_terminal_unchanged() -> None:
    s = Apply(target="f", arguments=["a", "b"])
    assert peephole_statement(s) == s


def test_halt_terminal_unchanged() -> None:
    s = Halt(value="z")
    assert peephole_statement(s) == s


def test_peephole_program_wraps_and_preserves_parameters() -> None:
    p = Program(
        parameters=["p1", "p2"],
        body=Copy(destination="x", source="x", then=Halt(value="p1")),
    )
    out = peephole_program(p)
    assert out.parameters == p.parameters
    assert out.body == Halt(value="p1")


def test_rules_recursive_inside_branch_arms() -> None:
    s = Branch(
        operator="==",
        left="i",
        right="j",
        then=Copy(
            destination="x",
            source="y",
            then=Copy(destination="x", source="x", then=Halt(value="x")),
        ),
        otherwise=Copy(
            destination="a",
            source="a",
            then=Copy(destination="b", source="c", then=Halt(value="b")),
        ),
    )
    assert peephole_statement(s) == Branch(
        operator="==",
        left="i",
        right="j",
        then=Halt(value="y"),
        otherwise=Halt(value="c"),
    )


def test_rules_recursive_inside_abstract_body() -> None:
    s = Abstract(
        destination="g",
        parameters=["z"],
        body=Copy(
            destination="x",
            source="y",
            then=Copy(destination="x", source="x", then=Halt(value="x")),
        ),
        then=Halt(value="g"),
    )
    assert peephole_statement(s) == Abstract(
        destination="g",
        parameters=["z"],
        body=Halt(value="y"),
        then=Halt(value="g"),
    )
