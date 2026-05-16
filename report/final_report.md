# 471c Compiler Extension Final Report

**Course:** CISC 471/671  
**Semester:** Spring 2026  
**Submission:** Individual

---

## 1. Group Members

| Name | Student ID |
|------|-----------|
| Mustafa Hussain | 702777137 |

---

## 2. Repository

The implementation is available at:

```
https://github.com/hussainmustafa2190/471c
```

All extensions are implemented on the main branch. To run all tests and verify coverage:

```bash
pytest packages/ --cov --cov-report=term-missing
```

---

## 3. Deviations from Proposal

### What matched the proposal exactly

- **Minor 2 (L1 Peephole Optimization):** implemented exactly as proposed — two rules, self-contained pass, no pipeline changes required
- **Minor 3 (L0 Dead Procedure Elimination):** implemented exactly as proposed — fixed-point reachability analysis over the Address graph, filters the procedure list
- **Minor 1 (Tuples and Lists):** implemented exactly as proposed — all new forms desugar to existing allocate/store/load primitives
- **Major 2 (Pattern Matching):** all seven pattern types implemented as proposed (IntPattern, BoolPattern, NilPattern, ConsPattern, TuplePattern, WildcardPattern, NamePattern)

### Minor deviations

**Cond desugaring:** The proposal described cond clauses using the condition directly as a Branch test. The implementation uses operator `!=` with `Immediate(0)` to convert the condition to a boolean decision, which is more consistent with how `and`/`or`/`not` are desugared. The behavior is identical.

**Operator expansion in lower levels:** The proposal mentioned expanding operators in L2/L1/L0 syntax. This was done as proposed but also required updating `to_python.py` at both L1 and L0 levels with new Python AST node types (`ast.FloorDiv`, `ast.Mod`, `ast.Gt`, `ast.GtE`, `ast.LtE`, `ast.NotEq`). This was implicit in the proposal but not explicitly listed.

**Parse test coverage:** The original `test_parse.py` did not cover the new transformer methods added for Major 1 and Major 2. Additional parse tests were added to bring `parse.py` back to 100% coverage. This was not mentioned in the proposal but was required by the contribution guidelines.

There are no deviations in the fundamental design or architecture. All extensions desugar before check as proposed, and nothing below the desugar pass required changes for any of the new syntax forms.

---

## 4. Files Added and Modified

### New Files Created

| File | Purpose |
|------|---------|
| `packages/L0/src/L0/dpe.py` | L0 dead procedure elimination pass |
| `packages/L0/test/L0/test_dpe.py` | Tests for dpe.py |
| `packages/L1/src/L1/peephole.py` | L1 peephole optimization pass |
| `packages/L1/test/L1/test_peephole.py` | Tests for peephole.py |
| `packages/L3/src/L3/desugar.py` | Desugaring pass — all new syntax |
| `packages/L3/test/L3/test_desugar.py` | Tests for desugar.py |

### Modified Files

| File | What Changed |
|------|-------------|
| `packages/L3/src/L3/syntax.py` | Added: BoolLiteral, And, Or, Not, Cond, Div, Mod, GreaterThan, GreaterThanOrEqual, LessThanOrEqual, NotEqual, Match, all Pattern types, Tuple, TupleRef, Cons, Nil, Car, Cdr, IsNil, ListLiteral |
| `packages/L3/src/L3/L3.lark` | Added grammar rules for all new syntax forms |
| `packages/L3/src/L3/parse.py` | Added transformer methods for all new grammar rules |
| `packages/L3/src/L3/main.py` | Added desugar step to pipeline after parsing |
| `packages/L2/src/L2/syntax.py` | Expanded operator literals to include `/`, `%`, `>`, `>=`, `<=`, `!=` |
| `packages/L2/src/L2/optimize.py` | Added constant folding cases for `/`, `%` and new comparators |
| `packages/L2/test/L2/test_optimize.py` | Added folding tests for new operators |
| `packages/L1/src/L1/syntax.py` | Expanded operator/comparator literals |
| `packages/L1/src/L1/to_python.py` | Added Python AST cases for FloorDiv, Mod, Gt, GtE, LtE, NotEq |
| `packages/L0/src/L0/syntax.py` | Expanded operator/comparator literals |
| `packages/L0/src/L0/to_python.py` | Added Python AST cases for new operators |
| `packages/L3/test/L3/test_parse.py` | Added 25 parse tests for all new syntax forms |
| `packages/L3/test/L3/test_desugar.py` | Added tests for Major 1 and Major 2 desugaring |

