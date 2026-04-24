from __future__ import annotations

from L0 import syntax as L0
from L1 import syntax as L1
from L1.close import close_program


def test_close_program_entry_procedure_is_named_l0() -> None:
    program = L1.Program(parameters=["x"], body=L1.Halt(value="x"))
    closed = close_program(program)

    assert [p.name for p in closed.procedures] == ["l0"]
    assert closed.procedures[0].parameters == ["x"]
    assert closed.procedures[0].body == L0.Halt(value="x")


def test_close_converts_all_shared_statement_kinds_and_apply() -> None:
    program = L1.Program(
        parameters=["x", "y"],
        body=L1.Copy(
            destination="a",
            source="x",
            then=L1.Immediate(
                destination="b",
                value=7,
                then=L1.Primitive(
                    destination="c",
                    operator="+",
                    left="a",
                    right="b",
                    then=L1.Allocate(
                        destination="arr",
                        count=2,
                        then=L1.Load(
                            destination="d",
                            base="arr",
                            index=0,
                            then=L1.Store(
                                base="arr",
                                index=1,
                                value="d",
                                then=L1.Branch(
                                    operator="<",
                                    left="a",
                                    right="b",
                                    then=L1.Apply(target="f", arguments=["x", "y"]),
                                    otherwise=L1.Halt(value="c"),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    closed = close_program(program)
    assert [p.name for p in closed.procedures] == ["l0"]

    expected_body: L0.Statement = L0.Copy(
        destination="a",
        source="x",
        then=L0.Immediate(
            destination="b",
            value=7,
            then=L0.Primitive(
                destination="c",
                operator="+",
                left="a",
                right="b",
                then=L0.Allocate(
                    destination="arr",
                    count=2,
                    then=L0.Load(
                        destination="d",
                        base="arr",
                        index=0,
                        then=L0.Store(
                            base="arr",
                            index=1,
                            value="d",
                            then=L0.Branch(
                                operator="<",
                                left="a",
                                right="b",
                                then=L0.Call(target="f", arguments=["x", "y"]),
                                otherwise=L0.Halt(value="c"),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    assert closed.procedures[0].body == expected_body


def test_close_lifts_single_abstract_before_entry_procedure() -> None:
    program = L1.Program(
        parameters=["x"],
        body=L1.Abstract(
            destination="f",
            parameters=["y"],
            body=L1.Halt(value="y"),
            then=L1.Apply(target="f", arguments=["x"]),
        ),
    )

    closed = close_program(program)

    assert [p.name for p in closed.procedures] == ["f0", "l0"]
    assert closed.procedures[0] == L0.Procedure(name="f0", parameters=["y"], body=L0.Halt(value="y"))
    assert closed.procedures[1].body == L0.Address(
        destination="f",
        name="f0",
        then=L0.Call(target="f", arguments=["x"]),
    )


def test_close_lifts_multiple_abstracts_in_encounter_order() -> None:
    program = L1.Program(
        parameters=["x"],
        body=L1.Abstract(
            destination="f",
            parameters=["a"],
            body=L1.Halt(value="a"),
            then=L1.Abstract(
                destination="g",
                parameters=["b"],
                body=L1.Halt(value="b"),
                then=L1.Branch(
                    operator="==",
                    left="x",
                    right="x",
                    then=L1.Apply(target="f", arguments=["x"]),
                    otherwise=L1.Apply(target="g", arguments=["x"]),
                ),
            ),
        ),
    )

    closed = close_program(program)
    assert [p.name for p in closed.procedures] == ["f0", "f1", "l0"]

    assert closed.procedures[0].parameters == ["a"]
    assert closed.procedures[1].parameters == ["b"]

    assert closed.procedures[2].body == L0.Address(
        destination="f",
        name="f0",
        then=L0.Address(
            destination="g",
            name="f1",
            then=L0.Branch(
                operator="==",
                left="x",
                right="x",
                then=L0.Call(target="f", arguments=["x"]),
                otherwise=L0.Call(target="g", arguments=["x"]),
            ),
        ),
    )


def test_close_lifts_nested_abstracts_depth_first() -> None:
    program = L1.Program(
        parameters=["x"],
        body=L1.Abstract(
            destination="outer",
            parameters=["y"],
            body=L1.Abstract(
                destination="inner",
                parameters=["z"],
                body=L1.Halt(value="z"),
                then=L1.Apply(target="inner", arguments=["y"]),
            ),
            then=L1.Apply(target="outer", arguments=["x"]),
        ),
    )

    closed = close_program(program)
    assert [p.name for p in closed.procedures] == ["f0", "f1", "l0"]

    assert closed.procedures[0] == L0.Procedure(name="f0", parameters=["z"], body=L0.Halt(value="z"))
    assert closed.procedures[1].parameters == ["y"]

    assert closed.procedures[1].body == L0.Address(
        destination="inner",
        name="f0",
        then=L0.Call(target="inner", arguments=["y"]),
    )

    assert closed.procedures[2].body == L0.Address(
        destination="outer",
        name="f1",
        then=L0.Call(target="outer", arguments=["x"]),
    )

