from __future__ import annotations

from L0.dpe import _collect_addresses, dpe_program
from L0.syntax import (
    Address,
    Allocate,
    Branch,
    Call,
    Copy,
    Halt,
    Immediate,
    Load,
    Primitive,
    Procedure,
    Program,
    Store,
)


def _l0(body):
    return Procedure(name="l0", parameters=[], body=body)


def test_l0_kept_with_no_addresses() -> None:
    p = Program(procedures=[_l0(Halt(value="x"))])
    out = dpe_program(p)
    assert len(out.procedures) == 1
    assert out.procedures[0].name == "l0"


def test_procedure_referenced_by_address_in_l0_is_kept() -> None:
    f0 = Procedure(name="f0", parameters=[], body=Halt(value="a"))
    l0 = _l0(
        Address(
            destination="g",
            name="f0",
            then=Address(
                destination="h",
                name="not_a_procedure",
                then=Halt(value="g"),
            ),
        )
    )
    p = Program(procedures=[f0, l0])
    out = dpe_program(p)
    assert [q.name for q in out.procedures] == ["f0", "l0"]


def test_unreachable_procedure_removed() -> None:
    dead = Procedure(name="dead", parameters=[], body=Halt(value="x"))
    l0 = _l0(Halt(value="y"))
    p = Program(procedures=[dead, l0])
    out = dpe_program(p)
    assert [q.name for q in out.procedures] == ["l0"]


def test_transitive_reachability() -> None:
    f1 = Procedure(name="f1", parameters=[], body=Halt(value="z"))
    f0 = Procedure(
        name="f0",
        parameters=[],
        body=Address(destination="h", name="f1", then=Halt(value="h")),
    )
    l0 = _l0(Address(destination="g", name="f0", then=Halt(value="g")))
    p = Program(procedures=[f1, f0, l0])
    out = dpe_program(p)
    assert [q.name for q in out.procedures] == ["f1", "f0", "l0"]


def test_unreachable_removed_despite_similar_name_pattern() -> None:
    f0_live = Procedure(name="f0", parameters=[], body=Halt(value="a"))
    f0_dead = Procedure(name="f0_unused", parameters=[], body=Halt(value="b"))
    l0 = _l0(Address(destination="g", name="f0", then=Halt(value="g")))
    p = Program(procedures=[f0_dead, f0_live, l0])
    out = dpe_program(p)
    assert [q.name for q in out.procedures] == ["f0", "l0"]


def test_survivor_order_matches_original() -> None:
    a = Procedure(name="a", parameters=[], body=Halt(value="1"))
    b = Procedure(name="b", parameters=[], body=Halt(value="2"))
    l0 = _l0(
        Address(
            destination="x",
            name="b",
            then=Address(destination="y", name="a", then=Halt(value="y")),
        )
    )
    p = Program(procedures=[a, b, l0])
    out = dpe_program(p)
    assert [q.name for q in out.procedures] == ["a", "b", "l0"]


def test_all_procedures_live_nothing_removed() -> None:
    f0 = Procedure(name="f0", parameters=[], body=Halt(value="q"))
    l0 = _l0(Address(destination="g", name="f0", then=Halt(value="g")))
    p = Program(procedures=[f0, l0])
    out = dpe_program(p)
    assert out == p


def test_address_in_branch_then_keeps_procedure() -> None:
    f0 = Procedure(name="f0", parameters=[], body=Halt(value="t"))
    l0 = _l0(
        Branch(
            operator="<",
            left="a",
            right="b",
            then=Address(destination="g", name="f0", then=Halt(value="g")),
            otherwise=Halt(value="x"),
        )
    )
    p = Program(procedures=[f0, l0])
    out = dpe_program(p)
    assert [q.name for q in out.procedures] == ["f0", "l0"]


def test_address_in_branch_otherwise_keeps_procedure() -> None:
    f0 = Procedure(name="f0", parameters=[], body=Halt(value="t"))
    l0 = _l0(
        Branch(
            operator="==",
            left="a",
            right="b",
            then=Halt(value="x"),
            otherwise=Address(destination="g", name="f0", then=Halt(value="g")),
        )
    )
    p = Program(procedures=[f0, l0])
    out = dpe_program(p)
    assert [q.name for q in out.procedures] == ["f0", "l0"]


def test_multiple_addresses_same_body_keep_all() -> None:
    f0 = Procedure(name="f0", parameters=[], body=Halt(value="0"))
    f1 = Procedure(name="f1", parameters=[], body=Halt(value="1"))
    l0 = _l0(
        Address(
            destination="a",
            name="f0",
            then=Address(destination="b", name="f1", then=Halt(value="b")),
        )
    )
    p = Program(procedures=[f0, f1, l0])
    out = dpe_program(p)
    assert [q.name for q in out.procedures] == ["f0", "f1", "l0"]


def test_collect_addresses_copy_recurses_then() -> None:
    s = Copy(
        destination="d",
        source="s",
        then=Address(destination="x", name="p", then=Halt(value="x")),
    )
    assert _collect_addresses(s) == frozenset({"p"})


def test_collect_addresses_immediate_recurses_then() -> None:
    s = Immediate(
        destination="d",
        value=3,
        then=Address(destination="x", name="q", then=Halt(value="x")),
    )
    assert _collect_addresses(s) == frozenset({"q"})


def test_collect_addresses_primitive_recurses_then() -> None:
    s = Primitive(
        destination="d",
        operator="+",
        left="a",
        right="b",
        then=Address(destination="x", name="r", then=Halt(value="x")),
    )
    assert _collect_addresses(s) == frozenset({"r"})


def test_collect_addresses_allocate_recurses_then() -> None:
    s = Allocate(
        destination="m",
        count=1,
        then=Address(destination="x", name="s", then=Halt(value="x")),
    )
    assert _collect_addresses(s) == frozenset({"s"})


def test_collect_addresses_load_recurses_then() -> None:
    s = Load(
        destination="d",
        base="m",
        index=0,
        then=Address(destination="x", name="t", then=Halt(value="x")),
    )
    assert _collect_addresses(s) == frozenset({"t"})


def test_collect_addresses_store_recurses_then() -> None:
    s = Store(
        base="m",
        index=0,
        value="v",
        then=Address(destination="x", name="u", then=Halt(value="x")),
    )
    assert _collect_addresses(s) == frozenset({"u"})


def test_collect_addresses_call_empty() -> None:
    assert _collect_addresses(Call(target="f", arguments=[])) == frozenset()


def test_collect_addresses_halt_empty() -> None:
    assert _collect_addresses(Halt(value="z")) == frozenset()


def test_fixed_point_two_passes() -> None:
    dead = Procedure(name="dead", parameters=[], body=Halt(value="n"))
    f1 = Procedure(name="f1", parameters=[], body=Halt(value="end"))
    f0 = Procedure(
        name="f0",
        parameters=[],
        body=Address(destination="h", name="f1", then=Halt(value="h")),
    )
    l0 = _l0(Address(destination="g", name="f0", then=Halt(value="g")))
    p = Program(procedures=[dead, f1, f0, l0])
    out = dpe_program(p)
    assert [q.name for q in out.procedures] == ["f1", "f0", "l0"]


def test_dpe_single_procedure_l0_unchanged() -> None:
    p = Program(procedures=[_l0(Halt(value="k"))])
    out = dpe_program(p)
    assert out == p
