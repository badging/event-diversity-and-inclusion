"""Aggregate raw issue/timeline data into per-reviewer statistics."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Iterable

# Issues not related to badging application are ignored.
_IN_PERSON_RE = re.compile(r"in[- ]person.*event")
_VIRTUAL_RE = re.compile(r"virtual.*event")
_BADGE_RE = re.compile(r"event.*badge.*submission")


def classify_issue(title: str | None) -> str | None:
    """Return 'IN-PERSON' | 'VIRTUAL' | 'BADGE', or None for non-review issues."""
    if not title:
        return None
    t = title.lower()
    if _IN_PERSON_RE.search(t):
        return "IN-PERSON"
    if _VIRTUAL_RE.search(t):
        return "VIRTUAL"
    if _BADGE_RE.search(t):
        return "BADGE"
    return None


@dataclass
class ReviewerStats:
    login: str
    recent: int = 0
    total: int = 0
    last_review: date | None = None
    last_assigned: date | None = None
    review_dates: list[datetime] = field(default_factory=list)


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    # GitHub returns trailing 'Z'; fromisoformat handles +00:00
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def build_stats(
    issues: Iterable[dict],
    window_start: datetime,
) -> dict[str, ReviewerStats]:
    """Walk issue nodes (GraphQL shape) and accumulate per-login counters."""
    stats: dict[str, ReviewerStats] = {}

    def slot(login: str) -> ReviewerStats:
        s = stats.get(login)
        if s is None:
            s = stats[login] = ReviewerStats(login=login)
        return s

    for issue in issues:
        if classify_issue(issue.get("title")) is None:
            continue
        closed = _parse(issue.get("closedAt"))
        assignees = [a["login"] for a in issue["assignees"]["nodes"]]

        # A closed issue counts as a review for every current assignee
        if closed:
            for login in assignees:
                s = slot(login)
                s.total += 1
                s.review_dates.append(closed)
                if closed >= window_start:
                    s.recent += 1
                cd = closed.date()
                if not s.last_review or cd > s.last_review:
                    s.last_review = cd

        # Track last assignment from AssignedEvent timeline
        for ev in issue["timelineItems"]["nodes"]:
            if ev.get("__typename") != "AssignedEvent":
                continue
            assignee = ev.get("assignee") or {}
            login = assignee.get("login")
            if not login:
                continue
            created = _parse(ev["createdAt"])
            if not created:
                continue
            s = slot(login)
            ad = created.date()
            if not s.last_assigned or ad > s.last_assigned:
                s.last_assigned = ad

    return stats
