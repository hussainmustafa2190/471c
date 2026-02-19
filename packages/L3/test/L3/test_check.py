import pytest
from L3.syntax import (
    Abstract, Allocate, Apply, Begin, Branch, 
    Immediate, Let, LetRec, Load, Primitive, Reference, Store
)
from L3.check import check_term

def test_check_immediates():
    check_term(Immediate(value=42), {})

def test_check_reference_success():
    check_term(Reference(name="x"), {"x": None})

def test_check_reference_error():
    with pytest.raises(NameError, match="Unbound identifier: x"):
        check_term(Reference(name="x"), {})

def test_check_let():
    # bindings is a list of tuples/pairs
    term = Let(bindings=[("x", Immediate(value=5))], body=Reference(name="x"))
    check_term(term, {})

def test_check_let_out_of_scope():
    term = Begin(
        effects=[Let(bindings=[("x", Immediate(value=5))], body=Immediate(value=10))],
        value=Reference(name="x")
    )
    with pytest.raises(NameError):
        check_term(term, {})

def test_check_letrec_recursion():
    term = LetRec(bindings=[("f", Reference(name="f"))], body=Reference(name="f"))
    check_term(term, {})

def test_check_abstract():
    term = Abstract(parameters=["x", "y"], body=Reference(name="x"))
    check_term(term, {})

def test_check_apply():
    term = Apply(target=Reference(name="f"), arguments=[Reference(name="x")])
    check_term(term, {"f": None, "x": None})

def test_check_branch():
    term = Branch(
        operator="==", 
        left=Immediate(value=1),
        right=Immediate(value=1),
        consequent=Immediate(value=2), 
        otherwise=Immediate(value=3)
    )
    check_term(term, {})

def test_check_primitive():
   
    term = Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=2))
    check_term(term, {})

def test_check_apply_no_args():
   
    term = Apply(target=Reference(name="f"), arguments=[])
    check_term(term, {"f": None})

def test_check_memory_ops():
    ctx = {"p": None, "v": None}
    check_term(Allocate(count=1), ctx) 
    check_term(Load(base=Reference(name="p"), index=0), ctx)
    check_term(Store(base=Reference(name="p"), index=0, value=Reference(name="v")), ctx)

def test_check_begin_logic():
    term = Begin(effects=[Immediate(value=1), Immediate(value=2)], value=Immediate(value=3))
    check_term(term, {})
    
def test_check_begin_empty_effects():
    # Covers the branch where the 'effects' loop does not execute
    term = Begin(effects=[], value=Immediate(value=100))
    check_term(term, {})