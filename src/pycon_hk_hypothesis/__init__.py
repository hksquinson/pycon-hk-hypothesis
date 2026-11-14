"""Talk materials for Property-Based Testing with Hypothesis (PyCon HK 2026)."""

from pycon_hk_hypothesis.lerp import lerp, scale_aware_atol, symmetric_values
from pycon_hk_hypothesis.schedule import (
    ISO_WEEKDAYS,
    Schedule,
    SchedulePayload,
    UnsatisfiableScheduleError,
    first_offset,
)
from pycon_hk_hypothesis.wald import wald_candidate_old, wald_candidate_stable

__all__ = [
    "ISO_WEEKDAYS",
    "Schedule",
    "SchedulePayload",
    "UnsatisfiableScheduleError",
    "first_offset",
    "lerp",
    "scale_aware_atol",
    "symmetric_values",
    "wald_candidate_old",
    "wald_candidate_stable",
]
