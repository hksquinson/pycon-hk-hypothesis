---
marp: true
theme: default
paginate: true
title: Property-Based Testing with Hypothesis
---

<style>
section.dense { padding: 40px 60px; font-size: 25px; line-height: 1.3; }
section.dense h1 { font-size: 40px; margin: 0 0 10px; }
section.dense pre { font-size: 0.66em; line-height: 1.1; }
section.tight { padding: 32px 55px; font-size: 24px; line-height: 1.25; }
section.tight h1 { font-size: 38px; margin: 0 0 8px; }
section.tight pre { font-size: 0.64em; line-height: 1.1; }
section.tight ul, section.tight ol { margin: 0.2em 0; }
section.tight li { margin: 0.1em 0; }
section.dense ul, section.dense ol { margin: 0.25em 0; }
section.dense li { margin: 0.15em 0; }
section pre .highlighted-line {
  display: inline-block;
  width: 100%;
  margin: 0 -0.45em;
  padding: 0 0.45em;
  background: #fff3bf;
  border-radius: 3px;
}
</style>

# Property-Based Testing with Hypothesis

**PyCon HK 2026**

Hon Kwan Shun Quinson

---

<!-- _class: lead -->
# Part 1: Motivating Example

---

# Motivating Example

Suppose you are writing a simple banking application:

```python
# Account has id and balance fields
def transfer(src: Account, dst: Account, amount: int, fee: int = 0) -> None:
    if amount < 0 or fee < 0:
        raise ValueError("amount and fee must be non-negative")
    if src.balance < amount:          # Hmm...
        raise ValueError("Insufficient funds")
    src.balance -= amount + fee       # Hmm...
    dst.balance += amount
```

How do you know this is right?

<!--
The two Hmm... lines are the bug: the guard checks `amount`, but the debit is
`amount + fee`. A fee larger than the sender's remaining balance drives it
negative. Do not say this yet; let the audience find it in the property.
Source: src/pycon_hk_hypothesis/simple_account.py (the buggy `transfer`).
-->

---

<!-- _class: dense -->
# Testing

Write a test:

```python
def test_transfer():
    a = Account(1, 100)
    b = Account(2)
    transfer(a, b, 50)
    assert a.balance == 50
    assert b.balance == 50
```

This seems to work... But what about other cases?
- What if the amount is negative?
- What if the fee is non-zero?
- What if I try to transfer more than the balance?

You can write more tests, but it is hard to cover all cases - there are too many possible values for balance and amount, and it is easy to miss edge cases.

---

<!-- _class: dense -->
# What Hypothesis Can Do

With Hypothesis, you can write a single test that covers many cases:

```python {5}
@given(transfers())
def test_transfer(case):
    src, dst, amount, fee = case
    check_transfer(transfer, case)
    assert src.balance >= 0 and dst.balance >= 0
```

- The highlighted line is the property: no transfer may overdraw either
  account.
- `check_transfer` checks the invalid, rejected, and accepted branches.

<!--
Source: src/pycon_hk_hypothesis/simple_account_testing.py.
`check_transfer` is the full contract. The last line repeats its
non-negativity check so the audience sees the property that catches the fee
bug; the helper already asserts it.
The exact-balance checks pass for the buggy transfer; only non-negativity
fails, so that is the assertion to point at when the counterexample appears.
The long branch-visible version is in git history if the audience needs it.
-->

---

<!-- _class: dense -->
# What Hypothesis Found

Hypothesis reports a counterexample:

```python
Failing test case: test_transfer(
    case=(Account(id=0, balance=0), Account(id=1, balance=0), 0, 1),
)
```

- `amount=0, fee=1`: validation check in the current implementation passes because amount is non-negative.
- The fee is debited from an account with zero balance, resulting in a negative balance.
- This is a bug if we do not want negative balances.

<!--
Source: scripts/10_simple_account.py output; src/pycon_hk_hypothesis/simple_account.py.
Run this to show the counterexample:

    uv run pytest tests/test_simple_account.py::test_transfer \
        --runxfail -q --tb=short --hypothesis-seed=0

`--runxfail` is required: the test is marked xfail(strict=True), so without it
pytest reports XFAIL and hides the counterexample Hypothesis found. The script
`uv run python scripts/10_simple_account.py` runs this command and then the
fixed transfer.

The lesson: the bug is not a typo in a random place; it is the boundary where
the contract and the implementation disagree.
-->

---

<!-- _class: dense -->
# The Fix

`withdraw` enforces the balance; `transfer` delegates the debit to it:

```python
class Account:
    def deposit(self, funds):
        self.balance += funds

    def withdraw(self, funds):
        if self.balance < funds:
            raise ValueError("Insufficient funds")
        self.balance -= funds

def transfer(src, dst, amount, fee=0):
    if amount < 0 or fee < 0:
        raise ValueError("amount and fee must be non-negative")
    src.withdraw(amount + fee)   # raises if the sender cannot pay
    dst.deposit(amount)
```

