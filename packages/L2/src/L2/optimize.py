from .syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Identifier,
    Immediate,
    Let,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
    Term,
)


class ConstantPropagation:
    """Constant propagation + constant folding.

    Propagation: a Let binding whose value is an Immediate (literal number)
    or a Reference (just another name) is inlined at every use site and the
    binding is dropped.

    Folding: after propagation pushes Immediates into Primitive / Branch nodes,
    we evaluate them at compile time instead of leaving the work for runtime.
    """

    # ------------------------------------------------------------------
    # Substitution helper: replace every free occurrence of `name` with
    # `replacement` inside `term`, respecting shadowing by inner binders.
    # ------------------------------------------------------------------

    def _subst(self, term: Term, name: Identifier, replacement: Term) -> Term:
        def recur(t: Term) -> Term:
            return self._subst(t, name, replacement)

        match term:
            case Reference(name=n) if n == name:
                return replacement

            case Reference():
                return term

            case Immediate() | Allocate():
                return term

            case Let(bindings=bindings, body=body):
                new_bindings = []
                shadowed = False
                for n, v in bindings:
                    new_bindings.append((n, recur(v)))
                    if n == name:
                        shadowed = True
                        new_bindings += [(bn, bv) for bn, bv in list(bindings)[len(new_bindings):]]
                        break
                new_body = body if shadowed else recur(body)
                return Let(bindings=new_bindings, body=new_body)

            case Abstract(parameters=parameters, body=body):
                if name in parameters:
                    return term
                return Abstract(parameters=parameters, body=recur(body))

            case Apply(target=target, arguments=arguments):
                return Apply(target=recur(target), arguments=[recur(a) for a in arguments])

            case Primitive(operator=op, left=left, right=right):
                return Primitive(operator=op, left=recur(left), right=recur(right))

            case Branch(operator=op, left=left, right=right, consequent=consequent, otherwise=otherwise):
                return Branch(operator=op, left=recur(left), right=recur(right),
                              consequent=recur(consequent), otherwise=recur(otherwise))

            case Load(base=base, index=index):
                return Load(base=recur(base), index=index)

            case Store(base=base, index=index, value=value):
                return Store(base=recur(base), index=index, value=recur(value))

            case Begin(effects=effects, value=value):  # pragma: no branch
                return Begin(effects=[recur(e) for e in effects], value=recur(value))

    # ------------------------------------------------------------------
    # Folding: Primitive / Branch with two known Immediates → compute now.
    # ------------------------------------------------------------------

    def _fold(self, term: Term) -> Term:
        match term:
            case Primitive(operator=op, left=Immediate(value=lv), right=Immediate(value=rv)):
                if op == "+":
                    return Immediate(value=lv + rv)
                elif op == "-":
                    return Immediate(value=lv - rv)
                else:
                    return Immediate(value=lv * rv)

            case Branch(operator=op, left=Immediate(value=lv), right=Immediate(value=rv),
                        consequent=consequent, otherwise=otherwise):
                result = (lv < rv) if op == "<" else (lv == rv)
                return self.run(consequent) if result else self.run(otherwise)

        return term

    # ------------------------------------------------------------------
    # Main recursive pass.
    # ------------------------------------------------------------------

    def run(self, term: Term) -> Term:
        match term:
            case Let(bindings=bindings, body=body):
                new_body = self.run(body)

                # inlined maps name → constant value for everything we've inlined so far
                inlined: dict[str, Term] = {}
                surviving = []

                for n, v in bindings:
                    # Apply any already-inlined constants into this binding's value
                    for prev_n, prev_v in inlined.items():
                        v = self._subst(v, prev_n, prev_v)
                    new_v = self.run(v)
                    if isinstance(new_v, (Immediate, Reference)):
                        inlined[n] = new_v
                        new_body = self._subst(new_body, n, new_v)
                    else:
                        surviving.append((n, new_v))

                # After all substitutions, the body may now be foldable
                new_body = self._fold(new_body)

                if not surviving:
                    return new_body
                return Let(bindings=surviving, body=new_body)

            case Abstract(parameters=parameters, body=body):
                return Abstract(parameters=parameters, body=self.run(body))

            case Apply(target=target, arguments=arguments):
                return Apply(target=self.run(target), arguments=[self.run(a) for a in arguments])

            case Primitive(operator=op, left=left, right=right):
                folded = self._fold(Primitive(operator=op, left=self.run(left), right=self.run(right)))
                return folded

            case Branch(operator=op, left=left, right=right, consequent=consequent, otherwise=otherwise):
                folded = self._fold(Branch(operator=op, left=self.run(left), right=self.run(right),
                                           consequent=consequent, otherwise=otherwise))
                if isinstance(folded, Branch):
                    return Branch(operator=folded.operator, left=folded.left, right=folded.right,
                                  consequent=self.run(folded.consequent),
                                  otherwise=self.run(folded.otherwise))
                return folded

            case Load(base=base, index=index):
                return Load(base=self.run(base), index=index)

            case Store(base=base, index=index, value=value):
                return Store(base=self.run(base), index=index, value=self.run(value))

            case Begin(effects=effects, value=value):
                return Begin(effects=[self.run(e) for e in effects], value=self.run(value))

            case _:  # Immediate, Reference, Allocate
                return term


