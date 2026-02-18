import pytest
from L3.syntax import (
    Abstract, Allocate, Apply, Begin, Branch, Identifier, 
    Immediate, Let, LetRec, Load, Primitive, Reference, Store
)
from L3.check import check_term

def test_check_immediates():
    check_term(Immediate(42), {})

def test_check_reference_success():
    check_term(Reference(Identifier("x")), {Identifier("x"): None})

def test_check_reference_error():
    with pytest.raises(NameError, match="Unbound identifier: x"):
        check_term(Reference(Identifier("x")), {})

def test_check_let():
    # let x = 5 in x
    term = Let(Identifier("x"), Immediate(5), Reference(Identifier("x")))
    check_term(term, {})

def test_check_let_out_of_scope():
    # (let x = 5 in 10); x (x is unbound here)
    term = Begin([
        Let(Identifier("x"), Immediate(5), Immediate(10)),
        Reference(Identifier("x"))
    ])
    with pytest.raises(NameError):
        check_term(term, {})

def test_check_letrec_recursion():
    # letrec f = f in f
    f = Identifier("f")
    term = LetRec([(f, Reference(f))], Reference(f))
    check_term(term, {})

def test_check_abstract():
    # lambda (x, y) -> x
    x, y = Identifier("x"), Identifier("y")
    term = Abstract([x, y], Reference(x))
    check_term(term, {})

def test_check_apply():
    f, x = Identifier("f"), Identifier("x")
    term = Apply(Reference(f), [Reference(x)])
    check_term(term, {f: None, x: None})

def test_check_primitive_and_branch():
    # if 1 then 2 else 3
    term = Branch(Immediate(1), Immediate(2), Immediate(3))
    check_term(term, {})
    
    # prim + 1 2
    term = Primitive("+", [Immediate(1), Immediate(2)])
    check_term(term, {})

def test_check_memory_ops():
    # alloc, load, store
    ptr, val = Identifier("p"), Identifier("v")
    ctx = {ptr: None, val: None}
    
    check_term(Allocate([Immediate(1)]), ctx)
    check_term(Load(Reference(ptr), Immediate(0)), ctx)
    check_term(Store(Reference(ptr), Immediate(0), Reference(val)), ctx)

def test_check_begin_empty_and_multiple():
    check_term(Begin([]), {})
    check_term(Begin([Immediate(1), Immediate(2)]), {})