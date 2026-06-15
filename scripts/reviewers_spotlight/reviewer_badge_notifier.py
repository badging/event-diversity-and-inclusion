import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import time
from slack_sdk import WebClient
from reviewers_spotlight.rendering import recognition
from reviewers_spotlight.config import load_config
from reviewers_spotlight.github_graphql import GraphQLClient, fetch_issues
from reviewers_spotlight.stats import build_stats

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
COMMUNITY_MANAGER_ID = os.getenv("COMMUNITY_MANAGER_ID")

STATE_FILE = "badge_state.json"

client = WebClient(token=SLACK_BOT_TOKEN)

BADGE_ORDER = ["🌱 New", "🥉 Bronze", "🥈 Silver", "🥇 Gold", "🏆 Platinum"]


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
    try:
        resp = client.chat_postMessage(
            channel=COMMUNITY_MANAGER_ID, 
            text=message
        )
        return resp.get("ok", False)
    except Exception as e:
        print(f"DM failed: {e}")
        return False


def fetch_reviewer_stats():
    config = load_config()
    client = GraphQLClient(config.token)

    now = datetime.now(timezone.utc)
    six_months_ago = now - timedelta(days=config.window_days)

    issues = fetch_issues(client, config.owner, config.name)
    return build_stats(issues, six_months_ago)


def send_notifications():
    state = load_state()
    stats = fetch_reviewer_stats()

    for username, data in stats.items():
        badge = recognition(data.total)
        old_badge = state.get(username)

        if old_badge is None:
            state[username] = badge
        elif is_upgrade(old_badge, badge):
            
            ok_public = False
            try:
                ok_public = send_public(username, badge)
            except Exception as e:
                print(f"Failed to send public notification for {username}: {e}")

            time.sleep(0.5)
            
            ok_dm = False
            try:
                ok_dm = send_dm(username, badge)
            except Exception as e:
                print(f"Failed to send DM for {username}: {e}")

            if ok_public and ok_dm:
                state[username] = badge
        else:
            # No upgrade or downgrade
            pass

    save_state(state)

if __name__ == "__main__":
    send_notifications()
