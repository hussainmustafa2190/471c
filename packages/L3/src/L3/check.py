from collections.abc import Mapping
from functools import partial

from .syntax import (
    Abstract,
    Allocate,
    And,
    Apply,
    Begin,
    BoolLiteral,
    BoolPattern,
    Branch,
    Car,
    Cdr,
    Cond,
    Cons,
    ConsPattern,
    Div,
    GreaterThan,
    GreaterThanOrEqual,
    Identifier,
    Immediate,
    IntPattern,
    IsNil,
    Let,
    LetRec,
    LessThan,
    LessThanOrEqual,
    ListLiteral,
    Load,
    Match,
    Mod,
    NamePattern,
    Nil,
    NilPattern,
    Not,
    NotEqual,
    Or,
    Pattern,
    Primitive,
    Program,
    Reference,
    Store,
    Term,
    Tuple,
    TuplePattern,
    TupleRef,
    WildcardPattern,
)

type Context = Mapping[Identifier, None]


def _pattern_binders(pattern: Pattern) -> frozenset[Identifier]:
    match pattern:
        case ConsPattern(head=h, tail=t):
            return frozenset({h, t})
        case TuplePattern(elements=names):
            return frozenset(names)
        case NamePattern(name=name):
            return frozenset({name})
        case IntPattern() | BoolPattern() | NilPattern() | WildcardPattern():  # pragma: no branch
            return frozenset()


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

        case Primitive(operator=_, left=left, right=right):
            recur(left)
            recur(right)

        case Branch(operator=_, left=left, right=right, consequent=consequent, otherwise=otherwise):
            recur(left)
            recur(right)
            recur(consequent)
            recur(otherwise)

        case Immediate():
            pass

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

        case BoolLiteral() | Nil():
            pass

        case And(left=left, right=right) | Or(left=left, right=right):
            recur(left)
            recur(right)

        case Not(operand=operand):
            recur(operand)

        case Cond(clauses=clauses):
            for cond, body in clauses:
                if cond is not None:
                    recur(cond)
                recur(body)

        case Div(left=left, right=right) | Mod(left=left, right=right):
            recur(left)
            recur(right)

        case LessThan(left=left, right=right) | GreaterThan(left=left, right=right):
            recur(left)
            recur(right)

        case GreaterThanOrEqual(left=left, right=right) | LessThanOrEqual(left=left, right=right) | NotEqual(
            left=left,
            right=right,
        ):
            recur(left)
            recur(right)

        case Match(scrutinee=scrutinee, clauses=clauses):
            recur(scrutinee)
            for pat, body in clauses:
                check_term(body, context | {b: None for b in _pattern_binders(pat)})

        case Tuple(elements=elements):
            for e in elements:
                recur(e)

        case TupleRef(base=base, index=_):
            recur(base)

        case Cons(head=head, tail=tail):
            recur(head)
            recur(tail)

        case Car(base=base) | Cdr(base=base) | IsNil(base=base):
            recur(base)

        case ListLiteral(elements=elements):
            for e in elements:
                recur(e)

        case _:  # pragma: no branch
            raise ValueError(f"Unknown term: {type(term)}")


def check_program(program: Program) -> None:
    if len(set(program.parameters)) != len(program.parameters):
        raise ValueError("Duplicate parameters in program")

    context = {p: None for p in program.parameters}
    check_term(program.body, context)
