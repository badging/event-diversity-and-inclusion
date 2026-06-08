"""Markdown rendering for the Reviewer Spotlight block."""
from __future__ import annotations

from datetime import datetime

from .categorize import Buckets
from .stats import ReviewerStats


def recognition(total: int) -> str:
    if total <= 5:
        return "🌱 New"
    if total <= 10:
        return "🥉 Bronze"
    if total <= 30:
        return "🥈 Silver"
    if total < 50:
        return "🥇 Gold"
    return "🏆 Platinum"


def _gh_link(login: str) -> str:
    return f"https://github.com/{login}"


def _issues_link(repo: str, login: str) -> str:
    return f"https://github.com/{repo}/issues?q=is:issue+assignee:{login}+is:closed"


def render_active(active: list[ReviewerStats], repo: str) -> str:
    rows = [
        "| Reviewer | Reviews (last 6 months) | Total Reviews | Last Review Date | Last Assigned Date | Badge Level | Events Reviewed |",
        "|----------|-------------------------|---------------|------------------|--------------------|-------------|-----------------|",
    ]
    for s in active:
        rows.append(
            f"| [{s.login}]({_gh_link(s.login)}) | {s.recent} | {s.total} | "
            f"{s.last_review} | {s.last_assigned} | {recognition(s.total)} | "
            f"[View]({_issues_link(repo, s.login)}) |"
        )
    return "\n".join(rows) if len(rows) > 2 else "_No active reviewers yet._"


def render_alumni(alumni: list[ReviewerStats], repo: str) -> str:
    rows = [
        "| Reviewer | Total Reviews | Last Active | Last Assigned Date | Badge Level | Events Reviewed |",
        "|----------|---------------|-------------|--------------------|-------------|-----------------|",
    ]
    for s in alumni:
        rows.append(
            f"| [{s.login}]({_gh_link(s.login)}) | {s.total} | "
            f"{s.last_review or 'N/A'} | {s.last_assigned} | 🎖️ Honour | "
            f"[View]({_issues_link(repo, s.login)}) |"
        )
    return "\n".join(rows) if len(rows) > 2 else "_No past reviewers yet._"


def render_welcome_back(items) -> str:
    if not items:
        return "_No past reviewer has returned recently._"
    return "\n".join(
        f"- @{s.login} returned in {d.strftime('%b %Y')} after a break! 🎉"
        for s, d in items
    )


def render_spotlight(buckets: Buckets, repo: str, now: datetime) -> str:
    return f"""
## ✨Reviewer Spotlight  

### Active Reviewers (last 6 months)  
{render_active(buckets.active, repo)}

---

### Past Reviewers  
{render_alumni(buckets.alumni, repo)}

---

### Welcome Back Highlight  
{render_welcome_back(buckets.welcome_back)}

_Last Updated: {now.strftime('%Y-%m-%d')}_  

"""
