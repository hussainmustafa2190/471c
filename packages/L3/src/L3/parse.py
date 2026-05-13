from collections.abc import Sequence
from pathlib import Path

from lark import Lark, Token, Transformer
from lark.visitors import v_args  # pyright: ignore[reportUnknownVariableType]

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
    Cons,
    ConsPattern,
    Cond,
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
    Primitive,
    Program,
    Reference,
    Store,
    Term,
    Tuple,
    TuplePattern,
    TupleRef,
    WildcardPattern,
    Pattern,
)

_PATTERN_TYPES = (
    IntPattern,
    BoolPattern,
    NilPattern,
    ConsPattern,
    TuplePattern,
    WildcardPattern,
    NamePattern,
)

_TERM_TYPES = (
    Let,
    LetRec,
    Reference,
    Abstract,
    Apply,
    Immediate,
    Primitive,
    Branch,
    BoolLiteral,
    And,
    Or,
    Not,
    Cond,
    Div,
    Mod,
    LessThan,
    GreaterThan,
    GreaterThanOrEqual,
    LessThanOrEqual,
    NotEqual,
    Match,
    Allocate,
    Load,
    Store,
    Begin,
    Tuple,
    TupleRef,
    Cons,
    Nil,
    Car,
    Cdr,
    IsNil,
    ListLiteral,
)


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

    def tuple_term(
        self,
        children: list[object],
    ) -> Term:
        elements = [c for c in children if isinstance(c, _TERM_TYPES)]
        return Tuple(elements=elements)

    @v_args(inline=True)
    def tuple_ref_term(
        self,
        _tuple_ref: Token,
        base: Term,
        index: Token,
    ) -> Term:
        return TupleRef(base=base, index=int(index))

    @v_args(inline=True)
    def cons_term(
        self,
        head: Term,
        tail: Term,
    ) -> Term:
        return Cons(head=head, tail=tail)

    @v_args(inline=True)
    def nil_term(
        self,
        _nil: Token,
    ) -> Term:
        return Nil()

    @v_args(inline=True)
    def car_term(
        self,
        base: Term,
    ) -> Term:
        return Car(base=base)

    @v_args(inline=True)
    def cdr_term(
        self,
        base: Term,
    ) -> Term:
        return Cdr(base=base)

    @v_args(inline=True)
    def is_nil_term(
        self,
        _nullp: Token,
        base: Term,
    ) -> Term:
        return IsNil(base=base)

    def list_term(
        self,
        children: list[object],
    ) -> Term:
        elements = [c for c in children if isinstance(c, _TERM_TYPES)]
        return ListLiteral(elements=elements)

    @v_args(inline=True)
    def true_term(
        self,
        _t: Token,
    ) -> Term:
        return BoolLiteral(value=True)

    @v_args(inline=True)
    def false_term(
        self,
        _t: Token,
    ) -> Term:
        return BoolLiteral(value=False)

    def and_term(
        self,
        children: list[object],
    ) -> Term:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        assert len(terms) == 2
        return And(left=terms[0], right=terms[1])

    def or_term(
        self,
        children: list[object],
    ) -> Term:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        assert len(terms) == 2
        return Or(left=terms[0], right=terms[1])

    def not_term(
        self,
        children: list[object],
    ) -> Term:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        assert len(terms) == 1
        return Not(operand=terms[0])

    @v_args(inline=True)
    def cond_clause_normal(
        self,
        cond: Term,
        body: Term,
    ) -> tuple[Term | None, Term]:
        return (cond, body)

    def cond_clause_else(
        self,
        children: list[object],
    ) -> tuple[Term | None, Term]:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        assert len(terms) == 1
        return (None, terms[0])

    def cond_clauses(
        self,
        clauses: list[tuple[Term | None, Term]],
    ) -> list[tuple[Term | None, Term]]:
        return clauses

    def cond_term(
        self,
        children: list[object],
    ) -> Term:
        clauses: list[tuple[Term | None, Term]] = []
        for c in children:
            if isinstance(c, list):
                clauses.extend(c)
        return Cond(clauses=clauses)

    def div_term(
        self,
        children: list[object],
    ) -> Term:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        assert len(terms) == 2
        return Div(left=terms[0], right=terms[1])

    def mod_term(
        self,
        children: list[object],
    ) -> Term:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        assert len(terms) == 2
        return Mod(left=terms[0], right=terms[1])

    def gt_term(
        self,
        children: list[object],
    ) -> Term:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        assert len(terms) == 2
        return GreaterThan(left=terms[0], right=terms[1])

    def gte_term(
        self,
        children: list[object],
    ) -> Term:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        assert len(terms) == 2
        return GreaterThanOrEqual(left=terms[0], right=terms[1])

    def lte_term(
        self,
        children: list[object],
    ) -> Term:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        assert len(terms) == 2
        return LessThanOrEqual(left=terms[0], right=terms[1])

    def neq_term(
        self,
        children: list[object],
    ) -> Term:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        assert len(terms) == 2
        return NotEqual(left=terms[0], right=terms[1])

    def lt_term(
        self,
        children: list[object],
    ) -> Term:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        assert len(terms) == 2
        return LessThan(left=terms[0], right=terms[1])

    @v_args(inline=True)
    def int_pattern(
        self,
        value: Token,
    ) -> IntPattern:
        return IntPattern(value=int(value))

    def bool_pattern(
        self,
        children: list[object],
    ) -> BoolPattern:
        tok = next(c for c in children if isinstance(c, Token))
        return BoolPattern(value=str(tok) == "true")

    @v_args(inline=True)
    def nil_pattern(
        self,
        _nil: Token,
    ) -> NilPattern:
        return NilPattern()

    def cons_pattern(
        self,
        children: list[object],
    ) -> ConsPattern:
        names = [str(c) for c in children if isinstance(c, Token) and c.type == "PATNAME"]
        assert len(names) == 2
        return ConsPattern(head=names[0], tail=names[1])

    def tuple_pattern(
        self,
        children: list[object],
    ) -> TuplePattern:
        names = [str(c) for c in children if isinstance(c, Token) and c.type == "PATNAME"]
        return TuplePattern(elements=names)

    @v_args(inline=True)
    def wildcard_pattern(
        self,
        _w: Token,
    ) -> WildcardPattern:
        return WildcardPattern()

    @v_args(inline=True)
    def name_pattern(
        self,
        name: Token,
    ) -> NamePattern:
        return NamePattern(name=str(name))

    def pattern(
        self,
        children: list[object],
    ) -> Pattern:
        return next(c for c in children if isinstance(c, _PATTERN_TYPES))

    def match_clause(
        self,
        children: list[object],
    ) -> tuple[Pattern, Term]:
        pat = next(c for c in children if isinstance(c, _PATTERN_TYPES))
        body = next(c for c in children if isinstance(c, _TERM_TYPES))
        return (pat, body)

    def match_term(
        self,
        children: list[object],
    ) -> Term:
        terms = [c for c in children if isinstance(c, _TERM_TYPES)]
        clauses = [c for c in children if isinstance(c, tuple) and len(c) == 2]
        return Match(scrutinee=terms[0], clauses=clauses)


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
