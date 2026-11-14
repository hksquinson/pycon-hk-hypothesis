# The NumPy example: lerp symmetry and floating-point tolerance

This example reproduces the failure behind NumPy PR
[#32721](https://github.com/numpy/numpy/pull/32721), reported in issue
[#28125](https://github.com/numpy/numpy/issues/28125).

The NumPy test `test_linear_interpolation_formula_symmetric` asserts that linear
interpolation is symmetric:

```python
left = lerp(a, b, 1 - (1 - t))
right = lerp(b, a, 1 - t)
assert_allclose(left, right)
```

That property is mathematically true. The failure is in the **tolerance**, not
in `lerp`.

## The failing pair

NumPy's CI produced:

```text
t = 0.5
a = 562949953421314.0
b = -562949953421310.9

left  = 1.625
right = 1.5
difference = 0.125
```

The inputs are about `5.6e14` and nearly opposite, so the midpoint is tiny
relative to them. One ULP at that scale is `0.125`: the two calculations differ
by exactly the precision available at the inputs. The default
`assert_allclose(rtol=1e-7, atol=0)` is far too tight for a result of order 1.

## The fix

NumPy PR #32721 changed the assertion to:

```python
atol = max(abs(a), abs(b)) * np.finfo(np.float64).eps * 100
assert_allclose(left, right, atol=atol, rtol=0)
```

The tolerance now scales with the input magnitude. For the pair above it is
`12.5`, comfortably above the `0.125` difference.

## The abstracted module

`src/pycon_hk_hypothesis/lerp.py` keeps the shape of NumPy's `_lerp`:

```python
diff = b - a
if t < 0.5:
    return a + diff * t
return b - diff * (1 - t)
```

It is pure Python floats; the IEEE-754 behaviour is the same as NumPy's
`float64` scalar arithmetic. The regression test pins the exact NumPy pair.

## The custom strategy

The original NumPy test used plain `st.floats`. That found the failure in 2025,
but current Hypothesis float generation does not reliably hit this pair by
chance. `lerp_testing.near_power_of_two()` encodes the dangerous region:

```python
exponent = draw(st.integers(40, 52))
magnitude = 2.0**exponent
a = magnitude + draw(st.floats(-1, 1))
b = -magnitude + draw(st.floats(-1, 1))
```

Straddling a power-of-two boundary makes `b - a` round, which is what produces
the cancellation. This is the custom-strategy lesson: when you know the
dangerous region, describe it directly instead of hoping a general generator
finds it.

## Why this is a good talk example

- It is a real CI failure from a major numerical library.
- The property is intuitive: interpolating one way is the reverse of the other.
- The failure is dramatic and easy to read: `1.625` versus `1.5`.
- The fix teaches a real numerical lesson: exact equality is the wrong
  specification for floating-point code; tolerances must scale with the inputs.
- It is honest about what Hypothesis found: a **test** bug, not a library bug.
  That is still valuable — the test's assumption was wrong.

## What it does not cover

- It does not exercise arrays, dtypes, or `hypothesis.extra.numpy`.
- It does not support a JSON/tool-call round-trip or CrossHair naturally.
- The failure is not data-dependent in the usual “wrong branch” sense; it is a
  numerical-precision boundary.

## Run it

```bash
uv run pytest tests/test_lerp.py
uv run python scripts/08_lerp_example.py
```
