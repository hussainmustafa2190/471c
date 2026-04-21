# L3 Compiler Extension Proposal

**Course:** CISC 471/671  
**Date:** April 2026  
**Submission:** Mustafa Hussain - 702777137

---

## Previous Proposal Summary

The original proposal submitted earlier in the semester outlined the following extensions:

**Major Extensions:**
1. Boolean Type and Logical Operators — adding `true`, `false`, `and`, `or`, `not` to L3
2. Basic Pattern Matching (`match`) — a desugaring pass for multi-way dispatch on values

**Minor Extensions:**
1. List Type — `cons`, `car`, `cdr`, `null?`, `list` built on top of `allocate`/`load`/`store`
2. `cond` Expression — multi-way conditional that desugars to nested `if`
3. Additional Operators — `/`, `%`, `>`, `>=`, `<=`

The original proposal treated booleans and pattern matching as separate major extensions and split the minor extensions across three loosely related features. Feedback noted that the minor extensions were a bit scattered and that the booleans extension was doing a lot on its own (it was really three features bundled as one).

---

## Revised Proposal

The revised proposal keeps the same five extensions but reorganizes and strengthens them in two ways:

1. **Major 1 is expanded** to absorb `cond` and the extended operators since they all share the same desugar-to-if story. This makes Major 1 a single coherent extension about *conditions and control flow*.

2. **Minor 1 is expanded** to cover both tuples and lists together since they are implemented the same way (both desugar to `allocate`/`load`/`store`). Minor 2 and Minor 3 are replaced with new, more interesting optimization extensions: an L1-level peephole optimizer and an L0-level dead procedure elimination pass.

The theme remains the same: making L3 expressive enough to write real functional programs. The revised structure just makes the extensions cleaner and more technically interesting.

---

## Overview

The five extensions in this proposal all work toward a single goal: extending L3 into a more complete Scheme-like functional language that can express real programs over structured data. By the end of the semester the goal is to be able to write something like this in L3:

```scheme
(l3 ()
  (letrec ((filter (lambda (pred lst)
                     (cond
                       ((null? lst) (list))
                       ((pred (car lst)) (cons (car lst) (filter pred (cdr lst))))
                       (else (filter pred (cdr lst))))))
           (evens (lambda (n) (== (% n 2) 0))))
    (filter evens (list 1 2 3 4 5 6))))
```

That is a real functional program — right now L3 cannot express it at all.

The extensions and their dependencies:

| Extension | Type | Depends On |
|-----------|------|-----------|
| Major 1: Booleans, Logical Operators, `cond`, Extended Operators | Major | None |
| Major 2: Pattern Matching (`match`) | Major | Major 1 (for boolean patterns), Minor 1 (for structural patterns) |
| Minor 1: Tuples and Lists | Minor | None |
| Minor 2: L1 Peephole Optimization | Minor | None |
| Minor 3: L0 Dead Procedure Elimination | Minor | None |

---

## Major Extension 1: Boolean Type, Logical Operators, `cond`, and Extended Arithmetic

### 1. Justification

This extension combines four closely related features that all belong in the same extension because they all share the same implementation strategy — desugaring into existing L3 primitives before the checker runs.

Right now L3 has no boolean values. The `if` form works but there is no `true` or `false` — you just use integers and hope for the best. This is confusing and makes programs hard to read. Anyone writing a program with conditions has to remember that 0 means false and anything else means true, which is error-prone. Pretty much every functional language has proper booleans — it is a glaring omission in L3.

The logical operators `and`, `or`, `not` are fundamental to writing real conditions. Without them you have to nest multiple `if` expressions to express something as simple as "x is between 0 and 100". The `cond` form is a direct quality-of-life improvement over deeply nested `if` expressions — it is standard Scheme and makes multi-way conditionals readable. The extended arithmetic operators (`/`, `%`, `>`, `>=`, `<=`) come up constantly in real programs and their absence forces awkward workarounds.

Grouping all of these into one major extension makes sense because they all share the same desugar story: every new form reduces to existing L3 primitives before the checker even runs.

### 2. Surface Language Description

**Boolean Literals:**

```scheme
true     ; => 1
false    ; => 0
```

**Logical Operators** (short-circuit):

```scheme
(not true)        ; => false
(and true false)  ; => false
(or  false true)  ; => true

; checking if x is in range [0, 10)
(l3 (x)
  (if (and (< x 10) (< 0 x))
      1
      0))
```

