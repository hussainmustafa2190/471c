from collections.abc import Sequence
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

type Identifier = Annotated[str, Field(min_length=1)]

type Nat = Annotated[int, Field(ge=0)]


class Program(BaseModel, frozen=True):
    tag: Literal["l3"] = "l3"
    parameters: Sequence[Identifier]
    body: "Term"


class Let(BaseModel, frozen=True):
    tag: Literal["let"] = "let"
    bindings: Sequence[tuple[Identifier, "Term"]]
    body: "Term"


class LetRec(BaseModel, frozen=True):
    tag: Literal["letrec"] = "letrec"
    bindings: Sequence[tuple[Identifier, "Term"]]
    body: "Term"


class Reference(BaseModel, frozen=True):
    tag: Literal["reference"] = "reference"
    name: Identifier


class Abstract(BaseModel, frozen=True):
    tag: Literal["abstract"] = "abstract"
    parameters: Sequence[Identifier]
    body: "Term"


class Apply(BaseModel, frozen=True):
    tag: Literal["apply"] = "apply"
    target: "Term"
    arguments: Sequence["Term"]


class Immediate(BaseModel, frozen=True):
    tag: Literal["immediate"] = "immediate"
    value: int


class Primitive(BaseModel, frozen=True):
    tag: Literal["primitive"] = "primitive"
    operator: Literal["+", "-", "*", "/", "%"]
    left: "Term"
    right: "Term"


class Branch(BaseModel, frozen=True):
    tag: Literal["branch"] = "branch"
    operator: Literal["<", "==", ">", ">=", "<=", "!="]
    left: "Term"
    right: "Term"
    consequent: "Term"
    otherwise: "Term"


class BoolLiteral(BaseModel, frozen=True):
    tag: Literal["bool"] = "bool"
    value: bool


class And(BaseModel, frozen=True):
    tag: Literal["and"] = "and"
    left: "Term"
    right: "Term"


class Or(BaseModel, frozen=True):
    tag: Literal["or"] = "or"
    left: "Term"
    right: "Term"


class Not(BaseModel, frozen=True):
    tag: Literal["not"] = "not"
    operand: "Term"


class Cond(BaseModel, frozen=True):
    tag: Literal["cond"] = "cond"
    clauses: Sequence[tuple[Optional["Term"], "Term"]]


class Div(BaseModel, frozen=True):
    tag: Literal["div"] = "div"
    left: "Term"
    right: "Term"


class Mod(BaseModel, frozen=True):
    tag: Literal["mod"] = "mod"
    left: "Term"
    right: "Term"


class GreaterThan(BaseModel, frozen=True):
    tag: Literal["gt"] = "gt"
    left: "Term"
    right: "Term"


class GreaterThanOrEqual(BaseModel, frozen=True):
    tag: Literal["gte"] = "gte"
    left: "Term"
    right: "Term"


class LessThanOrEqual(BaseModel, frozen=True):
    tag: Literal["lte"] = "lte"
    left: "Term"
    right: "Term"


class NotEqual(BaseModel, frozen=True):
    tag: Literal["neq"] = "neq"
    left: "Term"
    right: "Term"


class LessThan(BaseModel, frozen=True):
    tag: Literal["lt"] = "lt"
    left: "Term"
    right: "Term"


class IntPattern(BaseModel, frozen=True):
    tag: Literal["int-pattern"] = "int-pattern"
    value: int


class BoolPattern(BaseModel, frozen=True):
    tag: Literal["bool-pattern"] = "bool-pattern"
    value: bool


class NilPattern(BaseModel, frozen=True):
    tag: Literal["nil-pattern"] = "nil-pattern"


class ConsPattern(BaseModel, frozen=True):
    tag: Literal["cons-pattern"] = "cons-pattern"
    head: Identifier
    tail: Identifier


class TuplePattern(BaseModel, frozen=True):
    tag: Literal["tuple-pattern"] = "tuple-pattern"
    elements: Sequence[Identifier]


class WildcardPattern(BaseModel, frozen=True):
    tag: Literal["wildcard-pattern"] = "wildcard-pattern"


