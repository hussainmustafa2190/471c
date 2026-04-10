# L3 Compiler Extension Proposal

**Course:** 671  
**Date:** April 2026  
**Submission:** Graduate Student, Individual  

---

## Overview

The goal of my extensions is to make L3 feel more like a real usable functional language. Right now L3 is pretty bare — you can do arithmetic and basic branching but that is about it. My proposed extensions all work toward a single theme: extending L3 into a more complete Scheme-like functional language. The extensions build on each other, with booleans being the most foundational piece that others depend on.

The proposal includes 2 major extensions and 3 minor extensions, all working toward the same end goal of making L3 expressive enough to write real functional programs.

---

## Major Extension 1: Boolean Type and Logical Operators

### 1. Justification

Right now L3 has no boolean values. The `if` form works but there is no `true` or `false` — you just use integers and hope for the best. This is confusing for users and makes programs hard to read. Anyone writing a program with conditions has to remember that `0` means false and anything else means true, which is error-prone and ugly.

Adding proper booleans makes the language safer and more readable. It also unlocks `and`, `or`, and `not` which are fundamental to writing real programs. Pretty much every functional language has this — it is a glaring omission in L3.

### 2. Surface Language Description

Users will be able to write `true` and `false` as literal values. The logical operators `and`, `or`, and `not` will be available as built-in forms.

```scheme
; basic boolean literals
true
false

(not true)          ; => false
(not false)         ; => true
(and true true)     ; => true
(and true false)    ; => false
(or false false)    ; => false
(or false true)     ; => true

(l3 (x)
  (if (and (< x 10) (< 0 x))
    1
    0))

; checking if a number is in range
(l3 (n)
  (if (or (< n 0) (< 100 n))
    false
    true))
```

`and` stops evaluating as soon as it hits a `false`, and `or` stops as soon as it hits a `true`. This is standard short-circuit behavior and users will expect it. Internally `true` and `false` are represented as `Immediate(1)` and `Immediate(0)`. `not` desugars to `(if x false true)`. `and` and `or` desugar into nested `if` expressions so short-circuit behavior comes for free.

### 3. Compiler Impact

- **Parser / Grammar (`L3.lark`):** Add `true`, `false` as terminals. Add `and`, `or`, `not` as recognized forms. Medium effort.
- **Syntax (`L3/syntax.py`):** Treat `true`/`false` as `Immediate(1)`/`Immediate(0)`. Minimal changes.
- **Checker (`L3/check.py`):** Minimal impact — booleans are just values, no new scoping rules.
- **Uniqify and Eliminate LetRec:** No impact.
- **Optimizer (`L2/optimize.py`):** Constant propagation can fold boolean expressions at compile time. `(and true false)` folds to `false` immediately.
- **CPS Conversion (`L2/cps_convert.py`):** No new cases needed since `and`/`or`/`not` all desugar into `if`/`branch` before CPS runs.
- **Code generation:** No impact — booleans are just `1` and `0` in the output.

This is the most foundational extension. The `cond` extension (Minor 2) and the `null?` check in lists (Minor 1) both depend on it.

### 4. Success Criteria

- `true` and `false` parse and evaluate correctly
- `and`, `or`, `not` produce correct results for all input combinations
- Short-circuit evaluation works correctly
- Optimizer folds constant boolean expressions
- All existing tests still pass

---

## Major Extension 2: Basic Pattern Matching (match)

### 1. Justification

Pattern matching is one of the most useful features in functional languages. OCaml, Haskell, Rust, and even Python 3.10 all have it. Right now in L3, if you want to check multiple conditions you have to write deeply nested `if` expressions which are ugly and hard to read. A `match` form makes this much cleaner and is a good fit for a compiler course because it has a clear desugaring story.

### 2. Surface Language Description

The `match` form takes an expression and a list of clauses. Each clause has a pattern and a body. Patterns are kept simple for now: integer literals, boolean literals, and a wildcard `_`.

```scheme
(l3 (x)
  (match x
    (0  0)
    (1  1)
    (_  -1)))

(l3 (x)
  (match (< x 0)
    (true  -1)
    (false  1)))
```

`match` desugars into nested `if`/`branch` expressions. An integer literal `n` becomes `(== subject n)`, a boolean literal becomes the corresponding comparison, and the wildcard `_` is the final else branch. So:

```scheme
(match x (0 "zero") (1 "one") (_ "other"))
```

becomes:

```scheme
(if (== x 0) "zero" (if (== x 1) "one" "other"))
```

This desugaring happens as a new pass right after parsing, before the checker runs. The rest of the pipeline never sees `match` at all.

### 3. Compiler Impact

- **Parser / Grammar (`L3.lark`):** Add `match` form with pattern syntax. Medium effort.
- **Syntax (`L3/syntax.py`):** Add `Match` and `Pattern` nodes. Temporary — eliminated in the desugaring pass.
- **New pass `desugar.py`:** Walks the AST and replaces `Match` nodes with nested `Branch` nodes. This is where most of the work lives.
- **`main.py`:** Add the desugar pass right after parsing.
- **Checker and everything downstream:** No impact — `match` is gone before checker runs.
- **Optimizer:** Folds constant pattern matches for free since they become `Branch` nodes.

Depends on booleans (Major 1) for boolean patterns. Pairs naturally with `cond` (Minor 2).

### 4. Success Criteria

- Integer pattern matching works correctly
- Boolean patterns work (depends on Major 1)
- Wildcard `_` matches anything and must be last
- Nested `match` works correctly
- Optimizer folds constant match expressions
- Existing tests pass