`and` stops evaluating as soon as it hits a `false`. `or` stops as soon as it hits a `true`. Internally: `not` desugars to `(if x false true)`. `and a b` desugars to `(if a (if b true false) false)`. `or a b` desugars to `(if a true (if b true false))`. Short-circuit behavior comes for free from the `if` desugaring.

**`cond`:**

Instead of:

```scheme
(if (< x 0) -1 (if (== x 0) 0 1))
```

You can write:

```scheme
(cond
  ((< x 0)   -1)
  ((== x 0)   0)
  (else        1))
```

`else` is a wildcard that always evaluates to its body. `cond` desugars trivially into nested `if` expressions.

**Extended Arithmetic and Comparison Operators:**

```scheme
(/ 10 3)    ; => 3  (integer division)
(% 10 3)    ; => 1  (modulo)
(> 5 3)     ; => true
(>= 5 5)    ; => true
(<= 3 5)    ; => true
```

`> x y` desugars to `(< y x)`. `>= x y` desugars to `(not (< x y))`. `<= x y` desugars to `(not (< y x))`. `/` and `%` need new operator cases in the primitive handling. Division by zero raises a runtime error matching Python behavior.

**Complete Example:**

```scheme
(l3 (n)
  (cond
    ((< n 0)    false)
    ((== n 0)   false)
    ((> n 100)  false)
    (else       true)))
```

### 3. Compiler Impact

- **L3.lark (parser):** Add `true`, `false` as terminals. Add `and`, `or`, `not`, `cond` as recognized forms. Add `/`, `%`, `>`, `>=`, `<=` to the operator/comparator tokens. Medium effort.
- **L3/syntax.py:** Add node types for `And`, `Or`, `Not`, `Cond` (with a clause list) and expand the operator/comparator `Literal` types. `true`/`false` can just be `Immediate(1)`/`Immediate(0)` at parse time.
- **New desugar pass (desugar.py):** Runs right after parsing before check. Converts all the new forms into existing L3 primitives. `and`/`or`/`not` become nested `Branch` nodes. `cond` becomes nested `if`. `>`, `>=`, `<=` become combinations of `<` and `==`. This is where most of the implementation work lives.
- **L3/check.py:** Minimal impact — by the time check runs the new forms are already gone. If check runs before desugar for better error messages, new cases will be needed and I will decide on the ordering during implementation.
- **L2/optimize.py:** Constant folding in `ConstantPropagation._fold` gains new cases for `/` and `%` and the new comparison operators. `(and true false)` folds to `false` at compile time since it desugars to a `Branch` with `Immediate` operands.
- **L1/to_python.py:** New cases for `//` and `%` in the operator match. Everything else is handled by the desugar pass.
- **Everything else:** No impact. CPS conversion, uniqify, eliminate_letrec all see only existing node types after desugaring.

### 4. Success Criteria

- `true` and `false` parse and evaluate to 1 and 0 correctly
- `and`, `or`, `not` produce correct results for all input combinations
- Short-circuit evaluation works — second argument of `and` not evaluated when first is `false`
- `cond` with multiple clauses desugars to the same output as equivalent nested `if`
- `else` clause works as a fallback in `cond`
- `/`, `%` produce correct results including for negative inputs
- `>`, `>=`, `<=` produce correct results for all comparisons
- Optimizer folds constant boolean and arithmetic expressions
- All existing tests still pass
- 100% branch coverage on `desugar.py` and all modified files

---

## Major Extension 2: Basic Pattern Matching (`match`)

### 1. Justification

Pattern matching is one of the most useful features in functional languages. OCaml, Haskell, Rust, and even Python 3.10 all have it. Right now in L3, if you want to check multiple conditions you have to write deeply nested `if` expressions which are ugly and hard to read. A `match` form makes this much cleaner and is a good fit for a compiler course because it has a clear desugaring story.

With booleans (Major 1) and lists/tuples (Minor 1) in place, pattern matching becomes especially powerful. You can match on the shape of a list, check for `nil`, and bind the head and tail all in one expression instead of manually calling `null?`, `car`, and `cdr`.

### 2. Surface Language Description

The `match` form takes an expression and a list of clauses. Each clause has a pattern and a body. Clauses are tried in order and the first matching one is used.

Supported patterns in the initial version:

