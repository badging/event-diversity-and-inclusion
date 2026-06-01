import os
import json
from dotenv import load_dotenv
from github import Github, Auth
from datetime import datetime, timedelta, timezone
import time
from slack_sdk import WebClient

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "badging/event-diversity-and-inclusion")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
COMMUNITY_MANAGER_ID = os.getenv("COMMUNITY_MANAGER_ID")

STATE_FILE = "badge_state.json"

client = WebClient(token=SLACK_BOT_TOKEN)

if not GITHUB_TOKEN:
    raise RuntimeError("Missing GITHUB_TOKEN")

BADGE_ORDER = ["🌱 New", "🥉 Bronze", "🥈 Silver", "🥇 Gold", "🏆 Platinum"]

def get_badge(total: int) -> str:
    if total <= 5:
        return "🌱 New"
    elif total <= 10:
        return "🥉 Bronze"
    elif total <= 30:
        return "🥈 Silver"
    elif total < 50:
        return "🥇 Gold"
    return "🏆 Platinum"

# Helper to determine if a badge upgrade occurred
def is_upgrade(old: str | None, new: str) -> bool:
    if old is None:
        return False 
    return BADGE_ORDER.index(new) > BADGE_ORDER.index(old)

# State management for tracking badges and notifications
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# notify the slack channel and DM the community manager if a badge upgrade occurred
def send_public(username, badge):
    message = f"""
🥳 Big news! Reviewer @{username} has just leveled up to {badge}!

👏 Amazing work, @{username} — keep shining!
"""
    resp = client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=message)
    return resp.get("ok", False)

def send_dm(username, badge):
    message = f"""
Hi <@{COMMUNITY_MANAGER_ID}> 👋

Reviewer @{username} reached {badge} 🎉
"""
    resp = client.chat_postMessage(channel=COMMUNITY_MANAGER_ID, text=message)
    return resp.get("ok", False)


def fetch_reviewer_stats():
    g = Github(auth=Auth.Token(GITHUB_TOKEN))
    repo = g.get_repo(GITHUB_REPO)

    now = datetime.now(timezone.utc)
    six_months_ago = now - timedelta(days=180)

    stats = {}

    for issue in repo.get_issues(state="closed"):
        if not issue.assignees:
            continue

        for assignee in issue.assignees:
            name = assignee.login

            if name not in stats:
                stats[name] = {
                    "total": 0,
                    "recent": 0,
                    "dates": [],
                    "last": None,
                }

            stats[name]["total"] += 1

            if issue.closed_at >= six_months_ago:
                stats[name]["recent"] += 1

            stats[name]["dates"].append(issue.closed_at)

            if not stats[name]["last"] or issue.closed_at > stats[name]["last"]:
                stats[name]["last"] = issue.closed_at

    return stats


def send_notifications():
    state = load_state()
    stats = fetch_reviewer_stats()

    for username, data in stats.items():
        badge = get_badge(data["total"])
        old_badge = state.get(username)

        if is_upgrade(old_badge, badge):
            try:
                ok_public = send_public(username, badge)
                time.sleep(0.5)
                ok_dm = send_dm(username, badge)

                if ok_public and ok_dm:
                    state[username] = badge
                else:
                    print(
                        f"Slack send failed for {username}: public={ok_public}, dm={ok_dm}"
                    )

            except Exception as e:
                print(f"Failed to notify {username}: {e}")

    save_state(state)

if __name__ == "__main__":
    send_notifications()