- The fix assumes `withdraw` raises when the balance is insufficient;
  `transfer` passes it `amount + fee`.

---

<!-- _class: lead -->
# Part 2: Hypothesis

---

<!-- _class: dense -->
# Property-Based Testing

- Normal tests check a few specific inputs and outputs, so they cannot cover all cases.
- Property-based testing checks a **wide range of inputs** against a property,
  which can reveal bugs that normal tests miss.
- Hypothesis implements property-based testing in Python to help find bugs in your code.
- Features:
    - Generate random but structured inputs
    - Shrink failing examples to minimal counterexamples
    - Integrate with pytest and other testing frameworks
    - Support for custom strategies and complex data structures
- Used in real-world projects including NumPy, PyTorch, Pandas, etc.

---

# Visualizing the Input Space

<style scoped>
svg { display: block; margin: 0 auto; }
</style>

<div>
<svg viewBox="0 0 1100 330" width="1100" height="330" role="img"
     aria-label="Normal tests check a few hand-picked inputs, including values just outside the range; a property test generates many random inputs and checks them automatically, more densely near the boundaries."
     font-family="Helvetica, Arial, sans-serif">
  <text x="40" y="30" font-size="26" font-weight="700" fill="#222">Normal tests</text>
  <rect x="95" y="140" width="350" height="60" fill="#e9ecef"/>
  <line x1="60" y1="170" x2="480" y2="170" stroke="#333" stroke-width="2"/>
  <line x1="95" y1="163" x2="95" y2="177" stroke="#333" stroke-width="2"/>
  <line x1="270" y1="163" x2="270" y2="177" stroke="#333" stroke-width="2"/>
  <line x1="445" y1="163" x2="445" y2="177" stroke="#333" stroke-width="2"/>
  <text x="95" y="202" font-size="20" fill="#555" text-anchor="middle">0</text>
  <text x="270" y="202" font-size="20" fill="#555" text-anchor="middle">50</text>
  <text x="445" y="202" font-size="20" fill="#555" text-anchor="middle">100</text>
  <g stroke="#333" stroke-width="3">
    <line x1="91.5" y1="150" x2="91.5" y2="190"/>
    <line x1="95.0" y1="150" x2="95.0" y2="190"/>
    <line x1="98.5" y1="150" x2="98.5" y2="190"/>
    <line x1="224.5" y1="150" x2="224.5" y2="190"/>
    <line x1="270.0" y1="150" x2="270.0" y2="190"/>
    <line x1="441.5" y1="150" x2="441.5" y2="190"/>
    <line x1="445.0" y1="150" x2="445.0" y2="190"/>
    <line x1="448.5" y1="150" x2="448.5" y2="190"/>
  </g>
  <text x="270" y="250" font-size="20" fill="#444" text-anchor="middle">a few inputs, <tspan font-weight="700">chosen by hand</tspan></text>
  <text x="270" y="276" font-size="18" fill="#555" text-anchor="middle">-1, 0, 1, 37, 50, 99, 100, 101</text>
  <text x="590" y="30" font-size="26" font-weight="700" fill="#222">Property test</text>
  <rect x="645" y="140" width="350" height="60" fill="#e9ecef"/>
  <line x1="610" y1="170" x2="1030" y2="170" stroke="#333" stroke-width="2"/>
  <line x1="645" y1="163" x2="645" y2="177" stroke="#333" stroke-width="2"/>
  <line x1="820" y1="163" x2="820" y2="177" stroke="#333" stroke-width="2"/>
  <line x1="995" y1="163" x2="995" y2="177" stroke="#333" stroke-width="2"/>
  <text x="645" y="202" font-size="20" fill="#555" text-anchor="middle">0</text>
  <text x="820" y="202" font-size="20" fill="#555" text-anchor="middle">50</text>
  <text x="995" y="202" font-size="20" fill="#555" text-anchor="middle">100</text>
  <g stroke="#333" stroke-width="2" opacity="0.8">
    <line x1="645.0" y1="158" x2="645.0" y2="182"/>
    <line x1="648.5" y1="158" x2="648.5" y2="182"/>
    <line x1="654.7" y1="158" x2="654.7" y2="182"/>
    <line x1="673.1" y1="158" x2="673.1" y2="182"/>
    <line x1="677.3" y1="158" x2="677.3" y2="182"/>
    <line x1="693.0" y1="158" x2="693.0" y2="182"/>
    <line x1="697.7" y1="158" x2="697.7" y2="182"/>
    <line x1="700.4" y1="158" x2="700.4" y2="182"/>
    <line x1="702.6" y1="158" x2="702.6" y2="182"/>
    <line x1="703.1" y1="158" x2="703.1" y2="182"/>
    <line x1="727.5" y1="158" x2="727.5" y2="182"/>
    <line x1="731.8" y1="158" x2="731.8" y2="182"/>
    <line x1="738.5" y1="158" x2="738.5" y2="182"/>
    <line x1="757.3" y1="158" x2="757.3" y2="182"/>
    <line x1="759.2" y1="158" x2="759.2" y2="182"/>
    <line x1="761.3" y1="158" x2="761.3" y2="182"/>
    <line x1="774.6" y1="158" x2="774.6" y2="182"/>
    <line x1="791.4" y1="158" x2="791.4" y2="182"/>
    <line x1="805.3" y1="158" x2="805.3" y2="182"/>
    <line x1="819.3" y1="158" x2="819.3" y2="182"/>
    <line x1="825.0" y1="158" x2="825.0" y2="182"/>
    <line x1="829.5" y1="158" x2="829.5" y2="182"/>
    <line x1="848.0" y1="158" x2="848.0" y2="182"/>
    <line x1="865.6" y1="158" x2="865.6" y2="182"/>
    <line x1="883.8" y1="158" x2="883.8" y2="182"/>
    <line x1="886.7" y1="158" x2="886.7" y2="182"/>
    <line x1="887.0" y1="158" x2="887.0" y2="182"/>
    <line x1="926.8" y1="158" x2="926.8" y2="182"/>
    <line x1="934.6" y1="158" x2="934.6" y2="182"/>
    <line x1="947.6" y1="158" x2="947.6" y2="182"/>
    <line x1="954.6" y1="158" x2="954.6" y2="182"/>
    <line x1="968.3" y1="158" x2="968.3" y2="182"/>
    <line x1="981.2" y1="158" x2="981.2" y2="182"/>
    <line x1="981.4" y1="158" x2="981.4" y2="182"/>
    <line x1="987.8" y1="158" x2="987.8" y2="182"/>
    <line x1="988.9" y1="158" x2="988.9" y2="182"/>
    <line x1="991.5" y1="158" x2="991.5" y2="182"/>
    <line x1="995.0" y1="158" x2="995.0" y2="182"/>
  </g>
  <text x="820" y="250" font-size="20" fill="#444" text-anchor="middle">many random inputs, <tspan font-weight="700">automatically checked</tspan></text>
  <text x="820" y="276" font-size="18" fill="#555" text-anchor="middle">biased toward boundaries</text>