class DeadCodeElimination:
    """Dead code elimination.

    A Let binding whose name is never used in the body is dead and can be
    removed — but only when the bound expression is pure (no side effects).
    Pure expressions: Immediate, Reference, Allocate, Primitive, Load, Abstract.
    Apply and Store are kept because they may have observable side effects.
    """

    def _free_names(self, term: Term) -> frozenset[Identifier]:
        match term:
            case Reference(name=name):
                return frozenset({name})

            case Immediate() | Allocate():
                return frozenset()

            case Let(bindings=bindings, body=body):
                bound = frozenset(n for n, _ in bindings)
                from_values = frozenset().union(*(self._free_names(v) for _, v in bindings))
                from_body = self._free_names(body) - bound
                return from_values | from_body

            case Abstract(parameters=parameters, body=body):
                return self._free_names(body) - frozenset(parameters)

            case Apply(target=target, arguments=arguments):
                return self._free_names(target) | frozenset().union(*(self._free_names(a) for a in arguments))

            case Primitive(left=left, right=right):
                return self._free_names(left) | self._free_names(right)

            case Branch(left=left, right=right, consequent=consequent, otherwise=otherwise):
                return (self._free_names(left) | self._free_names(right)
                        | self._free_names(consequent) | self._free_names(otherwise))

            case Load(base=base):
                return self._free_names(base)

            case Store(base=base, value=value):
                return self._free_names(base) | self._free_names(value)

            case Begin(effects=effects, value=value):  # pragma: no branch
                return frozenset().union(*(self._free_names(e) for e in effects)) | self._free_names(value)

    def _is_pure(self, term: Term) -> bool:
        match term:
            case Immediate() | Reference() | Allocate():
                return True
            case Primitive(left=left, right=right):
                return self._is_pure(left) and self._is_pure(right)
            case Load(base=base):
                return self._is_pure(base)
            case Abstract():
                return True
            case _:
                return False

    def run(self, term: Term) -> Term:
        match term:
            case Let(bindings=bindings, body=body):
                new_body = self.run(body)
                used = self._free_names(new_body)

                surviving = []
                for n, v in bindings:
                    new_v = self.run(v)
                    if n not in used and self._is_pure(new_v):
                        pass  # dead — drop it
                    else:
                        surviving.append((n, new_v))
                        used = used | self._free_names(new_v)

                if not surviving:
                    return new_body
                return Let(bindings=surviving, body=new_body)

            case Abstract(parameters=parameters, body=body):
                return Abstract(parameters=parameters, body=self.run(body))

            case Apply(target=target, arguments=arguments):
                return Apply(target=self.run(target), arguments=[self.run(a) for a in arguments])

            case Primitive(operator=op, left=left, right=right):
                return Primitive(operator=op, left=self.run(left), right=self.run(right))

            case Branch(operator=op, left=left, right=right, consequent=consequent, otherwise=otherwise):
                return Branch(operator=op, left=self.run(left), right=self.run(right),
                              consequent=self.run(consequent), otherwise=self.run(otherwise))

            case Load(base=base, index=index):
                return Load(base=self.run(base), index=index)

            case Store(base=base, index=index, value=value):
                return Store(base=self.run(base), index=index, value=self.run(value))

            case Begin(effects=effects, value=value):
                return Begin(effects=[self.run(e) for e in effects], value=self.run(value))

            case _:  # Immediate, Reference, Allocate
                return term


# ---------------------------------------------------------------------------
# Top-level: run both passes in a loop until nothing changes
# ---------------------------------------------------------------------------

def optimize_program(
    program: Program,
) -> Program:
    cp = ConstantPropagation()
    dce = DeadCodeElimination()

    body = program.body
    while True:
        optimized = dce.run(cp.run(body))
        if optimized == body:
            break
        body = optimized

    return Program(
        parameters=program.parameters,
        body=body,
    )