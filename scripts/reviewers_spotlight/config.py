"""Runtime configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class Config:
    token: str
    repo: str           # "owner/name"
    readme_path: str
    window_days: int

    @property
    def owner(self) -> str:
        return self.repo.split("/", 1)[0]

    @property
    def name(self) -> str:
        return self.repo.split("/", 1)[1]



def load_config() -> Config:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Missing GITHUB_TOKEN")
    return Config(
        token=token,
        repo=os.getenv("GITHUB_REPO", "badging/event-diversity-and-inclusion"),
        readme_path=os.getenv("README_PATH", "README.md"),
        window_days=int(os.getenv("WINDOW_DAYS", "180")),
    )
