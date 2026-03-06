from collections.abc import Sequence
from pathlib import Path

from lark import Lark, Token, Transformer
from lark.visitors import v_args  # pyright: ignore[reportUnknownVariableType]

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

_TERM_TYPES = (Let, LetRec, Reference, Abstract, Apply, Immediate, Primitive, Branch, Allocate, Load, Store, Begin)


class AstTransformer(Transformer[Token, Program | Term]):
    @v_args(inline=True)
    def program(
        self,
        parameters: Sequence[Identifier],
        body: Term,
    ) -> Program:
        return Program(parameters=parameters, body=body)

    def parameters(
        self,
        params: list[Token],
    ) -> Sequence[Identifier]:
        return [str(p) for p in params]

    @v_args(inline=True)
    def term(
        self,
        t: Term,
    ) -> Term:
        return t

    @v_args(inline=True)
    def let(
        self,
        bindings: Sequence[tuple[Identifier, Term]],
        body: Term,
    ) -> Term:
        return Let(bindings=bindings, body=body)

    @v_args(inline=True)
    def letrec(
        self,
        bindings: Sequence[tuple[Identifier, Term]],
        body: Term,
    ) -> Term:
        return LetRec(bindings=bindings, body=body)

    def bindings(
        self,
        bs: list[tuple[Identifier, Term]],
    ) -> Sequence[tuple[Identifier, Term]]:
        return bs

    @v_args(inline=True)
    def binding(
        self,
        name: Token,
        value: Term,
    ) -> tuple[Identifier, Term]:
        return str(name), value

    @v_args(inline=True)
    def reference(
        self,
        name: Token,
    ) -> Term:
        return Reference(name=str(name))

    def abstract(
        self,
        children: list[object],
    ) -> Term:
        # LAMBDA is a named terminal — it may survive filtering depending on
        # the Lark parser backend, so we locate children by type rather than
        # relying on position.
        params: Sequence[Identifier] = next(c for c in children if isinstance(c, list))  # pyright: ignore[reportAssignmentType]
        body: Term = next(c for c in children if isinstance(c, _TERM_TYPES))  # pyright: ignore[reportAssignmentType]
        return Abstract(parameters=params, body=body)

    def apply(
        self,
        children: list[Term],
    ) -> Term:
        return Apply(target=children[0], arguments=children[1:])

    @v_args(inline=True)
    def immediate(
        self,
        value: Token,
    ) -> Term:
        return Immediate(value=int(value))

    @v_args(inline=True)
    def primitive(
        self,
        operator: Token,
        left: Term,
        right: Term,
    ) -> Term:
        return Primitive(
            operator=str(operator),  # pyright: ignore[reportArgumentType]
            left=left,
            right=right,
        )

    @v_args(inline=True)
    def branch(
        self,
        comparator: Token,
        left: Term,
        right: Term,
        consequent: Term,
        otherwise: Term,
    ) -> Term:
        return Branch(
            operator=str(comparator),  # pyright: ignore[reportArgumentType]
            left=left,
            right=right,
            consequent=consequent,
            otherwise=otherwise,
        )

    @v_args(inline=True)
    def allocate(
        self,
        count: Token,
    ) -> Term:
        return Allocate(count=int(count))

    @v_args(inline=True)
    def load(
        self,
        base: Term,
        index: Token,
    ) -> Term:
        return Load(base=base, index=int(index))

    @v_args(inline=True)
    def store(
        self,
        base: Term,
        index: Token,
        value: Term,
    ) -> Term:
        return Store(base=base, index=int(index), value=value)

    def begin(
        self,
        children: list[Term],
    ) -> Term:
        return Begin(effects=children[:-1], value=children[-1])


def parse_term(source: str) -> Term:
    grammar = Path(__file__).with_name("L3.lark").read_text()
    parser = Lark(grammar, parser="lalr", start="term")
    tree = parser.parse(source)  # pyright: ignore[reportUnknownMemberType]
    return AstTransformer().transform(tree)  # pyright: ignore[reportReturnType]


def parse_program(source: str) -> Program:
    grammar = Path(__file__).with_name("L3.lark").read_text()
    parser = Lark(grammar, parser="lalr", start="program")
    tree = parser.parse(source)  # pyright: ignore[reportUnknownMemberType]
    return AstTransformer().transform(tree)  # pyright: ignore[reportReturnType]
