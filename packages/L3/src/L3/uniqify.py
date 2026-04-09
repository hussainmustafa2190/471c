from collections.abc import Callable, Mapping
from functools import partial

from util.sequential_name_generator import SequentialNameGenerator

from .syntax import (
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
    Term,
)

type Context = Mapping[str, str]


def uniqify_term(
    term: Term,
    context: Context,
    fresh: Callable[[str], str],
) -> Term:
    _term = partial(uniqify_term, context=context, fresh=fresh)

    match term:
        case Let(bindings=bindings, body=body):
            # Binding values are evaluated in the OUTER context
            new_values = [_term(val) for _, val in bindings]
            # Each binder gets a fresh unique name
            local = {name: fresh(name) for name, _ in bindings}
            new_context = {**context, **local}
            new_bindings = [(local[name], val) for (name, _), val in zip(bindings, new_values)]
            return Let(
                bindings=new_bindings,
                body=uniqify_term(body, new_context, fresh),
            )

        case LetRec(bindings=bindings, body=body):
            # All binders are in scope for BOTH the values and the body
            local = {name: fresh(name) for name, _ in bindings}
            new_context = {**context, **local}
            new_bindings = [
                (local[name], uniqify_term(val, new_context, fresh))
                for name, val in bindings
            ]
            return LetRec(
                bindings=new_bindings,
                body=uniqify_term(body, new_context, fresh),
            )

        case Reference(name=name):
            return Reference(name=context[name])

        case Abstract(parameters=parameters, body=body):
            local = {p: fresh(p) for p in parameters}
            new_context = {**context, **local}
            return Abstract(
                parameters=[local[p] for p in parameters],
                body=uniqify_term(body, new_context, fresh),
            )

        case Apply(target=target, arguments=arguments):
            return Apply(
                target=_term(target),
                arguments=[_term(arg) for arg in arguments],
            )

        case Immediate():
            return term

        case Primitive(operator=operator, left=left, right=right):
            return Primitive(operator=operator, left=_term(left), right=_term(right))

        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return Branch(
                operator=operator,
                left=_term(left),
                right=_term(right),
                consequent=_term(consequent),
                otherwise=_term(otherwise),
            )

        case Allocate():
            return term

        case Load(base=base, index=index):
            return Load(base=_term(base), index=index)

        case Store(base=base, index=index, value=value):
            return Store(base=_term(base), index=index, value=_term(value))

        case Begin(effects=effects, value=value):  # pragma: no branch
            return Begin(effects=[_term(e) for e in effects], value=_term(value))


def uniqify_program(
    program: Program,
) -> tuple[Callable[[str], str], Program]:
    fresh = SequentialNameGenerator()

    _term = partial(uniqify_term, fresh=fresh)

    match program:
        case Program(parameters=parameters, body=body):  # pragma: no branch
            local = {parameter: fresh(parameter) for parameter in parameters}
            return (
                fresh,
                Program(
                    parameters=[local[parameter] for parameter in parameters],
                    body=_term(body, local),
                ),
            )