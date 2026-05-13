from __future__ import annotations

from collections.abc import Callable, Sequence

from util.sequential_name_generator import SequentialNameGenerator

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


def desugar_cond_list(
    remaining: list[tuple[Term | None, Term]],
    fresh: Callable[[str], str],
) -> Term:
    if not remaining:
        return Immediate(value=0)
    (condition, body), *rest = remaining
    if condition is None:
        return desugar_term(body, fresh)
    return Branch(
        operator="!=",
        left=desugar_term(condition, fresh),
        right=Immediate(value=0),
        consequent=desugar_term(body, fresh),
        otherwise=desugar_cond_list(rest, fresh),
    )


def desugar_match(
    scrutinee: Term,
    clauses: Sequence[tuple[Pattern, Term]],
    fresh: Callable[[str], str],
) -> Term:
    if not clauses:
        return Immediate(value=0)
    s_name = fresh("s")
    body = desugar_clauses(Reference(name=s_name), list(clauses), fresh)
    return Let(
        bindings=[(s_name, desugar_term(scrutinee, fresh))],
        body=body,
    )


def desugar_clauses(
    s: Term,
    clauses: list[tuple[Pattern, Term]],
    fresh: Callable[[str], str],
) -> Term:
    if not clauses:
        return Immediate(value=0)

    (pattern, body), *rest = clauses
    rest_term = desugar_clauses(s, rest, fresh)

    match pattern:
        case IntPattern(value=n):
            return Branch(
                operator="==",
                left=s,
                right=Immediate(value=n),
                consequent=desugar_term(body, fresh),
                otherwise=rest_term,
            )

        case BoolPattern(value=True):
            return Branch(
                operator="!=",
                left=s,
                right=Immediate(value=0),
                consequent=desugar_term(body, fresh),
                otherwise=rest_term,
            )

        case BoolPattern(value=False):
            return Branch(
                operator="==",
                left=s,
                right=Immediate(value=0),
                consequent=desugar_term(body, fresh),
                otherwise=rest_term,
            )

        case NilPattern():
            return Branch(
                operator="==",
                left=s,
                right=Immediate(value=0),
                consequent=desugar_term(body, fresh),
                otherwise=rest_term,
            )

        case ConsPattern(head=h, tail=t):
            return Branch(
                operator="!=",
                left=s,
                right=Immediate(value=0),
                consequent=Let(
                    bindings=[
                        (h, Load(base=s, index=0)),
                        (t, Load(base=s, index=1)),
                    ],
                    body=desugar_term(body, fresh),
                ),
                otherwise=rest_term,
            )

        case TuplePattern(elements=names):
            bindings = [(name, Load(base=s, index=i)) for i, name in enumerate(names)]
            return Let(bindings=bindings, body=desugar_term(body, fresh))

        case WildcardPattern():
            return desugar_term(body, fresh)

        case NamePattern(name=name):  # pragma: no branch
            return Let(
                bindings=[(name, s)],
                body=desugar_term(body, fresh),
            )


def desugar_term(term: Term, fresh: Callable[[str], str]) -> Term:
    match term:
        case BoolLiteral(value=True):
            return Immediate(value=1)

        case BoolLiteral(value=False):
            return Immediate(value=0)

        case Not(operand=x):
            dx = desugar_term(x, fresh)
            return Branch(
                operator="==",
                left=dx,
                right=Immediate(value=0),
                consequent=Immediate(value=1),
                otherwise=Immediate(value=0),
            )

        case And(left=a, right=b):
            da = desugar_term(a, fresh)
            db = desugar_term(b, fresh)
            return Branch(
                operator="!=",
                left=da,
                right=Immediate(value=0),
                consequent=Branch(
                    operator="!=",
                    left=db,
                    right=Immediate(value=0),
                    consequent=Immediate(value=1),
                    otherwise=Immediate(value=0),
                ),
                otherwise=Immediate(value=0),
            )

        case Or(left=a, right=b):
            da = desugar_term(a, fresh)
            db = desugar_term(b, fresh)
            return Branch(
                operator="!=",
                left=da,
                right=Immediate(value=0),
                consequent=Immediate(value=1),
                otherwise=Branch(
                    operator="!=",
                    left=db,
                    right=Immediate(value=0),
                    consequent=Immediate(value=1),
                    otherwise=Immediate(value=0),
                ),
            )

        case Cond(clauses=clauses):
            return desugar_cond_list(list(clauses), fresh)

        case Div(left=a, right=b):
            return Primitive(
                operator="/",
                left=desugar_term(a, fresh),
                right=desugar_term(b, fresh),
            )

        case Mod(left=a, right=b):
            return Primitive(
                operator="%",
                left=desugar_term(a, fresh),
                right=desugar_term(b, fresh),
            )

        case GreaterThan(left=a, right=b):
            return Branch(
                operator="<",
                left=desugar_term(b, fresh),
                right=desugar_term(a, fresh),
                consequent=Immediate(value=1),
                otherwise=Immediate(value=0),
            )

        case GreaterThanOrEqual(left=a, right=b):
            return Branch(
                operator="<",
                left=desugar_term(a, fresh),
                right=desugar_term(b, fresh),
                consequent=Immediate(value=0),
                otherwise=Immediate(value=1),
            )

        case LessThanOrEqual(left=a, right=b):
            return Branch(
                operator="<",
                left=desugar_term(b, fresh),
                right=desugar_term(a, fresh),
                consequent=Immediate(value=0),
                otherwise=Immediate(value=1),
            )

        case NotEqual(left=a, right=b):
            return Branch(
                operator="==",
                left=desugar_term(a, fresh),
                right=desugar_term(b, fresh),
                consequent=Immediate(value=0),
                otherwise=Immediate(value=1),
            )

        case LessThan(left=a, right=b):
            return Branch(
                operator="<",
                left=desugar_term(a, fresh),
                right=desugar_term(b, fresh),
                consequent=Immediate(value=1),
                otherwise=Immediate(value=0),
            )

        case Match(scrutinee=scrutinee, clauses=clauses):
            return desugar_match(scrutinee, clauses, fresh)

        case Tuple(elements=elements):
            n = len(elements)
            t = fresh("t")
            desugared_elements = [desugar_term(e, fresh) for e in elements]
            stores = [Store(base=Reference(name=t), index=i, value=v) for i, v in enumerate(desugared_elements)]
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
