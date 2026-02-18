from collections.abc import Mapping
from functools import partial

from .syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Identifier,
    Immediate,
    Let,
    LetRec,
    Load,
    Primitive,
    Reference,
    Store,
    Term,
)

type Context = Mapping[Identifier, None]


def check_term(
    term: Term,
    context: Context,
) -> None:
    recur = partial(check_term, context=context)

    match term:
        case Let(variable, value, body):
            recur(value)
            check_term(body, context | {variable: None})

        case LetRec(bindings, body):
            new_context = context | {var: None for var, _ in bindings}
            for _, val in bindings:
                check_term(val, new_context)
            check_term(body, new_context)

        case Reference(identifier):
            if identifier not in context:
                raise NameError(f"Unbound identifier: {identifier}")

        case Abstract(parameters, body):
            new_context = context | {p: None for p in parameters}
            check_term(body, new_context)

        case Apply(function, arguments):
            recur(function)
            for arg in arguments:
                recur(arg)

        case Immediate():
            pass

        case Primitive(_, arguments):
            for arg in arguments:
                recur(arg)

        case Branch(condition, then_term, else_term):
            recur(condition)
            recur(then_term)
            recur(else_term)

        case Allocate(items):
            for item in items:
                recur(item)

        case Load(collection, index):
            recur(collection)
            recur(index)

        case Store(collection, index, value):
            recur(collection)
            recur(index)
            recur(value)

        case Begin(terms):
            for t in terms:
                recur(t)