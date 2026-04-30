from __future__ import annotations

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
    Statement,
    Store,
)


def _collect_addresses(statement: Statement) -> frozenset[str]:
    match statement:
        case Address(name=name, then=then):
            return frozenset({name}) | _collect_addresses(then)

        case Branch(then=then, otherwise=otherwise):
            return _collect_addresses(then) | _collect_addresses(otherwise)

        case Copy(then=then):
            return _collect_addresses(then)

        case Immediate(then=then):
            return _collect_addresses(then)

        case Primitive(then=then):
            return _collect_addresses(then)

        case Allocate(then=then):
            return _collect_addresses(then)

        case Load(then=then):
            return _collect_addresses(then)

        case Store(then=then):
            return _collect_addresses(then)

        case Call():
            return frozenset()

        case Halt():  # pragma: no branch
            return frozenset()


def dpe_program(program: Program) -> Program:
    proc_map: dict[str, Procedure] = {p.name: p for p in program.procedures}
    live: set[str] = {"l0"}

    while True:
        discovered: set[str] = set()
        for name in live:
            proc = proc_map.get(name)
            if proc is None:
                continue
            discovered |= _collect_addresses(proc.body)
        next_live = live | discovered
        if next_live == live:
            break
        live = next_live

    kept = [p for p in program.procedures if p.name in live]
    return Program(procedures=kept)