</svg>
</div>

**Hypothesis samples the range** — a finite number of inputs, never every value.

<!--
This is a sketch, not a to-scale picture. The captions make the contrast
explicit: normal tests are **chosen by hand**; the property test's inputs are
**automatically checked**. The left panel is the hand-picked set a careful
programmer might write: -1, 0, 1, 50, 99, 100, 101, plus 37 as an arbitrary
business-rule boundary. Even that list is manual work, and the arbitrary
boundary is easy to miss.

The right panel is a real sample from
`st.floats(min_value=0, max_value=100)`, not hand-placed ticks. Run
`uv run python scripts/13_input_space.py` to reproduce the 48 values
(seed 11) and the SVG x coordinates. Repeated values, especially 0.0, collapse
onto one tick in the drawing.

Hypothesis runs a finite number of samples. `st.integers` upweights the
endpoints and samples across bit widths; `st.floats` also includes `nan`,
`inf`, and `-0.0`. Say "samples, with a bias toward boundaries", not "checks
every value". Shrinking is explained on its own slide later; do not introduce
it here.
Source: Hypothesis docs, "What you can generate" and the `st.integers` /
`st.floats` reference pages.
-->

---

# Writing a Property-Based Test

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_reverse_twice(xs):
    assert list(reversed(list(reversed(xs)))) == xs

