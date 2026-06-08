"""Split reviewers into active / alumni / welcome-back groups."""
from __future__ import annotations

from dataclasses import dataclass
from .config import load_config
from datetime import datetime, timedelta

from .stats import ReviewerStats

# Welcome-back banner only shows reviewers whose return is still fresh.
WELCOME_BACK_MAX_AGE = timedelta(days=30)


@dataclass
class Buckets:
    active: list[ReviewerStats]
    alumni: list[ReviewerStats]
    welcome_back: list[tuple[ReviewerStats, "datetime.date"]]


def categorize(
    stats: dict[str, ReviewerStats],
    window_start: datetime,
    now: datetime,
) -> Buckets:
    active: list[ReviewerStats] = []
    alumni: list[ReviewerStats] = []
    welcome_back: list[tuple[ReviewerStats, "datetime.date"]] = []
    # window = timedelta(days=(datetime.now(window_start.tzinfo) - window_start).days)
    window = now - window_start
    # today = datetime.now(window_start.tzinfo).date()
    today = now.date()

    for s in stats.values():
        if s.last_review and s.last_review >= window_start.date():
            active.append(s)
            dates = sorted(s.review_dates)
            if (
                len(dates) >= 2
                and (dates[-1] - dates[-2]) > window
                and (today - s.last_review) <= WELCOME_BACK_MAX_AGE
            ):
                welcome_back.append((s, s.last_review))
        else:
            alumni.append(s)

    active.sort(key=lambda s: -s.total)
    alumni.sort(key=lambda s: -s.total)
    return Buckets(active=active, alumni=alumni, welcome_back=welcome_back)
