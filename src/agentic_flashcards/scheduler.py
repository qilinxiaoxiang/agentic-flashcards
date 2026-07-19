from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class Schedule:
    due_on: str
    interval_days: int
    ease: int
    repetitions: int


def next_schedule(
    *, reviewed_on: str, rating: int, interval_days: int, ease: int, repetitions: int
) -> Schedule:
    """Return a transparent adaptive schedule using integer-only state."""
    day = date.fromisoformat(reviewed_on)
    if rating not in {0, 1, 2, 3}:
        raise ValueError("rating must be 0, 1, 2, or 3")
    if rating == 0:
        next_interval, next_repetitions = 1, 0
    elif repetitions == 0:
        next_interval, next_repetitions = 1, 1
    elif repetitions == 1:
        next_interval, next_repetitions = 3 if rating == 1 else 6, 2
    else:
        multiplier = {1: 110, 2: ease, 3: ease + 20}[rating]
        next_interval = max(1, round(interval_days * multiplier / 100))
        next_repetitions = repetitions + 1
    next_ease = min(300, max(130, ease + {0: -20, 1: -10, 2: 0, 3: 10}[rating]))
    return Schedule(
        due_on=(day + timedelta(days=next_interval)).isoformat(),
        interval_days=next_interval,
        ease=next_ease,
        repetitions=next_repetitions,
    )