test_reverse_twice()   # no pytest: call the test
```

- `@given` turns a normal test into a property test.
- `st.lists(st.integers())` describes a *strategy* for generating lists of integers.
- The assertion is the property: reversing a list twice returns the original list.
- Without pytest: run `python test_reverse.py`.

<!--
Source: Hypothesis tutorial / "What you can generate".
The docs' first example is the encode/decode round-trip:
    @given(st.text())
    def test_decode_inverts_encode(s):
        assert decode(encode(s)) == s
Same shape: a round-trip property. Round-trip is the first property Zac
Hatfield-Dodds recommends.

No pytest: the file ends with `test_reverse_twice()`, and `python
test_reverse.py` runs it. This is the same pattern as
`scripts/14_shrink_demo.py`; with pytest, omit the call and run `pytest`.
-->

---

<!-- _class: dense -->
# Where to Use Property-Based Testing

<style scoped>
table { font-size: 0.8em; }
</style>

| Property | Definition | Example |
|---|---|---|
| Round-trip | two operations undo each other | `json.loads(json.dumps(x)) == x` |
| Invariant | a property true of every valid output | `sorted(xs)` is ordered and a permutation |
| Idempotence | repeating the operation is a no-op | `fmt(fmt(src)) == fmt(src)` |
| Metamorphic | a known input change implies a known output change | `sum(c * x for x in xs) == c * sum(xs)` |
| Equivalence | old and new code agree | `old_code(x) == new_code(x)` |
| Oracle | check the answer with a separate, independent method | validate a Sudoku grid |

- Start where the input space is large and the property is easy to state.
- One function can have several properties: `sorted` is ordered, a permutation,
  and idempotent.
- Keep normal tests for exact regressions; properties cover the space around them.
<!--Removed because it is about pytest.mark.parametrize, which specifies all necessary inputs instead of stating properties I think?-->
<!-- - `pytest.mark.parametrize` is for a short table of known cases: the exact
  input from a bug report, a boundary like `withdraw(0)`, or a business rule. -->

<!--
Source: Zac Hatfield-Dodds 2019 (property tactics); Hypothesis docs.
Ghostwriter can propose round-trip, idempotence, and equivalence properties.
Idempotence repeats the same operation: `f(f(x)) == f(x)`. Metamorphic changes
the input in a known way and predicts how the output changes:
`f(T(x)) == S(f(x))`. A round-trip composes two operations that return the
original value. The oracle checks an answer without recomputing it: a Sudoku
solver is hard, but validating a completed grid is easy. A SAT solver is the
same idea: checking that an assignment satisfies every clause is easy. `sorted`
is also idempotent, so one function can illustrate more than one pattern: the
pattern is the shape of the property, not the function.
Parametrize is explicit: the exact input from a bug report, `withdraw(0)` and
`withdraw(balance)`, or a rule such as "transfers under 10 are free." It gives
clear failure messages and runs fast; properties cover the space around those
cases.
Equivalence is the refactor pattern: two implementations should agree.
Ghostwriter's `--equivalent` option generates it. Oracle is a separate checker,
not a second implementation.
-->

---

<!-- _class: lead -->
# Part 3: Strategies

---

# Strategies: Numerical Values

```python
st.integers()                                  # any integer
st.integers(min_value=0, max_value=100)        # bounded
st.floats()                                    # includes NaN and inf by default
st.floats(allow_nan=False, allow_infinity=False)
st.fractions()
st.decimals()
```

- Bound the domain when the contract has bounds.
- `st.floats()` can generate `nan`, `inf`, and `-0.0`; decide explicitly.

<!--
Source: Hypothesis strategies reference.
Verify:
    @given(st.floats(allow_nan=False, allow_infinity=False))
    def test_finite(x): assert math.isfinite(x)
-->

---

# Strategies: Collections and Text

```python
st.lists(st.integers(), min_size=1, max_size=5)
st.sets(st.integers())
st.dictionaries(st.text(), st.integers())
st.tuples(st.integers(), st.text())

st.text(alphabet="abc")
st.binary()
st.from_regex(r"[a-z]+@[a-z]+\.[a-z]{2,3}")
```

- `min_size` / `max_size` bound collections.
- `unique=True` when duplicates are invalid.
- `st.text()` includes control characters and unusual Unicode.

<!--
Source: Hypothesis strategies reference.
One idea: strategies compose. Lists of tuples of dictionaries are fine.
`st.from_regex()` is the on-ramp to structured strings.
-->

---

# Modifying and Filtering Test Cases

```python
st.integers().map(lambda x: x * 2)              # transform
st.integers().filter(lambda x: x % 2 == 0)      # keep even values

@given(st.integers(), st.integers(min_value=1, max_value=10))
def test_floor_division_lossless(a, b):
    assume(a % b == 0)          # relationship between a and b
    assert (a // b) * b == a
```

- `map` transforms values; `filter` discards values from one strategy.
- `assume` discards the whole test case when a condition is not met.
- Use `assume` for relationships between inputs; `filter` only sees one
  strategy.
- Both can reject too much (`filter_too_much`). Prefer a strategy that only
  generates valid inputs.

<!--
Source: Hypothesis docs, "Adapting strategies" (tutorial/adapting-strategies).
Exact wording:
- "`.filter` lets you filter test inputs from a single strategy. Hypothesis
  also provides an `assume` function for when you need to filter an entire
  test case, based on an arbitrary condition."
- "Where possible, you should use `.filter`. Hypothesis can often rewrite
  simple filters into more efficient sampling methods than rejection sampling,
  and will retry filters several times instead of aborting the entire test case
  (as with `assume`)."
- "For more complex relationships that can't be expressed with `.filter`, use
  `assume`."
- "`assume` lets you skip the test case at any point in the test, even inside
  arbitrarily deep nestings of functions."
The docs' example keeps `assume(a % b == 0)` because it expresses "a more
complicated relationship between `a` and `b`", while `b != 0` moves into
`.filter`. The docs use unbounded integers; `b` is bounded here so the live
demo does not trip `filter_too_much` on the relationship.
-->

---

# Custom Strategies: Recursive Data

```python
import json
from hypothesis import strategies as st

json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(),
    lambda children: st.lists(children)
    | st.dictionaries(st.text(), children),
    max_leaves=5,
)

