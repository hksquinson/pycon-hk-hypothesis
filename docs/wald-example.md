# The NumPy example: negative Wald samples

This example reproduces the bug fixed by NumPy PR
[#29609](https://github.com/numpy/numpy/pull/29609). Unlike the lerp example,
this one is a **code bug**, not a test-tolerance bug: the fix changes the
computation itself.

## The real test

The PR was prompted by a Hypothesis property proposed and written by an LLM
agent, then verified and fixed by a human. The test was essentially:

```python
@given(
    st.floats(min_value=1e8, max_value=1e15),
    st.floats(min_value=0.1, max_value=10.0),
)
@settings(max_examples=50)
def test_wald_negative_values(mean, scale):
    random = Generator(MT19937(1234567890))
    samples = random.wald(mean, scale, size=1000)
    assert all(s >= 0 for s in samples), f"negative sample: {mean=}, {scale=}"
```

The property is simple: **a Wald-distributed sample must never be negative.**
It failed.

## The bug

NumPy's `random_wald` computed a candidate from a standard-normal draw `Z`:

```c
Y = mean * Z * Z;
X = mean + (mean / (2 * scale)) * (Y - sqrt(4 * scale * Y + Y * Y));
```

When `Y >> scale`, the two terms inside the parentheses nearly cancel. The
result is the difference of two large, nearly equal numbers, so the low bits
are lost and the candidate can come out negative.

A one-sigma draw is enough:

```text
mean  = 1e8
scale = 0.1
z     = 1.0     -> Y = 1e8

old formula    = -1.4901161193847656
stable formula =  0.1000000082740371
```

The negative candidate is not rescued by the acceptance step; it can be
returned as a negative sample.

## The fix

The PR replaced the formula with an algebraically equivalent, numerically
stable form:

```c
d = 1 + sqrt(1 + 4 * scale / Y);
X = mean * (1 - 2 / d);
```

This avoids subtracting nearly equal large numbers. The property test then
passes over the generated range.

## The abstraction

`src/pycon_hk_hypothesis/wald.py` keeps the old and new formulas. The
abstraction draws `(mean, scale, z)` directly instead of running the RNG and
the acceptance step:

- `Y = mean * z**2` is the same transformation of a standard-normal draw.
- `wald_candidate_old` is the pre-fix formula.
- `wald_candidate_stable` is the post-fix formula.
- The property is `candidate >= 0`.

`wald_testing.wald_inputs()` covers the PR's ranges;
`cancellation_prone()` biases toward `Y >> scale`, which is the custom-strategy
lesson: encode the dangerous region instead of hoping a general float
distribution finds it.

## Why this example is compelling

- It is a real code bug in a major numerical library.
- The fix changes the implementation, not the test tolerance.
- The property is intuitive and the failure is dramatic.
- An LLM agent wrote the property that found it; a human verified and fixed the
  bug. That is a concrete LLM-assisted development story, not a generic claim.
- The failure is a numerical-stability lesson: algebraically equivalent
  formulas are not numerically equivalent.

## What it does not cover

- It does not run the C implementation or the full RNG pipeline; it isolates the
  numerical core.
- It does not support a JSON/tool-call round-trip or CrossHair naturally.
- The real test is stochastic; the abstraction draws the normal value directly
  so the failure is deterministic and the shrink is readable.

## Run it

```bash
uv run pytest tests/test_wald.py
uv run python scripts/09_wald_example.py
```