- Integer literals — match a specific integer
- `true` / `false` — match boolean values (depends on Major 1)
- `nil` — match the empty list (depends on Minor 1)
- `(cons name1 name2)` — match a cons cell, bind head and tail
- `(tuple name ...)` — match a tuple of a specific arity, bind each element
- `_` (wildcard) — match anything, bind nothing
- A plain name — match anything and bind it

**Integer and boolean dispatch:**

```scheme
(l3 (x)
  (match x
    (0   0)
    (1   1)
    (_  -1)))

(l3 (x)
  (match (< x 0)
    (true  -1)
    (false  1)))
```

**List pattern matching:**

```scheme
(l3 ()
  (letrec ((sum (lambda (xs)
                  (match xs
                    (nil         0)
                    ((cons h t)  (+ h (sum t)))))))
    (sum (list 1 2 3 4 5))))
```

**Tuple destructuring:**

```scheme
(l3 (pair)
  (match pair
    ((tuple a b)  (+ a b))))
```

`match` desugars into nested `if`/`let` expressions. An integer pattern `n` becomes `(== subject n)`. `nil` becomes `(null? subject)`. `(cons h t)` becomes `(if (not (null? subject)) (let ((h (car subject)) (t (cdr subject))) body) ...)`. Tuple patterns use `tuple-ref`. The wildcard and name patterns are the final `else` branch. This desugaring happens in `desugar.py` right after parsing — the rest of the pipeline never sees a `match` node at all.

### 3. Compiler Impact

- **L3.lark:** Add `match` form and pattern sub-grammar. Patterns are a new recursive grammar fragment. Medium effort.
- **L3/syntax.py:** Add `Match` node and a `Pattern` sum type (`IntPattern`, `BoolPattern`, `NilPattern`, `ConsPattern`, `TuplePattern`, `WildcardPattern`, `NamePattern`). These are temporary — eliminated in `desugar.py`.
- **desugar.py (extended from Major 1):** New `desugar_match` function walks the AST and replaces `Match` nodes with nested `Branch`/`Let` nodes. This is the main implementation work for this extension.
- **L3/check.py:** If check runs after desugar, no new cases needed. If check runs before, a new case for `Match` must verify that pattern binders are in scope in the clause body.
- **Everything downstream:** No impact — `match` is gone before `eliminate_letrec`, CPS conversion, or code generation sees the AST.
- **Optimizer:** Constant pattern matches fold for free since they become `Branch` nodes with `Immediate` operands, which the existing `ConstantPropagation` already handles.

### 4. Success Criteria

- Integer pattern matching works for all integer values
- Boolean patterns `true`/`false` work correctly (requires Major 1)
- `nil` and `cons` patterns work for list matching (requires Minor 1)
- Tuple patterns destructure correctly (requires Minor 1)
- Wildcard `_` matches anything and works as a catch-all
- Pattern binders are scoped to the clause body only
- Nested `match` expressions work correctly
- Optimizer folds constant match expressions
- All existing tests still pass
- 100% branch coverage on all new and modified files

---

## Minor Extension 1: Tuples and Lists

### 1. Justification

A functional language without structured data is very limited. Right now the only way to group values in L3 is to use `allocate`/`store`/`load` directly, which is manual memory management. It works but writing anything over sequences requires a lot of boilerplate. Adding tuples and lists as first-class forms makes L3 much more expressive and enables the structural patterns in Major Extension 2.

Tuples are fixed-size heterogeneous collections useful for grouping a known number of values (like a coordinate pair). Lists are the classic Lisp/Scheme singly-linked structure for sequences of arbitrary length. Both are fundamental to functional programming and together they cover most structured data needs.

### 2. Surface Language Description

**Tuples:**

```scheme
(tuple 1 2 3)          ; a 3-element tuple
(tuple-ref t 0)        ; first element
(tuple-ref t 1)        ; second element

(l3 (x y)
  (let ((pair (tuple x y)))
    (+ (tuple-ref pair 0) (tuple-ref pair 1))))
```

**Lists:**

```scheme
(list)                       ; empty list
(list 1 2 3)                 ; list containing 1, 2, 3
(cons 1 (list 2 3))          ; same as (list 1 2 3)
(car (list 1 2 3))           ; => 1
(cdr (list 1 2 3))           ; => (2 3)
(null? (list))               ; => true
(null? (list 1 2))           ; => false

; sum a list recursively
(l3 ()
  (letrec ((sum (lambda (lst)
                  (if (null? lst)
                      0
                      (+ (car lst) (sum (cdr lst)))))))
    (sum (list 1 2 3 4 5))))   ; => 15
```

