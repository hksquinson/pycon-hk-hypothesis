"""Hypothesis settings profiles used by the talk.

Select a profile from the command line:

    uv run pytest --hypothesis-profile=fast
    uv run pytest --hypothesis-profile=ci

``fast`` is for quick local runs. ``ci`` extends the built-in CI profile,
keeping derandomization, the disabled database, blob printing, and the
suppressed ``too_slow`` health check, then raises ``max_examples``.
"""

from __future__ import annotations

from hypothesis import settings

settings.register_profile("fast", max_examples=20, deadline=None)
settings.register_profile("ci", parent=settings.get_profile("ci"), max_examples=1000)
