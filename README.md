# Property-Based Testing with Hypothesis

Talk materials for **PyCon HK 2026**: *Property-Based Testing with Hypothesis* by Hon Kwan Shun Quinson.

- **When:** Sat 14 Nov 2026, 12:00–12:30
- **Where:** LW003 (Community), PyCon HK 2026
- **Repo purpose:** runnable demos, a realistic example, and slides for a 30-minute talk.

## What's here

- `slides/talk.md` — the Marp deck: 39 pages, with 34 in the main talk and 5 in the appendix.
- `slides/dist/` — the built HTML and PDF, tracked so they open without a build.
- `src/` and `tests/` — the code behind every slide example.
- `scripts/` — numbered, runnable demos.
- `docs/` — long-form notes on the examples.

The talk's real example is the NumPy Wald-distribution bug from
[PR #29609](https://github.com/numpy/numpy/pull/29609): a Hypothesis property
found negative samples, and the fix changed the numerical formula. The opening
example is a small bank transfer whose fee bypasses the balance check.

Every slide example is backed by runnable code or a test. Point a coding agent
at `tests/` and `docs/` for examples; there is no separate skill to install.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/). The project uses Python 3.13 via
`.python-version`.

```bash
uv sync
uv run pytest
uv run pytest --hypothesis-profile=fast   # quick local run
uv run pytest --hypothesis-profile=ci     # deeper run for CI
uv run python scripts/00_smoke.py
```

### Demos

```bash
uv run python scripts/09_wald_example.py       # main real example
uv run python scripts/10_simple_account.py     # opening account example
uv run python scripts/13_input_space.py        # samples behind the diagram
uv run python scripts/14_shrink_demo.py        # shrinking without pytest
uv run python scripts/11_heap_stateful.py      # appendix: heap counterexample
uv run python scripts/12_ghostwriter.py        # appendix: generated test
uv run python scripts/08_lerp_example.py       # alternative: tolerance bug
uv run python scripts/06_realistic_example.py  # earlier schedule example
uv run python scripts/07_crosshair_schedule.py # earlier CrossHair demo
```

- `09_wald_example.py` reproduces the negative-sample bug, the stable formula,
  and the Hypothesis search.
- `10_simple_account.py` shows the unchecked fee and the minimal
  `amount=0, fee=1` counterexample.
- `13_input_space.py` prints the real `st.floats(0, 100)` samples used in the
  input-space diagram.
- `14_shrink_demo.py` runs a property test without pytest and prints the
  minimal `[100]` failure.
- `11_heap_stateful.py` runs the heap state machine and prints the five-step
  counterexample.
- `12_ghostwriter.py` runs `hypothesis write` on the demo module and
  prints/saves the generated round-trip test.
- `08_lerp_example.py` reproduces the NumPy lerp symmetry failure, the
  default-tolerance failure, the scale-aware fix, and a custom strategy.
- `00_smoke.py` checks both the normal Hypothesis backend and the CrossHair
  symbolic-execution backend.
- `06_realistic_example.py` demonstrates the schedule bug, the Hypothesis
  search, the shrink, and the JSON round trip. Add `--report` for the raw
  `@given` output.
- `07_crosshair_schedule.py` checks the bounded search window with CrossHair.

## Settings profiles

`conftest.py` registers two Hypothesis settings profiles:

- `fast` — 20 examples, no deadline.
- `ci` — the built-in `ci` profile plus `max_examples=1000`.

Select one explicitly:

```bash
uv run pytest --hypothesis-profile=fast
uv run pytest --hypothesis-profile=ci
```

Use `--hypothesis-profile=ci` in CI. The generic `CI` environment variable only
selects Hypothesis's built-in `ci` profile, before `conftest.py` has a chance
to extend it.

## Slides

The deck uses [Marp](https://marp.app/): a single Markdown file rendered to
HTML/PDF.

```bash
npm install
npm run slides:build
npm run slides:pdf     # requires Chrome or Chromium
npm run slides:watch
```

See [`slides/README.md`](slides/README.md) for the Puppeteer/`CHROME_PATH`
workaround when Chrome is not on your `PATH`.

## Layout

```text
docs/        Long-form notes on the examples
scripts/     Numbered, runnable Hypothesis demos
src/         Examples: Wald, lerp, simple account, heap state machine, Ghostwriter demo
tests/       Pytest property tests for the examples
slides/      Marp deck, build config, and tracked exports
scratchpad/  Local-only planning notes (gitignored)
```

## License

MIT License

Copyright (c) 2026 Hon Kwan Shun Quinson

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
USE OR OTHER DEALINGS IN THE SOFTWARE.

The same text is in [`LICENSE`](LICENSE).