class NamePattern(BaseModel, frozen=True):
    tag: Literal["name-pattern"] = "name-pattern"
    name: Identifier


type Pattern = Annotated[
    IntPattern
    | BoolPattern
    | NilPattern
    | ConsPattern
    | TuplePattern
    | WildcardPattern
    | NamePattern,
    Field(discriminator="tag"),
]


class Match(BaseModel, frozen=True):
    tag: Literal["match"] = "match"
    scrutinee: "Term"
    clauses: Sequence[tuple[Pattern, "Term"]]


class Allocate(BaseModel, frozen=True):
    tag: Literal["allocate"] = "allocate"
    count: Nat


class Load(BaseModel, frozen=True):
    tag: Literal["load"] = "load"
    base: "Term"
    index: Nat


class Store(BaseModel, frozen=True):
    tag: Literal["store"] = "store"
    base: "Term"
    index: Nat
    value: "Term"


class Begin(BaseModel, frozen=True):
    tag: Literal["begin"] = "begin"
    effects: Sequence["Term"]
    value: "Term"


class Tuple(BaseModel, frozen=True):
    tag: Literal["tuple"] = "tuple"
    elements: Sequence["Term"]


class TupleRef(BaseModel, frozen=True):
    tag: Literal["tuple-ref"] = "tuple-ref"
    base: "Term"
    index: Nat


class Cons(BaseModel, frozen=True):
    tag: Literal["cons"] = "cons"
    head: "Term"
    tail: "Term"


class Nil(BaseModel, frozen=True):
    tag: Literal["nil"] = "nil"


class Car(BaseModel, frozen=True):
    tag: Literal["car"] = "car"
    base: "Term"


class Cdr(BaseModel, frozen=True):
    tag: Literal["cdr"] = "cdr"
    base: "Term"


class IsNil(BaseModel, frozen=True):
    tag: Literal["is-nil"] = "is-nil"
    base: "Term"


class ListLiteral(BaseModel, frozen=True):
    tag: Literal["list"] = "list"
    elements: Sequence["Term"]


type Term = Annotated[
    Let
    | LetRec
    | Reference
    | Abstract
    | Apply
    | Immediate
    | Primitive
    | Branch
    | BoolLiteral
    | And
    | Or
    | Not
    | Cond
    | Div
    | Mod
    | GreaterThan
    | GreaterThanOrEqual
    | LessThanOrEqual
    | NotEqual
    | LessThan
    | Match
    | Allocate
    | Load
    | Store
    | Begin
    | Tuple
    | TupleRef
    | Cons
    | Nil
    | Car
    | Cdr
    | IsNil
    | ListLiteral,
    Field(discriminator="tag"),
]


# Resolve forward references now that Term and all classes are fully defined.
Program.model_rebuild()
Let.model_rebuild()
LetRec.model_rebuild()
Abstract.model_rebuild()
Apply.model_rebuild()
Primitive.model_rebuild()
Branch.model_rebuild()
Load.model_rebuild()
Store.model_rebuild()
Begin.model_rebuild()
Tuple.model_rebuild()
TupleRef.model_rebuild()
Cons.model_rebuild()
Nil.model_rebuild()
Car.model_rebuild()
Cdr.model_rebuild()
IsNil.model_rebuild()
ListLiteral.model_rebuild()
BoolLiteral.model_rebuild()
And.model_rebuild()
Or.model_rebuild()
Not.model_rebuild()
Cond.model_rebuild()
Div.model_rebuild()
Mod.model_rebuild()
GreaterThan.model_rebuild()
GreaterThanOrEqual.model_rebuild()
LessThanOrEqual.model_rebuild()
NotEqual.model_rebuild()
LessThan.model_rebuild()
IntPattern.model_rebuild()
BoolPattern.model_rebuild()
NilPattern.model_rebuild()
ConsPattern.model_rebuild()
TuplePattern.model_rebuild()
WildcardPattern.model_rebuild()
NamePattern.model_rebuild()
Match.model_rebuild()
