import pytest
from L3.check import check_program, check_term
from L3.syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Immediate,
    Let,
    LetRec,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
)

def test_check_program_success():
    program = Program(parameters=["arg1"], body=Immediate(value=0))
    check_program(program)

def test_check_program_empty_params():
    # Clears branch partial for program parameter loop
    program = Program(parameters=[], body=Immediate(value=0))
    check_program(program)

def test_check_program_duplicate_parameters():
    program = Program(parameters=["x", "x"], body=Immediate(value=0))
    with pytest.raises(ValueError, match="Duplicate parameters in program"):
        check_program(program)

def test_check_term_let_success():
    term = Let(bindings=[("x", Immediate(value=0))], body=Reference(name="x"))
    check_term(term, {})

def test_check_term_let_scope():
    term = Let(
        bindings=[("x", Immediate(value=0)), ("y", Reference(name="x"))],
        body=Reference(name="y"),
    )
    with pytest.raises(ValueError, match="Unbound identifier: x"):
        check_term(term, {})

def test_check_term_let_duplicate_binders():
    term = Let(
        bindings=[("x", Immediate(value=0)), ("x", Immediate(value=1))],
        body=Reference(name="x"),
    )
    with pytest.raises(ValueError, match="Duplicate binders in Let"):
        check_term(term, {})

def test_check_term_letrec_success():
    term = LetRec(
        bindings=[("y", Reference(name="x")), ("x", Immediate(value=0))],
        body=Reference(name="x"),
    )
    check_term(term, {})

def test_check_term_letrec_duplicate_binders():
    term = LetRec(
        bindings=[("x", Immediate(value=0)), ("x", Immediate(value=1))],
        body=Reference(name="x"),
    )
    with pytest.raises(ValueError, match="Duplicate binders in LetRec"):
        check_term(term, {})


def test_check_term_abstract_success():
    term = Abstract(parameters=["x"], body=Reference(name="x"))
    check_term(term, {})

def test_check_term_abstract_empty_params():
    term = Abstract(parameters=[], body=Immediate(value=0))
    check_term(term, {})

def test_check_term_abstract_duplicate_parameters():
    term = Abstract(parameters=["x", "x"], body=Immediate(value=0))
    with pytest.raises(ValueError, match="Duplicate parameters in Abstract"):
        check_term(term, {})

def test_check_term_apply_success():
    term = Apply(target=Reference(name="x"), arguments=[Immediate(value=0)])
    check_term(term, {"x": None})

def test_check_term_apply_no_args():
    term = Apply(target=Reference(name="f"), arguments=[])
    check_term(term, {"f": None})

def test_check_term_reference_free():
    with pytest.raises(ValueError, match="Unbound identifier: x"):
        check_term(Reference(name="x"), {})

def test_check_term_immediate():
    check_term(Immediate(value=0), {})

def test_check_term_primitive():
    term = Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=2))
    check_term(term, {})

def test_check_term_branch():
    term = Branch(
        operator="<", 
        left=Immediate(value=1), 
        right=Immediate(value=2),
        consequent=Immediate(value=0), 
        otherwise=Immediate(value=1)
    )
    check_term(term, {})

def test_check_term_allocate():
    check_term(Allocate(count=5), {})

def test_check_term_load():
    check_term(Load(base=Reference(name="x"), index=0), {"x": None})

def test_check_term_store():
    check_term(Store(
        base=Reference(name="x"), 
        index=0, 
        value=Immediate(value=0)
    ), {"x": None})

def test_check_term_begin_success():
    term = Begin(effects=[Immediate(value=1)], value=Immediate(value=0))
    check_term(term, {})

def test_check_term_begin_empty_effects():
    term = Begin(effects=[], value=Immediate(value=0))
    check_term(term, {})

def test_coverage_gap_fillers():
    check_program(Program(parameters=[], body=Immediate(value=0)))
    check_term(Let(bindings=[], body=Immediate(value=0)), {})
    check_term(LetRec(bindings=[], body=Immediate(value=0)), {})
    check_term(Abstract(parameters=[], body=Immediate(value=0)), {})
    check_term(Apply(target=Immediate(value=0), arguments=[]), {})
    check_term(Begin(effects=[], value=Immediate(value=0)), {})

def test_coverage_unknown_term():
    with pytest.raises(ValueError, match="Unknown term:"):
        check_term("Not a Term", {}) 