---

## 5. Test Cases and Results

All 378 tests pass at 100% branch coverage.

### Test Results by File

| Test File | Tests | Result |
|-----------|-------|--------|
| `packages/L0/test/L0/test_dpe.py` | 20 | PASSED |
| `packages/L1/test/L1/test_close.py` | 5 | PASSED |
| `packages/L1/test/L1/test_peephole.py` | 20 | PASSED |
| `packages/L2/test/L2/test_cps_convert.py` | 41 | PASSED |
| `packages/L2/test/L2/test_optimize.py` | 94 | PASSED |
| `packages/L3/test/L3/test_check.py` | 25 | PASSED |
| `packages/L3/test/L3/test_desugar.py` | 47 | PASSED |
| `packages/L3/test/L3/test_eliminate_letrec.py` | 31 | PASSED |
| `packages/L3/test/L3/test_parse.py` | 60 | PASSED |
| `packages/L3/test/L3/test_uniqify.py` | 35 | PASSED |
| **TOTAL** | **378** | **ALL PASSED** |

### Coverage Report

```
Name                                                  Stmts   Miss Branch BrPart  Cover
---------------------------------------------------------------------------------------
packages\L0\src\L0\dpe.py                                40      0     26      0   100%
packages\L0\src\L0\syntax.py                             30      0      0      0   100%
packages\L1\src\L1\close.py                              39      0     22      0   100%
packages\L1\src\L1\peephole.py                           31      0     24      0   100%
packages\L1\src\L1\syntax.py                             28      0      0      0   100%
packages\L2\src\L2\cps_convert.py                        64      0     30      0   100%
packages\L2\src\L2\optimize.py                          190      0    132      0   100%
packages\L2\src\L2\syntax.py                             30      0      0      0   100%
packages\L3\src\L3\check.py                             109      0     86      0   100%
packages\L3\src\L3\desugar.py                           128      0     96      0   100%
packages\L3\src\L3\eliminate_letrec.py                   73      0     54      0   100%
packages\L3\src\L3\parse.py                             183      0      4      0   100%
packages\L3\src\L3\syntax.py                            127      0      0      0   100%
packages\L3\src\L3\uniqify.py                            48      0     26      0   100%
packages\util\src\util\sequential_name_generator.py       8      0      0      0   100%
---------------------------------------------------------------------------------------
TOTAL                                                  1128      0    500      0   100%
```

---

## 6. Sample Programs

The following programs demonstrate the extensions working end to end.

### 6.1 Factorial — booleans and cond

```scheme
(l3 (n)
  (letrec ((fact (lambda (x)
                   (cond
                     ((== x 0) 1)
                     (else (* x (fact (- x 1))))))))
    (fact n)))
```

Run: `python fact.py 10` → `3628800`

### 6.2 List Sum — lists and pattern matching

```scheme
(l3 ()
  (letrec ((sum (lambda (lst)
                  (match lst
                    (nil         0)
                    ((cons h t)  (+ h (sum t)))))))
    (sum (list 1 2 3 4 5 6 7 8 9 10))))
```

Run: `python sum.py` → `55`

### 6.3 List Filter — combining all major extensions

```scheme
(l3 ()
  (letrec ((filter (lambda (pred lst)
                     (match lst
                       (nil          (list))
                       ((cons h t)
                         (if (pred h)
                             (cons h (filter pred (cdr lst)))
                             (filter pred (cdr lst)))))))
           (evens (lambda (n) (== (% n 2) 0))))
    (filter evens (list 1 2 3 4 5 6))))
```

Run: `python filter.py` → returns even numbers from the list

### 6.4 Tuple Swap — tuples and tuple pattern matching

```scheme
(l3 (x y)
  (let ((pair (tuple x y)))
    (match pair
      ((tuple a b) (+ (* b 100) a)))))
```

Run: `python swap.py 3 7` → `703`

### 6.5 Boolean Range Check — logical operators and extended comparisons

