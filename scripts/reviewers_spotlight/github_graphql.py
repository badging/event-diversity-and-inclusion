"""GraphQL client for the GitHub v4 API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

import requests

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# One query, two concerns:
#   - paginate issues by updatedAt desc so we can stop early
#   - pull assignees + AssignedEvent timeline items inline
ISSUES_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  rateLimit { cost remaining resetAt }
  repository(owner: $owner, name: $name) {
    issues(
      first: 50,
      after: $cursor,
      orderBy: {field: UPDATED_AT, direction: DESC}
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        state
        closedAt
        updatedAt
        assignees(first: 20) { nodes { login } }
        timelineItems(first: 100, itemTypes: [ASSIGNED_EVENT]) {
          nodes {
            __typename
            ... on AssignedEvent {
              createdAt
              assignee { ... on User { login } }
            }
          }
        }
      }
    }
  }
}
"""


@dataclass
class GraphQLMetrics:
    """Cumulative cost counters for a run."""
    requests: int = 0
    points: int = 0
    remaining: int | None = None
    pages: list[int] = field(default_factory=list)


class GraphQLClient:
    def __init__(self, token: str, session: requests.Session | None = None):
        self._session = session or requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        })
        self.metrics = GraphQLMetrics()

    def execute(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        resp = self._session.post(
            GITHUB_GRAPHQL_URL,
            json={"query": query, "variables": variables},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        if "errors" in payload:
            raise RuntimeError(f"GraphQL errors: {payload['errors']}")

        rl = payload["data"].get("rateLimit") or {}
        self.metrics.requests += 1
        self.metrics.points += int(rl.get("cost", 0))
        self.metrics.remaining = rl.get("remaining", self.metrics.remaining)
        return payload["data"]


def fetch_issues(
    client: GraphQLClient,
    owner: str,
    name: str,
    stop_before: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield issue nodes newest-first; stop when an issue is older than
    `stop_before` (ISO timestamp) -- saves pages when we only care about a
    recent window."""
    cursor: str | None = None
    while True:
        data = client.execute(
            ISSUES_QUERY,
            {"owner": owner, "name": name, "cursor": cursor},
        )
        page = data["repository"]["issues"]
        nodes = page["nodes"]
        client.metrics.pages.append(len(nodes))

        for issue in nodes:
            yield issue

        if stop_before and nodes and nodes[-1]["updatedAt"] < stop_before:
            return

        if not page["pageInfo"]["hasNextPage"]:
            return
        cursor = page["pageInfo"]["endCursor"]