---

## Minor Extension 1: List Type

### 1. Justification

A functional language without lists is pretty limited. Lists are the bread and butter of Scheme/Lisp. Adding basic list support makes it possible to write actually interesting programs in L3 like summing a list, filtering, reversing, etc.

### 2. Surface Language Description

```scheme
(list)                       ; empty list
(list 1 2 3)                 ; => (1 2 3)
(cons 1 (list 2 3))          ; => (1 2 3)
(car (list 1 2 3))           ; => 1
(cdr (list 1 2 3))           ; => (2 3)
(null? (list))               ; => true
(null? (list 1 2))           ; => false

(l3 ()
  (letrec ((sum (lambda (lst)
                 (if (null? lst)
                   0
                   (+ (car lst) (sum (cdr lst)))))))
    (sum (list 1 2 3 4 5))))   ; => 15
```

Lists are built on top of the existing `allocate`/`store`/`load` infrastructure. The empty list is `Immediate(0)`. `cons` allocates a 2-slot array with head at index 0 and tail at index 1. `car` is `load` at 0, `cdr` is `load` at 1, `null?` is `(== lst 0)`. Everything desugars before the checker runs so the rest of the pipeline is unaffected.

### 3. Compiler Impact

- **Parser:** Add `list`, `cons`, `car`, `cdr`, `null?` as recognized forms. Small effort.
- **Desugar pass (shared with match):** Handle list forms. Small-medium effort.
- **Everything else:** No impact.
- **CPS:** No new cases needed — `allocate`/`load`/`store` already handled.

### 4. Success Criteria

- `cons`, `car`, `cdr`, `null?` work correctly
- `(list 1 2 3)` builds the right structure
- Recursive list programs like sum and length work correctly

---

## Minor Extension 2: cond Expression

### 1. Justification

Nested `if` expressions get ugly fast. `cond` is standard Scheme syntax that makes multi-way conditionals readable. Very small effort, noticeable usability improvement.

### 2. Surface Language Description

Instead of:

```scheme
(if (< x 0) -1 (if (== x 0) 0 1))
```

You can write:

```scheme
(cond
  ((< x 0)  -1)
  ((== x 0)  0)
  (else       1))
```

Desugars trivially into nested `if` expressions. `else` is just a wildcard that always evaluates to its body.

### 3. Compiler Impact

- **Parser:** Add `cond` form. Small.
- **Desugar pass:** A few lines to convert `cond` into nested `if`. Trivial.
- **Everything else:** No impact.

### 4. Success Criteria

- `cond` with multiple clauses works
- `else` clause works as a fallback
- Desugars to same output as equivalent nested `if`

---

## Minor Extension 3: Additional Operators

### 1. Justification

L3 only has `+`, `-`, `*`, `<`, `==`. Missing division, modulo, and the other comparison operators. These come up constantly in real programs.

### 2. Surface Language Description

```scheme
(/ 10 3)     ; => 3   (integer division)
(% 10 3)     ; => 1   (modulo)
(> 5 3)      ; => true
(>= 5 5)     ; => true
(<= 3 5)     ; => true
```

`>`, `>=`, `<=` desugar into combinations of `<` and `==`. `/` and `%` need new operator cases added to the existing primitive handling.

### 3. Compiler Impact

- **Parser / Grammar:** Add new operator tokens. Small.
- **L2/L3 Syntax:** Add `/` and `%` to the operator literal type. Small.
- **Optimizer:** Add folding cases for new operators. Small.
- **CPS:** No new cases — same structure as existing primitives.
- **Code generation:** Add Python AST nodes for `//` and `%`. Small.

### 4. Success Criteria

- All new operators produce correct results
- Optimizer folds constant expressions with new operators
- Division by zero raises a reasonable error

---

## Timeline

| Week | Work |
|------|------|
| **Week 1** | Major Extension 1: Booleans. Parser changes, syntax nodes, desugar pass skeleton, optimizer folding for booleans. Write tests. |
| **Week 2** | Major Extension 2: Pattern matching. Grammar additions, Match AST nodes, desugar pass, integration tests. Also Minor Extension 3 (operators) since it is small. |
| **Week 3** | Minor Extension 1: Lists. Desugar into allocate/load/store, test with recursive list programs. Minor Extension 2: cond. |
| **Week 4** | Buffer week. Full integration testing. Bug fixes. Make sure entire existing test suite still passes. Final documentation. |

---

## How the Extensions Fit Together

All five extensions work toward the same goal: making L3 usable for writing real functional programs. The dependency structure is straightforward:

- **Booleans (Major 1)** is the foundation — `cond`, `match`, and `null?` all depend on it
- **Pattern matching (Major 2)** builds on booleans for boolean patterns
- **Lists (Minor 1)** uses booleans for `null?` and uses the existing `letrec`
- **cond (Minor 2)** is independent but pairs naturally with booleans
- **Operators (Minor 3)** is completely independent and can be done anytime

By the end of the month you should be able to write something like this in L3:

```scheme
(l3 ()
  (letrec ((filter (lambda (pred lst)
                    (cond
                      ((null? lst)         (list))
                      ((pred (car lst))    (cons (car lst)
                                                 (filter pred (cdr lst))))
                      (else                (filter pred (cdr lst))))))
           (evens  (lambda (n) (== (% n 2) 0))))
    (filter evens (list 1 2 3 4 5 6))))  ; => (2 4 6)
```

That is a real functional program — and right now L3 cannot express it at all. That is the goal.