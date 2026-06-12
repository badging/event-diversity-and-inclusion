"""Reviewer Spotlight pipeline.

Modules:
    config            - environment / runtime configuration
    github_graphql    - thin GraphQL client + paginated issue fetcher
    stats             - build per-reviewer aggregates from raw issue data
    categorize        - active / alumni / welcome-back partitioning
    rendering         - markdown rendering of spotlight tables
    readme_updater    - replace the spotlight block inside a markdown file
    notifiers         - pluggable side-channel notifiers (Slack, etc.)
"""
