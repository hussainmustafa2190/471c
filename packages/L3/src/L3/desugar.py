from __future__ import annotations

from collections.abc import Callable

from util.sequential_name_generator import SequentialNameGenerator

from .syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Car,
    Cdr,
    Cons,
    Immediate,
    IsNil,
    Let,
    LetRec,
    ListLiteral,
    Load,
    Nil,
    Primitive,
    Program,
    Reference,
    Store,
    Term,
    Tuple,
    TupleRef,
)


def desugar_term(term: Term, fresh: Callable[[str], str]) -> Term:
    match term:
        case Tuple(elements=elements):
            n = len(elements)
            t = fresh("t")
            desugared_elements = [desugar_term(e, fresh) for e in elements]
            stores = [
                Store(base=Reference(name=t), index=i, value=v)
                for i, v in enumerate(desugared_elements)
            ]
            return Let(
                bindings=[(t, Allocate(count=n))],
                body=Begin(effects=stores, value=Reference(name=t)),
            )

        case TupleRef(base=base, index=index):
            return Load(base=desugar_term(base, fresh), index=index)

        case Nil():
            return Immediate(value=0)

        case Cons(head=head, tail=tail):
            c = fresh("c")
            return Let(
                bindings=[(c, Allocate(count=2))],
                body=Begin(
                    effects=[
                        Store(base=Reference(name=c), index=0, value=desugar_term(head, fresh)),
                        Store(base=Reference(name=c), index=1, value=desugar_term(tail, fresh)),
                    ],
                    value=Reference(name=c),
                ),
            )

        case Car(base=base):
            return Load(base=desugar_term(base, fresh), index=0)

        case Cdr(base=base):
            return Load(base=desugar_term(base, fresh), index=1)

        case IsNil(base=base):
            b = desugar_term(base, fresh)
            return Branch(
                operator="==",
                left=b,
                right=Immediate(value=0),
                consequent=Immediate(value=1),
                otherwise=Immediate(value=0),
            )

        case ListLiteral(elements=elements):
            if not elements:
                return Immediate(value=0)
            if len(elements) == 1:
                return desugar_term(Cons(head=elements[0], tail=Nil()), fresh)
            return desugar_term(
                Cons(head=elements[0], tail=ListLiteral(elements=elements[1:])),
                fresh,
            )

        case Let(bindings=bindings, body=body):
            return Let(
                bindings=[(n, desugar_term(v, fresh)) for n, v in bindings],
                body=desugar_term(body, fresh),
            )

        case LetRec(bindings=bindings, body=body):
            return LetRec(
                bindings=[(n, desugar_term(v, fresh)) for n, v in bindings],
                body=desugar_term(body, fresh),
            )

        case Reference(name=name):
            return Reference(name=name)

        case Abstract(parameters=parameters, body=body):
            return Abstract(parameters=parameters, body=desugar_term(body, fresh))

        case Apply(target=target, arguments=arguments):
            return Apply(
                target=desugar_term(target, fresh),
                arguments=[desugar_term(a, fresh) for a in arguments],
            )

        case Immediate(value=value):
            return Immediate(value=value)

        case Primitive(operator=operator, left=left, right=right):
            return Primitive(
                operator=operator,
                left=desugar_term(left, fresh),
                right=desugar_term(right, fresh),
            )

        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return Branch(
                operator=operator,
                left=desugar_term(left, fresh),
                right=desugar_term(right, fresh),
                consequent=desugar_term(consequent, fresh),
                otherwise=desugar_term(otherwise, fresh),
            )

        case Allocate(count=count):
            return Allocate(count=count)

        case Load(base=base, index=index):
            return Load(base=desugar_term(base, fresh), index=index)

        case Store(base=base, index=index, value=value):
            return Store(
                base=desugar_term(base, fresh),
                index=index,
                value=desugar_term(value, fresh),
            )

        case Begin(effects=effects, value=value):  # pragma: no branch
            return Begin(
                effects=[desugar_term(e, fresh) for e in effects],
                value=desugar_term(value, fresh),
            )


def desugar_program(program: Program) -> Program:
    fresh = SequentialNameGenerator()
    return Program(
        parameters=program.parameters,
        body=desugar_term(program.body, fresh),
    )