@given(json_values)
def test_json_round_trip(value):
    assert json.loads(json.dumps(value)) == value
```

In `lambda: children`, `children` is the recursive strategy itself, so the strategy generates lists and dictionaries of other JSON values.

<!--
Source: Hypothesis docs, "Custom strategies" / recursive strategies.
-->

---

# Custom Strategies: `@st.composite`

```python
@st.composite
def ordered_pairs(draw):
    n1 = draw(st.integers())
    n2 = draw(st.integers(min_value=n1))
    return n1, n2

@given(ordered_pairs())
def test_pairs_are_ordered(pair):
    n1, n2 = pair
    assert n1 <= n2
```

- `draw` lets later values depend on earlier ones.
- Use it when fields are correlated, or when `filter` would reject too much.
- You can also use `st.tuples(...).map(sorted)` for this pair, but naming it this way could be easier to read and reuse.

<!--
Source: Hypothesis docs, "Custom strategies" (tutorial/custom-strategies),
"dependent generation" example.
-->

---

<!-- _class: dense -->
# Custom Strategies: `st.data()`

```python
from bisect import bisect_left
from hypothesis import given, strategies as st

@given(st.data())
def test_binary_search_finds_value(data):
    values = sorted(data.draw(st.lists(st.integers(), min_size=1)))
    index = data.draw(st.integers(min_value=0, max_value=len(values) - 1))
    found = bisect_left(values, values[index])
    assert values[found] == values[index]
```

- `st.data()` lets the test draw values while it runs.
- The second draw needs `len(values)`, which exists only after the list is
  drawn and sorted.
- Use it when the test calls a function between draws. Use `@st.composite`
  when the dependency is reusable input generation.

<!--
Source: Hypothesis docs, "Mixing data generation and test code" (`st.data`).
The sequence is draw -> sort -> draw using the length -> binary search ->
assert. The second draw depends on the first draw's result, so it belongs in
the test rather than in a reusable strategy.
-->

---

<!-- _class: dense -->
# Why Hypothesis, Not Just Random Generation?

- A **strategy** describes how to generate inputs: `st.integers()`,
  `st.text()`, `st.lists(st.integers())`.
- You could write a `random` loop yourself, but Hypothesis adds:
  - structured generation for lists, dictionaries, and nested data;
  - a bias toward edge cases: small values, boundaries, and special values;
  - shrinking to a minimal counterexample;
  - replay of saved failures and `--hypothesis-seed`;
  - pytest integration and readable failure reports.
- You describe the input space once; Hypothesis handles generation, shrinking,
  and replay.

<!--
The point: DIY random generation gives a sample. Hypothesis gives a sample plus
edge-case bias, shrinking, replay, and reporting. The strategy is the reusable
description of the input space.
-->

---

<!-- _class: lead -->
# Part 4: Integration and Getting Feedback

---

<!-- _class: dense -->
# Shrinking to a Minimal Counterexample

```python
# shrink_demo.py
@given(st.lists(st.integers()))
def test_sum_below_100(xs):
    assert sum(xs) < 100

test_sum_below_100()   # no pytest: call the test
```

```bash
$ python shrink_demo.py
Failing test case: test_sum_below_100(
    xs=[100],
)
```

- Hypothesis repeatedly tried smaller inputs that still failed, down to one value.
- The shrink is the bug report: `[100]`, not a page of numbers.
- Shrinks often land on a boundary: `0`, `100`, an empty list.
- The account example shrank to `amount=0, fee=1`; the Wald example shrank to
  `mean=1e8, scale=0.171875, z=1.0`.

<!--
Verified with Hypothesis 6.170.9: `uv run python scripts/14_shrink_demo.py`
prints `Failing test case: test_sum_below_100(xs=[100])`.

Without pytest, call the test function yourself; Hypothesis still shrinks and
prints the same failing case. The slide's `shrink_demo.py` is
`scripts/14_shrink_demo.py` in this repo.

With pytest:

    uv run pytest tests/test_slide_examples.py::test_sum_below_100 \
        --runxfail -q --tb=short --hypothesis-seed=0

The test is marked xfail(strict=True) so the suite stays green; `--runxfail`
shows the counterexample.
-->

---

# Test Settings

```python
from hypothesis import given, settings, strategies as st

