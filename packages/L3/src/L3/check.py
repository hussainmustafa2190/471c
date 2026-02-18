from collections.abc import Mapping
from functools import partial

from .syntax import (
    Abstract, Allocate, Apply, Begin, Branch, Identifier, 
    Immediate, Let, LetRec, Load, Primitive, Reference, Store, Term,
)

type Context = Mapping[Identifier, None]

def check_term(term: Term, context: Context) -> None:
    recur = partial(check_term, context=context)

    match term:
        case Let(bindings=bindings, body=body):
            current_ctx = context
            for var, val in bindings:
                check_term(val, current_ctx) 
                current_ctx = current_ctx | {var: None} 
            check_term(body, current_ctx)

        case LetRec(bindings=bindings, body=body):
            new_context = context | {var: None for var, _ in bindings}
            for _, val in bindings:
                check_term(val, new_context)
            check_term(body, new_context)

        case Reference(name=name):
            if name not in context:
                raise NameError(f"Unbound identifier: {name}")

        case Abstract(parameters=parameters, body=body):
            check_term(body, context | {p: None for p in parameters})

        case Apply(target=target, arguments=arguments):
            recur(target)
            for arg in arguments:
                recur(arg)

        case Immediate(value=value):
            pass

        case Primitive(operator=_, left=left, right=right):
            recur(left)
            recur(right)

        case Branch(operator=_, left=left, right=right, consequent=consequent, otherwise=otherwise):
            recur(left)
            recur(right)
            recur(consequent)
            recur(otherwise)

        case Allocate(count=value):
            pass

        case Load(base=base, index=_):
            recur(base)

        case Store(base=base, index=_, value=value):
            recur(base)
            recur(value)

        case Begin(effects=effects, value=value):
            for e in effects:
                recur(e)
            recur(value)