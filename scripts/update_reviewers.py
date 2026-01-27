import os
from datetime import datetime, timedelta, timezone, time
from github import Github, Auth

# GitHub auth
token = os.getenv("GITHUB_TOKEN")
repo_name = os.getenv("GITHUB_REPO", "badging/event-diversity-and-inclusion")

token = os.getenv("GITHUB_TOKEN")
if not token:
    raise RuntimeError("Missing GITHUB_TOKEN")

g = Github(auth=Auth.Token(token))
repo = g.get_repo(repo_name)

# Test mode (set reviewers you want to track)
#TEST_REVIEWERS = os.getenv("TEST_REVIEWERS", "").split(",")
now = datetime.now(timezone.utc)
six_months_ago = now - timedelta(days=180)

reviewer_stats = {}

# Collect issues closed (last 6 months and beyond)
for issue in repo.get_issues(state="closed"):
    if issue.assignees:
        for assignee in issue.assignees:
            name = assignee.login
            # if TEST_REVIEWERS and name not in TEST_REVIEWERS:
            #  continue
            if name not in reviewer_stats:
                reviewer_stats[name] = {
                    "recent": 0,
                    "total": 0,
                    "last": None,
                    "dates": [],  # track all review dates
                    "last_assigned": None # track last assigned dates
                }
            reviewer_stats[name]["total"] += 1
            if issue.closed_at >= six_months_ago:
                reviewer_stats[name]["recent"] += 1
            reviewer_stats[name]["dates"].append(issue.closed_at)
            if (
                not reviewer_stats[name]["last"]
                or issue.closed_at > datetime.combine(reviewer_stats[name]["last"], time.min).replace(tzinfo=timezone.utc)
            ):
                reviewer_stats[name]["last"] = issue.closed_at.date()

# Retrieve currently assigned tasks from open issues
issue_tracker_main = {} # tracks each assignee's last active assignment
# Collect open issues
for issue in repo.get_issues(state = 'open'):
    issue_tracker_sub = {} # tracks last event per assignee for this issue
    for event in issue.get_timeline():
        # Only process assignment-related events
        if event.event in ['assigned', 'unassigned']:
            name = event.raw_data['assignee']['login']
            event_date = event.created_at.date()

            # Keep the latest event per assignee for this issue
            if (
                name not in issue_tracker_sub 
                or event_date >= issue_tracker_sub[name]['event_date']
                ):
                issue_tracker_sub[name] = {'status': event.event, 'event_date': event_date}

    # Merge this issue's sub-tracker into the main tracker
    for name, info in issue_tracker_sub.items():
        if name not in issue_tracker_main:
            # Add new assignee
            issue_tracker_main[name] = info
        else:
            # Update main only if this is an active assignment
            current = issue_tracker_main[name]
            if info['status'] == 'assigned' and (current['status'] == 'unassigned' 
            or info['event_date'] > current['event_date']):
                    issue_tracker_main[name] = info

# Update each assignee’s last assigned date if they are currently assigned
for name in issue_tracker_main:
    if (
        issue_tracker_main[name]['status'] == 'assigned' 
        and name in reviewer_stats
        ):
        reviewer_stats[name]['last_assigned'] = issue_tracker_main[name]['event_date']

# Split Active / Alumni / Welcome Back
active, alumni, welcome_back = [], [], []
six_months = timedelta(days=180)

for reviewer, stats in reviewer_stats.items():
    dates = sorted(stats["dates"])
    last_active = stats["last"]

    if last_active and last_active >= six_months_ago.date():
        # Active by default
        active.append((reviewer, stats))

        # Detect welcome_back = reviewer had a gap > 6 months, then returned
        if len(dates) >= 2:
            gap = dates[-1] - dates[-2]
            if gap > six_months:
                welcome_back.append((reviewer, last_active))

    else:
        alumni.append((reviewer, stats))