@settings(max_examples=500, deadline=None)
@given(st.integers())
def test_slow(x):
    ...
```

- `max_examples` trades time for confidence.
- `deadline` caps the elapsed time of one example, not the whole run.
- `deadline=None` for genuinely slow tests; do not hide a performance bug.
- Per-test `@settings` overrides the active profile.

<!--
Source: Hypothesis settings docs and the `settings.deadline` docstring.
The deadline applies to each individual test case (one generated example),
in milliseconds. Exceeding it raises DeadlineExceeded. It is not the total
test runtime, and `max_examples` is the separate count of examples.
The `default` profile sets 200 ms; the `ci` profile disables it. Hypothesis
treats the deadline as a soft limit in some cases to avoid flakiness.
Also: derandomize=True, database=None, backend="crosshair".
-->

---

<!-- _class: dense -->
# Settings Profiles

```python
# conftest.py
from hypothesis import settings

settings.register_profile("fast", max_examples=20, deadline=None)
settings.register_profile(
    "ci", parent=settings.get_profile("ci"), max_examples=1000
)
```

- Built-in `default`: 100 examples, 200 ms deadline per example.
- Built-in `ci`: `derandomize=True`, `deadline=None`, `database=None`,
  `print_blob=True`, and no `too_slow` health check.
- `register_profile(name, ...)` defines a profile. Select it with
  `settings.load_profile("fast")` or `pytest --hypothesis-profile=fast`.
- `parent` is the profile to inherit from: the `ci` line starts from the
  built-in `ci` and overrides only `max_examples`. Select it with
  `--hypothesis-profile=ci`.

<!--
Source: Hypothesis settings docs, "Built-in profiles".
`settings.get_profile("ci")` returns the built-in profile; passing it as
`parent` keeps derandomize, database=None, print_blob, and the health-check
suppression, then overrides max_examples.
Register profiles in conftest.py so pytest loads them before tests run.
-->

---

<!-- _class: dense -->
# Running and Reproducing Tests

```python
@given(st.integers())
@example(123456789)             # pin the regression
def test_with_example(x):
    assert x != 123456789
```

```bash
pytest                              # @given tests are ordinary pytest tests
pytest --hypothesis-seed=1234       # reproduce a failure
pytest --hypothesis-profile=ci      # select a settings profile
```

- `--hypothesis-seed` replays a failure; the example database replays saved
  cases first.
- If it is a pytest test, reproducing is just running `pytest` again.
- `@example(...)` pins an exact case and does not shrink.
- Keep normal tests; add properties next to them, not instead of them.

<!--
Source: Hypothesis database, settings, and pytest integration docs; Zac
Hatfield-Dodds 2019.
`abs(x) > 0` is not used here: Hypothesis samples 0 immediately, so it fails
without `@example` and does not show what pinning buys you. The value
123456789 is the one from the CrossHair slide: random sampling misses it, the
`crosshair` backend finds it symbolically, and `@example` pins it.
Run this to see the pinned failure:

    uv run pytest tests/test_slide_examples.py::test_with_example_fails \
        --runxfail -q

Demo if the room does not know pytest:
1. Open `tests/test_slide_examples.py` and point at a function named `test_*`.
2. Run `uv run pytest tests/test_slide_examples.py -q` to show the green suite.
3. Run `uv run pytest tests/test_slide_examples.py::test_with_example_fails \
       --runxfail -q` to show one failure.
4. Run the same command again to show the same failing case.
No fixtures or plugins are involved: `@given` wraps the function, so the
normal pytest workflow is unchanged.

`@given` works with pytest fixtures and parametrize. Use session-scoped
fixtures: function-scoped fixtures run once per test, not once per input, and
trigger a health check. Profile details are on the Settings Profiles slide.
-->

---

<!-- _class: lead -->
# Part 5: In Practice

---

# LLMs and Property-Based Testing

- LLMs can write the strategies and the first draft of a property, which are
  the slow parts of property-based testing.
- Kiro describes one workflow: a specification becomes Hypothesis tests.
  [Does your code match your spec?](https://kiro.dev/blog/property-based-testing/)
- The next two slides show a concrete case: an LLM proposed the NumPy Wald
  property, a human checked it, and it found a real bug.
- In practice, the LLM proposes and the human checks the property and the
  strategy.

<!--
Sources: Kiro blog + correctness docs; arXiv 2510.09907; arXiv 2307.04346;
NumPy PR #29609.
-->

---

<!-- _class: dense -->
# Real Example: NumPy Wald Distribution

**NumPy PR [#29609](https://github.com/numpy/numpy/pull/29609)**

The Wald distribution describes the time required for a type of random process to reach a threshold condition. 
Because it describes time, the sampled value is always non-negative.

The pre-fix formula, simplified from NumPy's C:

```text
Y = mean * z**2  # z is a standard-normal draw
X = mean + (mean / (2 * scale)) * (Y - sqrt(4 * scale * Y + Y * Y))
```

<!--What is the wald distribution? How is it an inverse of the Gaussian? Why is it used in NumPy?-->

The property that caught the bug:

```python
@given(
    st.floats(min_value=1e8, max_value=1e15),
    st.floats(min_value=0.1, max_value=10.0),
)
def test_wald_negative_values(mean, scale):
    random = Generator(MT19937(1234567890))
    assert all(s >= 0 for s in random.wald(mean, scale, size=1000))
