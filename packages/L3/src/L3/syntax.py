from collections.abc import Sequence
from typing import Annotated, Literal

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
    operator: Literal["+", "-", "*"]
    left: "Term"
    right: "Term"


class Branch(BaseModel, frozen=True):
    tag: Literal["branch"] = "branch"
    operator: Literal["<", "=="]
    left: "Term"
    right: "Term"
    consequent: "Term"
    otherwise: "Term"


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