```scheme
(l3 (n)
  (if (and (>= n 0) (<= n 100))
      1
      0))
```

Run: `python range.py 50` → `1` (in range)  
Run: `python range.py 150` → `0` (out of range)

### 6.6 FizzBuzz — modulo operator and cond

```scheme
(l3 (n)
  (letrec ((fizzbuzz (lambda (x)
                       (cond
                         ((== (% x 15) 0) 0)
                         ((== (% x 3)  0) 3)
                         ((== (% x 5)  0) 5)
                         (else x)))))
    (fizzbuzz n)))
```

Run: `python fizzbuzz.py 15` → `0` (fizzbuzz)  
Run: `python fizzbuzz.py 9` → `3` (fizz)  
Run: `python fizzbuzz.py 10` → `5` (buzz)

---

## 7. Future Implementation Ideas

### 7.1 Exhaustiveness Checking for match

Currently a `match` expression with no matching clause silently returns `0`. A future extension would add a checker pass that verifies at least one pattern is guaranteed to match. A match on an integer with no wildcard or name pattern would be flagged as potentially non-exhaustive.

### 7.2 Named Top-Level Functions (define)

Adding a `define` form similar to Scheme would let users write helper functions at the top level instead of wrapping everything in a single `letrec`. It would desugar to `letrec` before check runs, making it purely a surface-level convenience with no pipeline impact.

```scheme
(l3 (n)
  (define (square x) (* x x))
  (define (cube x) (* x (square x)))
  (cube n))
```

### 7.3 String Type

Adding string literals and basic string operations would make the language much more useful for real programs. Strings could be represented as Python strings directly in `to_python.py`.

### 7.4 Tail Call Optimization

CPS conversion already puts all recursive calls in tail position, but the generated Python code still uses real function calls which can stack overflow on deep recursion. A trampolining pass would allow programs to run on arbitrarily large inputs.

### 7.5 Type Inference

Adding a Hindley-Milner type inference pass would catch type errors at compile time instead of at runtime. It would run between check and uniqify and would require adding type constraints to the AST.

### 7.6 Better Error Messages with Source Positions

Adding source position tracking to the parser and threading positions through the AST would allow the checker to give much more useful error messages with line and column numbers.

---

## 8. Reflection

### What I learned from the course

The most valuable thing this course taught me is how a compiler is just a series of transformations on data structures. Each pass takes an AST of one form and produces an AST of another form, with each pass responsible for eliminating exactly one layer of complexity. Before this course I thought of a compiler as a single large opaque system. Now I see it as a pipeline of small, composable, individually-testable functions.

CPS conversion was the most conceptually challenging topic. The idea that you can represent the entire control flow of a program as function calls, eliminating all notion of a call stack, took a while to click. Once it did, it was genuinely satisfying to see how naturally it handles things like early returns and exceptions.

The distinction between L3, L2, L1, and L0 made something click that I had read about but not really understood before — the difference between a high-level language feature and its low-level implementation. A list in L3 is a natural idea. A list in L0 is two slots in an array with a null sentinel. The compiler bridges that gap one step at a time.

### What I learned from implementing the extensions

The most important lesson from implementing the extensions was to put new features as early in the pipeline as possible. By putting everything in the desugar pass before check, I got to reuse all the existing infrastructure for free. `check`, `uniqify`, `eliminate_letrec`, `cps_convert`, and `close` all required zero changes for any of the new syntax. This is the open-closed principle in practice.

Testing at 100% branch coverage was more useful than I expected. Several times I wrote code that seemed obviously correct but had an edge case I had not considered — an empty list of clauses, a `cond` with no `else`, a tuple with zero elements. The coverage tool forced me to write tests for those cases, and in two instances those tests caught real bugs.

Pattern matching was the most satisfying extension to implement because it required thinking carefully about the desugaring. Getting the scrutinee to evaluate exactly once by binding it to a fresh name, making ConsPattern generate the right Load indices, and handling the wildcard as a pure passthrough all required careful thought. The end result — a clean recursive `desugar_clauses` function — felt elegant.

Working solo on a project this size also taught me a lot about managing complexity. Breaking each extension into small pieces (grammar → syntax → parse → desugar → test) and getting each piece working before moving to the next made what could have been an overwhelming task manageable.