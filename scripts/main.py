"""Entrypoint: GraphQL -> stats -> categorize -> render -> update README"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone

from reviewers_spotlight.categorize import categorize
from reviewers_spotlight.config import load_config
from reviewers_spotlight.github_graphql import GraphQLClient, fetch_issues
from reviewers_spotlight.readme_updater import update_block
from reviewers_spotlight.rendering import render_spotlight
from reviewers_spotlight.stats import build_stats



def main() -> None:
    cfg = load_config()
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(
        days=cfg.window_days
        )
    client = GraphQLClient(cfg.token)
    issues = list(fetch_issues(client, cfg.owner, cfg.name))
    stats = build_stats(issues, window_start)
    buckets = categorize(stats, window_start, now)

    spotlight = render_spotlight(buckets, cfg.repo, now)
    update_block(cfg.readme_path, spotlight)


    m = client.metrics
    print(
        f"GraphQL: {m.requests} requests, {m.points} pts, "
        f"{m.remaining} remaining, {len(issues)} issues processed."
    )


if __name__ == "__main__":
    main()
