from __future__ import annotations

from functools import partial

from L0 import syntax as L0
from L1 import syntax as L1
from util.sequential_name_generator import SequentialNameGenerator


def close_statement(
    statement: L1.Statement,
    *,
    generator: SequentialNameGenerator,
    procedures: list[L0.Procedure],
) -> L0.Statement:
    _statement = partial(close_statement, generator=generator, procedures=procedures)

    match statement:
        case L1.Copy(destination=destination, source=source, then=then):
            return L0.Copy(
                destination=destination,
                source=source,
                then=_statement(then),
            )

        case L1.Immediate(destination=destination, value=value, then=then):
            return L0.Immediate(
                destination=destination,
                value=value,
                then=_statement(then),
            )

        case L1.Primitive(
            destination=destination,
            operator=operator,
            left=left,
            right=right,
            then=then,
        ):
            return L0.Primitive(
                destination=destination,
                operator=operator,
                left=left,
                right=right,
                then=_statement(then),
            )

        case L1.Branch(operator=operator, left=left, right=right, then=then, otherwise=otherwise):
            return L0.Branch(
                operator=operator,
                left=left,
                right=right,
                then=_statement(then),
                otherwise=_statement(otherwise),
            )

        case L1.Allocate(destination=destination, count=count, then=then):
            return L0.Allocate(
                destination=destination,
                count=count,
                then=_statement(then),
            )

        case L1.Load(destination=destination, base=base, index=index, then=then):
            return L0.Load(
                destination=destination,
                base=base,
                index=index,
                then=_statement(then),
            )

        case L1.Store(base=base, index=index, value=value, then=then):
            return L0.Store(
                base=base,
                index=index,
                value=value,
                then=_statement(then),
            )

        case L1.Apply(target=target, arguments=arguments):
            return L0.Call(
                target=target,
                arguments=arguments,
            )

        case L1.Abstract(destination=destination, parameters=parameters, body=body, then=then):
            closed_body = _statement(body)
            name = generator("f")
            procedures.append(
                L0.Procedure(
                    name=name,
                    parameters=parameters,
                    body=closed_body,
                )
            )
            return L0.Address(
                destination=destination,
                name=name,
                then=_statement(then),
            )

        case L1.Halt(value=value):  # pragma: no branch
            return L0.Halt(value=value)


def close_program(program: L1.Program) -> L0.Program:
    generator = SequentialNameGenerator()
    procedures: list[L0.Procedure] = []

    match program:
        case L1.Program(parameters=parameters, body=body):  # pragma: no branch
            closed_body = close_statement(body, generator=generator, procedures=procedures)
            procedures.append(
                L0.Procedure(
                    name="l0",
                    parameters=parameters,
                    body=closed_body,
                )
            )
            return L0.Program(procedures=procedures)