```

<!--
Source: docs/wald-example.md; NumPy PR #29609.
The slide shows the pre-fix formula simplified from `random_wald`; the C
original is in the PR's base commit.
Demo: uv run python scripts/09_wald_example.py
The real test draws mean/scale and runs the RNG; the abstraction draws z
directly so the shrink is deterministic.
-->

---

# Real Example: What Hypothesis Found

Hypothesis finds a counterexample:

```text
mean = 1e8, scale = 0.171875, z = 1.0  ->  Y = 1e8
old formula    = -1.4901161193847656e-08
stable formula =  0.17187500311877102
```

- The failure indicates instability in the old formula.
- Fix: `d = 1 + sqrt(1 + 4 * scale / Y); X = mean * (1 - 2 / d)`.

<!--
Demo outline:
1. Show the old formula and the one-sigma case.
2. This is the shrink from tests/test_wald.py::test_old_formula_is_nonnegative:
   uv run pytest tests/test_wald.py::test_old_formula_is_nonnegative \
       --runxfail -q --tb=short
   scripts/09_wald_example.py shows the same cancellation with a different draw.
3. The three ranges are wald_testing.cancellation_prone(); explain why a
   generic float distribution is the wrong strategy.
4. Show the stable formula and the passing property.
5. Say clearly: this found a counterexample, not a proof.
Source: src/pycon_hk_hypothesis/wald.py, wald_testing.py.
-->

---

<!-- _class: lead -->
# Part 6: Limitations and Conclusion

---

# Limitations

- A property that is too general can pass while the code is wrong.
  - For example, `assert isinstance(add(a, b), int)` passes even if `add`
    subtracts: the type is right, the answer is not.
- PBT samples inputs: it finds counterexamples, not proofs.
- More input coverage costs more testing time. Tune `max_examples` and profiles.
- Not every requirement is a property; use normal tests for exact regressions.

<!--
Sources: Emma Saroyan 2025 (limitations); Kiro correctness docs ("not formal
verification"); Hypothesis docs.

The account property needs both conservation and non-negativity: conservation
alone passes on the buggy transfer.
The Wald test draws `z` directly so the failure is deterministic.
Use a fast local profile and a deeper CI profile; `max_examples` is the main
cost knob.
-->

---

# Conclusion

- Normal tests cover the cases you thought of; properties check the rule over
  many inputs.
- Hypothesis generates inputs, shrinks failures, and works with pytest.
- After today, add Hypothesis to one project, and point your coding agent at
  the Hypothesis docs and this talk's repo tests.

Try it out!

<!--
The docs and this talk's repo tests are the examples the agent can read; there
is no agent skill to install. The docs and repo links are on the References and
Thank You slides.
-->

---

<!-- _class: tight -->
# References and AI Use

**Sources**
- Hypothesis documentation: [https://hypothesis.readthedocs.io/](https://hypothesis.readthedocs.io/)
- PyCon talks:
    - Zac Hatfield-Dodds, *Escape from auto-manual testing with Hypothesis!* (PyCon US 2019): [https://www.youtube.com/watch?v=KcyGUVzL7HA](https://www.youtube.com/watch?v=KcyGUVzL7HA)
    - Cheuk Ting Ho, *I hate writing tests, that's why I use Hypothesis* (PyCon UK 2022): [https://www.youtube.com/watch?v=A_Ow-XdmyLU](https://www.youtube.com/watch?v=A_Ow-XdmyLU)
    - Florian Bruhin, *Property based testing with Hypothesis* (SPS 2024): [https://www.youtube.com/watch?v=6a1RvMKj0ws](https://www.youtube.com/watch?v=6a1RvMKj0ws)
    - Emma Saroyan, *Property-based testing the Python way* (PyCon Portugal 2025): [https://www.youtube.com/watch?v=x_aquLINszU](https://www.youtube.com/watch?v=x_aquLINszU)
- NumPy PR #29609: [https://github.com/numpy/numpy/pull/29609](https://github.com/numpy/numpy/pull/29609)
- Kiro: [https://kiro.dev/blog/property-based-testing](https://kiro.dev/blog/property-based-testing) and [https://kiro.dev/docs/specs/correctness](https://kiro.dev/docs/specs/correctness)
- The Fuzzing Book: [https://www.fuzzingbook.org/](https://www.fuzzingbook.org/)
- My repository: [https://github.com/hksquinson/pycon-hk-hypothesis](https://github.com/hksquinson/pycon-hk-hypothesis)

**AI use:** Slides and demos were drafted with AI assistance and reviewed
by the speaker.

<!--
Answer "is it weird to mention AI use?" — no; transparency is better than a
surprise. Keep the vendor-neutral framing.
-->

---

# Thank You!

<div style="display: flex; align-items: center; gap: 48px; margin-top: 48px;">
  <div style="flex: 1;">
    <p>Happy to take questions!</p>
    <p>Repo: <a href="https://github.com/hksquinson/pycon-hk-hypothesis">https://github.com/hksquinson/pycon-hk-hypothesis</a></p>
  </div>
  <figure style="margin: 0; text-align: center;">
    <img src="repo-qr.svg" alt="QR code for the talk repository" width="240">
    <figcaption style="font-size: 20px; color: #555; margin-top: 8px;">Scan for the repo</figcaption>
  </figure>
</div>

<!--
The QR code encodes the same repository URL printed on the slide. It was
generated with segno; the SVG is slides/repo-qr.svg.
-->


---

# Additional Slides

---

<!-- _class: dense -->
# Stateful Testing: Rules

```python
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, precondition, rule

class HeapMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.heap = []

    @rule(value=st.integers())
    def push(self, value):
        heappush(self.heap, value)

    @precondition(lambda self: self.heap)
    @rule()
    def pop(self):
        correct = min(self.heap)
        assert heappop(self.heap) == correct
```

- Generates a **sequence of operations**, not one input.
- `@precondition` prevents popping an empty heap.
- `Bundle`, `@initialize`, `@invariant` extend the same idea.

<!--
Source: Hypothesis blog, "Rule Based Stateful Testing" (2016-04-19), heap example.
Optional section; repo-only bonus if time is short.
-->

---

# Stateful Testing: The Counterexample

```text
Failing test case: <state machine>
E       state = HeapMachine()
E       state.push(value=0)
E       state.push(value=1)
E       state.push(value=0)
E       state.pop()
E       state.pop()
E       state.teardown()
```

- The second `pop()` returns 1, but the heap still contains 0.
- The bug: `heappop` is `heap.pop(0)` without rebalancing.
- The fix: sift the last element down after removing the root.

<!--
The blog's sequence is push(1), push(0), push(0), pop, pop; this machine
shrinks to the same shape with a different push order. The exact blog sequence
is pinned in tests/test_heap_stateful.py.
Run: uv run pytest tests/test_heap_stateful.py --runxfail
Plain pytest reports XFAIL; --runxfail shows the counterexample.
-->

---

<!-- _class: dense -->
# Ghostwriter: Automated Testing without LLMs

```bash
hypothesis write \
  pycon_hk_hypothesis.ghostwriter_demo.encode \
  pycon_hk_hypothesis.ghostwriter_demo.decode \
  --roundtrip
```

`scripts/12_ghostwriter.py` runs that command and saves the generated test.
The generated test:

```python
@given(data=st.binary(), text=st.text())
def test_roundtrip_encode_decode(data: bytes, text: str) -> None:
    value0 = pycon_hk_hypothesis.ghostwriter_demo.encode(text=text)
    value1 = pycon_hk_hypothesis.ghostwriter_demo.decode(data=value0)
    assert text == value1, (text, value1)
```

- It is a starting point: review the property, choose the strategy, run it.
- Property styles: `--roundtrip`, `--idempotent`, `--equivalent`, `--binary-op`.

<!--
Run: uv run python scripts/12_ghostwriter.py
Source: Hypothesis Ghostwriter docs; Cheuk Ting Ho 2022.
Optional slide; move after the end if time is short.
-->

---

# CrossHair: Sampled vs Explored

```python
from hypothesis import given, settings, strategies as st

@settings(backend="crosshair", deadline=None)
@given(st.integers())
def test_solver(x):
    assert x != 123456789
```

- Default backend: Hypothesis samples inputs.
- `backend="crosshair"`: symbolic execution treats inputs as unknowns and
  asks a solver for a value that breaks the assertion.
- It finds `x=123456789`; random sampling essentially never would.
- Not a proof: bounded inputs, pure functions, solver limits.

<!--
Source: Hypothesis CrossHair docs; Fuzzing Book symbolic-execution chapter.
Appendix slide; after the talk if time allows.
-->
