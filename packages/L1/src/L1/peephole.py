from __future__ import annotations

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
    Statement,
    Store,
)


def peephole_statement(statement: Statement) -> Statement:
    match statement:
        case Copy(destination=destination, source=source, then=then):
            if destination == source:
                return peephole_statement(then)
            new_then = peephole_statement(then)
            if isinstance(new_then, Halt) and new_then.value == destination:
                return Halt(value=source)
            return Copy(
                destination=destination,
                source=source,
                then=new_then,
            )

        case Abstract(
            destination=destination,
            parameters=parameters,
            body=body,
            then=then,
        ):
            return Abstract(
                destination=destination,
                parameters=parameters,
                body=peephole_statement(body),
                then=peephole_statement(then),
            )

        case Immediate(destination=destination, value=value, then=then):
            return Immediate(
                destination=destination,
                value=value,
                then=peephole_statement(then),
            )

        case Primitive(
            destination=destination,
            operator=operator,
            left=left,
            right=right,
            then=then,
        ):
            return Primitive(
                destination=destination,
                operator=operator,
                left=left,
                right=right,
                then=peephole_statement(then),
            )

        case Branch(operator=operator, left=left, right=right, then=then, otherwise=otherwise):
            return Branch(
                operator=operator,
                left=left,
                right=right,
                then=peephole_statement(then),
                otherwise=peephole_statement(otherwise),
            )

        case Allocate(destination=destination, count=count, then=then):
            return Allocate(
                destination=destination,
                count=count,
                then=peephole_statement(then),
            )

        case Load(destination=destination, base=base, index=index, then=then):
            return Load(
                destination=destination,
                base=base,
                index=index,
                then=peephole_statement(then),
            )

        case Store(base=base, index=index, value=value, then=then):
            return Store(
                base=base,
                index=index,
                value=value,
                then=peephole_statement(then),
            )

        case Apply(target=target, arguments=arguments):
            return Apply(target=target, arguments=arguments)

        case Halt(value=value):  # pragma: no branch
            return Halt(value=value)


def peephole_program(program: Program) -> Program:
    return Program(
        parameters=program.parameters,
        body=peephole_statement(program.body),
    )
