from collections.abc import Callable, Sequence
from functools import partial

from L1 import syntax as L1

from L2 import syntax as L2


def cps_convert_term(
    term: L2.Term,
    k: Callable[[L1.Identifier], L1.Statement],
    fresh: Callable[[str], str],
) -> L1.Statement:
    _term = partial(cps_convert_term, fresh=fresh)
    _terms = partial(cps_convert_terms, fresh=fresh)

    match term:
        case L2.Let(bindings=bindings, body=body):
            # Each binding (name, val) becomes a Copy/assignment in L1.
            # We evaluate each binding value, copy the result into `name`,
            # then continue with the remaining bindings and finally the body.
            def convert_bindings(
                remaining: list[tuple[L2.Identifier, L2.Term]],
            ) -> L1.Statement:
                if not remaining:
                    return _term(body, k)
                (name, val), *rest = remaining
                return _term(val, lambda src: L1.Copy(
                    destination=name,
                    source=src,
                    then=convert_bindings(rest),
                ))

            return convert_bindings(list(bindings))

        case L2.Reference(name=name):
            # A variable reference — just pass the name straight to k
            return k(name)

        case L2.Abstract(parameters=parameters, body=body):
            # A lambda becomes an L1.Abstract (a named function definition).
            # We add a continuation parameter "k..." to the parameter list.
            # Inside the body, instead of returning normally we call that k.
            k_name = fresh("k")
            dest = fresh("t")
            return L1.Abstract(
                destination=dest,
                parameters=[*parameters, k_name],
                body=_term(body, lambda result: L1.Apply(
                    target=k_name,
                    arguments=[result],
                )),
                then=k(dest),
            )

        case L2.Apply(target=target, arguments=arguments):
            # To call a CPS function we must first build a continuation closure
            # that captures "what to do with the return value", pass it as an
            # extra argument, then tail-call the function.
            k_name = fresh("k")
            result = fresh("t")
            return _terms([target, *arguments], lambda vals: L1.Abstract(
                destination=k_name,
                parameters=[result],
                body=k(result),
                then=L1.Apply(
                    target=vals[0],
                    arguments=[*vals[1:], k_name],
                ),
            ))

        case L2.Immediate(value=value):
            dest = fresh("t")
            return L1.Immediate(destination=dest, value=value, then=k(dest))

        case L2.Primitive(operator=operator, left=left, right=right):
            # Evaluate both operands, then emit the operation
            dest = fresh("t")
            return _terms([left, right], lambda vals: L1.Primitive(
                destination=dest,
                operator=operator,
                left=vals[0],
                right=vals[1],
                then=k(dest),
            ))

        case L2.Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            # Create a join-point continuation so both branches converge
            # to the same "rest of the program".
            j_name = fresh("j")
            result = fresh("t")
            return _terms([left, right], lambda vals: L1.Abstract(
                destination=j_name,
                parameters=[result],
                body=k(result),
                then=L1.Branch(
                    operator=operator,
                    left=vals[0],
                    right=vals[1],
                    then=_term(consequent, lambda v: L1.Apply(target=j_name, arguments=[v])),
                    otherwise=_term(otherwise, lambda v: L1.Apply(target=j_name, arguments=[v])),
                ),
            ))

        case L2.Allocate(count=count):
            dest = fresh("t")
            return L1.Allocate(destination=dest, count=count, then=k(dest))

        case L2.Load(base=base, index=index):
            dest = fresh("t")
            return _term(base, lambda b: L1.Load(
                destination=dest,
                base=b,
                index=index,
                then=k(dest),
            ))

        case L2.Store(base=base, index=index, value=value):
            # Store has no meaningful return value — emit a dummy Immediate(0)
            # after the store so k has something to receive.
            dummy = fresh("t")
            return _terms([base, value], lambda vals: L1.Store(
                base=vals[0],
                index=index,
                value=vals[1],
                then=L1.Immediate(destination=dummy, value=0, then=k(dummy)),
            ))

        case L2.Begin(effects=effects, value=value):  # pragma: no branch
            # Effects are evaluated for side effects only — their results are
            # discarded.  The value of the Begin is the last term.
            def convert_effects(remaining: list[L2.Term]) -> L1.Statement:
                if not remaining:
                    return _term(value, k)
                first, *rest = remaining
                return _term(first, lambda _: convert_effects(rest))

            return convert_effects(list(effects))


def cps_convert_terms(
    terms: Sequence[L2.Term],
    k: Callable[[Sequence[L1.Identifier]], L1.Statement],
    fresh: Callable[[str], str],
) -> L1.Statement:
    _term = partial(cps_convert_term, fresh=fresh)
    _terms = partial(cps_convert_terms, fresh=fresh)

    match terms:
        case []:
            return k([])

        case [first, *rest]:
            return _term(first, lambda first: _terms(rest, lambda rest: k([first, *rest])))

        case _:  # pragma: no cover
            raise ValueError(terms)


def cps_convert_program(
    program: L2.Program,
    fresh: Callable[[str], str],
) -> L1.Program:
    _term = partial(cps_convert_term, fresh=fresh)

    match program:
        case L2.Program(parameters=parameters, body=body):  # pragma: no branch
            return L1.Program(
                parameters=parameters,
                body=_term(body, lambda value: L1.Halt(value=value)),
            )