# Recognition levels
def recognition(total):
    if total <= 5:
        return "🌱 New"
    elif total <= 10:
        return "🥉 Bronze"
    elif total <= 30:
        return "🥈 Silver"
    elif total < 50:
        return "🥇 Gold"
    else:
        return "🏆 Platinum"


# Build tables
# def table_active():
#     rows = ["| Reviewer | Reviews (Last 6 mo) | Total Reviews | Last Review Date | Recognition Level |",
#             "|----------|----------------------|---------------|------------------|-------------------|"]
#     for r, s in active:
#         rows.append(f"| @{r} | {s['recent']} | {s['total']} | {s['last']} | {recognition(s['total'])} |")
#     return "\n".join(rows) if len(rows) > 2 else "_No active reviewers yet._"

def table_active():
    rows = ["| Reviewer | Reviews (last 6 months) | Total Reviews | Last Review Date | Last Assigned Date | Badge Level | Events Reviewed |",
            "|----------|-------------------------|---------------|------------------|--------------------|-------------|---------------- |"]
    for r, s in sorted(active, key=lambda x: -x[1]['total']):
        try:
            user = repo.get_user(r.lstrip('@'))
            full_name = user.name or "N/A"
        except Exception:
            full_name = "N/A"

        github_link = f"https://github.com/{r.lstrip('@')}"
        # Link to all closed issues ever assigned to this reviewer
        issues_link = f"https://github.com/{repo_name}/issues?q=is:issue+assignee:{r.lstrip('@')}+is:closed"

        rows.append(
            f"| [{r}]({github_link}) | {s['recent']} | {s['total']} | {s['last']} | {s['last_assigned']} | {recognition(s['total'])} | [View]({issues_link})"
        )
    return "\n".join(rows) if len(rows) > 2 else "_No active reviewers yet._"


def table_alumni():
    rows = ["| Reviewer | Total Reviews | Last Active | Last Assigned Date |Badge Level | Events Reviewed |",
            "|----------|---------------|-------------|--------------------|------------|-----------------|"]
    for r, s in sorted(alumni, key=lambda x: -x[1]['total']):
        try:
            user = repo.get_user(r.lstrip('@'))
            full_name = user.name or "N/A"
        except Exception:
            full_name = "N/A"

        github_link = f"https://github.com/{r.lstrip('@')}"
        # Link to all closed issues ever assigned
        issues_link = f"https://github.com/{repo_name}/issues?q=is:issue+assignee:{r.lstrip('@')}+is:closed"
        last = s['last'] or "N/A"

        rows.append(
            f"| [{r}]({github_link}) | {s['total']} | {last} | {s['last_assigned']} | 🎖️ Honour | [View]({issues_link})"
        )
    return "\n".join(rows) if len(rows) > 2 else "_No past reviewers yet._"



def list_welcome_back():
    if not welcome_back:
        return "_No past reviewer has returned recently._"
    return "\n".join([f"- @{r} returned in {d.strftime('%b %Y')} after a break! 🎉" for r, d in welcome_back])

# def table_debug_dates():
#     rows = ["<!--", "### 🐞 Debug Reviewer Dates (raw)", "| Reviewer | Review Dates |", "|----------|--------------|"]
#     for r, s in reviewer_stats.items():
#         date_list = ", ".join([d.strftime("%Y-%m-%d") for d in sorted(s['dates'])])
#         rows.append(f"| @{r} | {date_list} |")
#     rows.append("-->")
#     return "\n".join(rows)


spotlight = f"""
## ✨Reviewer Spotlight  

### Active Reviewers (last 6 months)  
{table_active()}

---

### Past Reviewers  
{table_alumni()}

---

### Welcome Back Highlight  
{list_welcome_back()}

_Last Updated: {now.strftime('%Y-%m-%d')}_  


"""
# {table_debug_dates()}

# Update README
with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

start = "<!-- REVIEWER_SPOTLIGHT_START -->"
end = "<!-- REVIEWER_SPOTLIGHT_END -->"
before = content.split(start)[0]
after = content.split(end)[1]
new_content = f"{before}{start}\n{spotlight}\n{end}{after}"

with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_content)