Implementation: everything desugars to existing `allocate`/`store`/`load` infrastructure. The empty list is `Immediate(0)`. `cons` allocates a 2-slot array, stores head at index 0 and tail at index 1. `car` is load at index 0, `cdr` is load at index 1. `null?` desugars to `(== lst 0)`. `(list 1 2 3)` desugars to `(cons 1 (cons 2 (cons 3 nil)))`. Tuples allocate an N-slot array and store each element; `tuple-ref` is load at the given index.

### 3. Compiler Impact

- **L3.lark:** Add `list`, `cons`, `car`, `cdr`, `null?`, `tuple`, `tuple-ref` as recognized forms. Small effort.
- **desugar.py (extended):** Handle all the new list and tuple forms — translates them into `Allocate`/`Store`/`Load` trees. Small-medium effort.
- **Everything else:** No impact. All new forms are eliminated after desugar. CPS conversion, optimizer, and code generation already handle `allocate`/`store`/`load`.

### 4. Success Criteria

- `cons`, `car`, `cdr`, `null?` all produce correct results
- `(list 1 2 3)` builds the right structure and `car`/`cdr` traverse it correctly
- Recursive list programs like sum and length work correctly
- `tuple` and `tuple-ref` work for tuples of various sizes
- Nested structures (list of tuples, etc.) work correctly
- 100% branch coverage on new desugar cases

---

## Minor Extension 2: L1 Peephole Optimization

### 1. Justification

CPS conversion produces correct L1 code but it is not particularly clean. Because each term independently allocates fresh names and builds continuation closures, the output often contains redundant patterns that could be simplified before code generation. For example a `Copy` where the source and destination are the same name is a no-op. A continuation closure that is immediately applied to a known value can be beta-reduced away.

This extension adds a peephole optimization pass that runs on the L1 AST after CPS conversion and before `to_python`. The pass looks for simple redundant patterns and eliminates them. This reduces the size of the generated Python code and makes it faster and easier to inspect.

This is a minor extension because the pass is completely self-contained — it reads and writes L1 ASTs and does not interact with any other pipeline stage. It also does not require any new syntax or semantic analysis.

### 2. Surface Language Description

No surface language impact. The benefit is visible in the generated Python output being smaller and cleaner.

For example, after CPS conversion of a simple `let` binding the output might contain:

```python
# before peephole optimization
def k0(t0):
    return halt(t0)
return f(x, k0)
```

If `k0` is only ever called once and its body is just a halt, the optimizer can inline it:

```python
# after peephole optimization
return f(x, lambda t0: halt(t0))
```

The specific patterns targeted are:

- **Copy self-assignment:** `Copy(x, x, then)` reduces to `then` directly — assigning a variable to itself does nothing.
- **Halt after Copy:** `Copy(x, y, Halt(x))` where the destination is immediately returned reduces to `Halt(y)`.
- **Trivial continuation inlining:** An `Abstract` whose body is just a `Halt` or a single `Copy` and which is used in exactly one place can be inlined at its call site.

### 3. Compiler Impact

- **New file L1/peephole.py:** A recursive function `peephole_statement` that walks `Statement` trees and applies the reduction rules. Returns a new `Statement`.
- **L3/main.py:** One new line — `l1 = peephole_program(l1)` between CPS conversion and code generation.
- **Everything else:** No impact. The pass consumes and produces L1 ASTs which are already well-defined.

This extension is completely independent of all other extensions and can be implemented at any point.

### 4. Success Criteria

- All existing tests still pass after the peephole pass is added (correctness is preserved)
- Copy self-assignments are eliminated
- Halt-after-Copy chains are simplified
- Trivial continuation closures are inlined where safe
- Generated Python output for simple programs like `fact.l3` is measurably shorter
- 100% branch coverage on `peephole.py`

---

## Minor Extension 3: L0 Dead Procedure Elimination

### 1. Justification

After CPS conversion and lowering to L0, a program is represented as a flat list of `Procedure`s. Each procedure is referenced by name using the `Address` instruction before it can be called via `Call`. CPS conversion can produce procedures that are never actually reachable from the entry point — for example, continuation closures that get inlined by the peephole optimizer (Minor 2) may leave behind orphaned procedure definitions that are never addressed.

