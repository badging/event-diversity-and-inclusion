import os
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import time
from slack_sdk import WebClient
from reviewers_spotlight.rendering import recognition
from pathlib import Path

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
COMMUNITY_MANAGER_ID = os.getenv("COMMUNITY_MANAGER_ID")

client = WebClient(token=SLACK_BOT_TOKEN)

BADGE_ORDER = ["🌱 New", "🥉 Bronze", "🥈 Silver", "🥇 Gold", "🏆 Platinum"]

def extract_old_badges(readme_path: str) -> dict[str, str]:
    old_badges = {}
    p = Path(readme_path)
    if not p.exists():
        return old_badges
    
    content = p.read_text(encoding="utf-8")
    in_active = False
    in_alumni = False
    
    for line in content.splitlines():
        if "### Active Reviewers" in line:
            in_active = True
            in_alumni = False
        elif "### Past Reviewers" in line:
            in_alumni = True
            in_active = False
            
        if line.strip().startswith('| [') and ' | ' in line:
            parts = [x.strip() for x in line.split('|')]
            login_match = re.search(r'\[([^\]]+)\]', parts[1])
            if login_match:
                login = login_match.group(1)
                try:
                    if in_active:
                        total = int(parts[3])
                    elif in_alumni:
                        total = int(parts[2])
                    else:
                        continue
                    old_badges[login] = recognition(total)
                except (ValueError, IndexError):
                    pass
    return old_badges


# Helper to determine if a badge upgrade occurred
def is_upgrade(old: str | None, new: str) -> bool:
    if old is None:
        return False 
    return BADGE_ORDER.index(new) > BADGE_ORDER.index(old)

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

def send_notifications(stats, old_badges: dict):
    notified_count = 0
    for username, data in stats.items():
        badge = recognition(data.total)
        old_badge = old_badges.get(username)

        if old_badge is None:
            # First time seeing this reviewer, no notification to avoid spam
            pass
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
                notified_count += 1
        else:
            # No upgrade or downgrade
            pass

    print(f"Notifications: {notified_count} upgrades processed and notified to Slack.")

