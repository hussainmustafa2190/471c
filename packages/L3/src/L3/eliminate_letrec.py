import L2.syntax as L2

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
    Program,
    Reference,
    Store,
    Term,
)


def _subst(term: Term, names: frozenset[Identifier]) -> Term:
    if not names:
        return term

    match term:
        case Reference(name=name) if name in names:
            return Load(base=Reference(name=name), index=0)

        case Reference():
            return term

        case Immediate():
            return term

        case Allocate():
            return term

        case Let(bindings=bindings, body=body):
            new_bindings = [(n, _subst(val, names)) for n, val in bindings]
            shadowed = names - {n for n, _ in bindings}
            return Let(bindings=new_bindings, body=_subst(body, shadowed))

        case LetRec(bindings=bindings, body=body):
            shadowed = names - {n for n, _ in bindings}
            new_bindings = [(n, _subst(val, shadowed)) for n, val in bindings]
            return LetRec(bindings=new_bindings, body=_subst(body, shadowed))

        case Abstract(parameters=parameters, body=body):
            shadowed = names - set(parameters)
            return Abstract(parameters=parameters, body=_subst(body, shadowed))

        case Apply(target=target, arguments=arguments):
            return Apply(target=_subst(target, names), arguments=[_subst(arg, names) for arg in arguments])

        case Primitive(operator=operator, left=left, right=right):
            return Primitive(operator=operator, left=_subst(left, names), right=_subst(right, names))

        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return Branch(
                operator=operator,
                left=_subst(left, names),
                right=_subst(right, names),
                consequent=_subst(consequent, names),
                otherwise=_subst(otherwise, names),
            )

        case Load(base=base, index=index):
            return Load(base=_subst(base, names), index=index)

        case Store(base=base, index=index, value=value):
            return Store(base=_subst(base, names), index=index, value=_subst(value, names))

        case Begin(effects=effects, value=value):  # pragma: no branch
            return Begin(effects=[_subst(e, names) for e in effects], value=_subst(value, names))


def eliminate_letrec_term(term: Term) -> L2.Term:
    recur = eliminate_letrec_term

    match term:
        case LetRec(bindings=bindings, body=body):
            if not bindings:
                return recur(body)

            names = frozenset(n for n, _ in bindings)
            subst_values = [_subst(val, names) for _, val in bindings]
            subst_body = _subst(body, names)

            alloc_bindings: list[tuple[Identifier, L2.Term]] = [(n, L2.Allocate(count=1)) for n, _ in bindings]

            stores: list[L2.Term] = [
                L2.Store(base=L2.Reference(name=n), index=0, value=recur(sv))
                for (n, _), sv in zip(bindings, subst_values)
            ]

            return L2.Let(bindings=alloc_bindings, body=L2.Begin(effects=stores, value=recur(subst_body)))

        case Let(bindings=bindings, body=body):
            return L2.Let(bindings=[(n, recur(val)) for n, val in bindings], body=recur(body))

        case Reference(name=name):
            return L2.Reference(name=name)

        case Abstract(parameters=parameters, body=body):
            return L2.Abstract(parameters=list(parameters), body=recur(body))

        case Apply(target=target, arguments=arguments):
            return L2.Apply(target=recur(target), arguments=[recur(arg) for arg in arguments])

        case Immediate(value=value):
            return L2.Immediate(value=value)

        case Primitive(operator=operator, left=left, right=right):
            return L2.Primitive(operator=operator, left=recur(left), right=recur(right))

        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return L2.Branch(
                operator=operator,
                left=recur(left),
                right=recur(right),
                consequent=recur(consequent),
                otherwise=recur(otherwise),
            )

        case Allocate(count=count):
            return L2.Allocate(count=count)

        case Load(base=base, index=index):
            return L2.Load(base=recur(base), index=index)

        case Store(base=base, index=index, value=value):
            return L2.Store(base=recur(base), index=index, value=recur(value))

        case Begin(effects=effects, value=value):  # pragma: no branch
            return L2.Begin(effects=[recur(e) for e in effects], value=recur(value))


def eliminate_letrec_program(program: Program) -> L2.Program:
    return L2.Program(parameters=list(program.parameters), body=eliminate_letrec_term(program.body))
