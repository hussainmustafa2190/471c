from collections.abc import Mapping, Sequence
from functools import partial

from .syntax import (
    Abstract, Allocate, Apply, Begin, Branch, Identifier, 
    Immediate, Let, LetRec, Load, Primitive, Program, Reference, Store, Term,
)

type Context = Mapping[Identifier, None]

def check_term(term: Term, context: Context) -> None:
    recur = partial(check_term, context=context)

    match term:
        case Let(bindings=bindings, body=body):
            binders = [b[0] for b in bindings]
            if len(set(binders)) != len(binders):
                raise ValueError("Duplicate binders in Let")
            for _, val in bindings:
                check_term(val, context)
            check_term(body, context | {var: None for var, _ in bindings})

        case LetRec(bindings=bindings, body=body):
            binders = [b[0] for b in bindings]
            if len(set(binders)) != len(binders):
                raise ValueError("Duplicate binders in LetRec")
            
            new_context = context | {var: None for var, _ in bindings}
            for _, val in bindings:
                check_term(val, new_context)
            check_term(body, new_context)

        case Reference(name=name):
            if name not in context:
                raise ValueError(f"Unbound identifier: {name}")

        case Abstract(parameters=parameters, body=body):
            if len(set(parameters)) != len(parameters):
                raise ValueError("Duplicate parameters in Abstract")
            check_term(body, context | {p: None for p in parameters})

        case Apply(target=target, arguments=arguments):
            recur(target)
            for arg in arguments:
                recur(arg)

        case Immediate():
            pass

        case Primitive(operator=_, left=left, right=right):
            recur(left)
            recur(right)

        case Branch(operator=_, left=left, right=right, consequent=consequent, otherwise=otherwise):
            recur(left)
            recur(right)
            recur(consequent)
            recur(otherwise)

        case Allocate(count=_):
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
        
        case _:
            raise ValueError(f"Unknown term: {type(term)}")

def check_program(program: Program) -> None:
    # Check for duplicate top-level parameters
    if len(set(program.parameters)) != len(program.parameters):
        raise ValueError("Duplicate parameters in program")
    
    context = {p: None for p in program.parameters}
    check_term(program.body, context)