Dead procedure elimination at the L0 level removes any `Procedure` whose name never appears in an `Address` instruction reachable from the entry procedure (`l0`). This is meaningful at the L0 level specifically because `l0/to_python.py` emits a Python function definition for every `Procedure` in the program — dead procedures become dead Python functions that take up space in the output file and slow down module loading.

This is a minor extension because the analysis is straightforward: walk the reachable procedures collecting `Address` targets, then filter the procedure list. No new syntax, no new node types, and no changes to any other pipeline stage.

### 2. Surface Language Description

No surface language impact. The benefit is in the generated Python output being smaller. For example if CPS conversion produces procedures `l0`, `k0`, `k1`, `k2` but only `l0` and `k1` are ever referenced via `Address`, the dead procedure eliminator removes `k0` and `k2` before code generation. The generated Python file then contains only two function definitions instead of four.

The analysis works as follows:

1. Start with the set of live procedures containing just the entry point `l0`
2. For each live procedure, scan its statement tree for `Address` instructions and add the named procedure to the live set
3. Repeat until the live set stops growing (fixed-point iteration)
4. Remove any `Procedure` from the program whose name is not in the live set

### 3. Compiler Impact

- **New file L0/dpe.py:** A function `dpe_program` that takes an `L0.Program` and returns a new `L0.Program` with unreachable procedures removed. The reachability analysis collects `Address.name` values by walking each live procedure's `Statement` tree recursively (handling the `Branch` node's two arms).
- **L3/main.py:** One new line — `l0 = dpe_program(l0)` between L0 generation and `to_ast_program`.
- **L0/syntax.py:** No changes needed — the existing node types are sufficient.
- **L0/to_python.py:** No changes needed — it already iterates over whatever procedures are in the program.
- **Everything else:** No impact.

The pass interacts naturally with Minor Extension 2 (peephole): if peephole inlines a continuation and that makes some procedures unreachable, DPE will clean them up. Running peephole first then DPE gives better results than either alone.

### 4. Success Criteria

- All existing tests still pass after DPE is added (correctness is preserved — live procedures are never removed)
- A program with unused procedures generates Python output without those functions
- The entry procedure `l0` is never removed
- A procedure referenced only transitively (A addresses B, B addresses C) is correctly kept alive
- The fixed-point iteration terminates correctly for mutually referencing procedures
- 100% branch coverage on `dpe.py`

---

## Timeline

| Week | Extension | Goal |
|------|-----------|------|
| Week 1 | Major 1 — booleans and `cond` | Parser changes, desugar pass, `true`/`false`, `and`/`or`/`not`, `cond`. Tests passing. |
| Week 2 | Major 1 — extended operators + Minor 2 | Add `/`, `%`, `>`, `>=`, `<=`. Add L1 peephole optimization pass. Tests and coverage. |
| Week 3 | Minor 1 — tuples and lists | Desugar list and tuple forms into `allocate`/`load`/`store`. Test with recursive list programs. |
| Week 4 | Minor 3 — L0 dead procedure elimination | Reachability analysis over L0 procedures. Test that dead procedures are removed and live ones are kept. |
| Weeks 5–6 | Major 2 — pattern matching | Grammar additions, `Match` AST nodes, `desugar_match` for all pattern types. End-to-end tests. |
| Week 7 | Integration and cleanup | Full integration tests across all extensions, coverage audit, README updates, bug fixes. |

If time runs short the most likely cut is tuple patterns in Major 2 — I can start with just `nil`/`cons`/integer/wildcard patterns and add tuple patterns as a follow-up. The optimization passes (Minor 2 and Minor 3) are also easy to scope down since they are purely additive and do not block anything else.

---

## How the Extensions Fit Together

All five extensions work toward the same goal: making L3 expressive enough to write real functional programs over structured data.

- **Major 1** is the most foundational — `cond`, pattern matching on booleans, and `null?` from Minor 1 all depend on it
- **Minor 1** is independent of Major 1 but feeds into Major 2 (the `nil`/`cons`/`tuple` patterns)
- **Major 2** soft-depends on Major 1 for boolean patterns and Minor 1 for structural patterns — integer and wildcard patterns work without either
- **Minor 2** (peephole) and **Minor 3** (L0 DPE) are completely independent and can be done at any point; they interact with each other in that peephole can create dead procedures that DPE then removes
