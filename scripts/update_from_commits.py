#!/usr/bin/env python3
"""Fetch recent commits from PE repos and add new activity entries to data.json."""

import json
import os
import re
import subprocess
from datetime import datetime, timedelta

# PE repos to monitor (owner/repo -> project id mapping)
REPOS = {
    "claytonjamescreed-sudo/pacific-enclosures-dashboard": "job-costing",
    "claytonjamescreed-sudo/pacific-enclosures-estimator": "estimator",
    "claytonjamescreed-sudo/pe-pm-dashboard": "pm",
}

# Classify commits by message keywords
CLASSIFICATIONS = [
    (r"\bfix\b", "fix", "var(--green-bg)"),
    (r"\bdeploy|ship|release|launch\b", "deploy", "var(--green-bg)"),
    (r"\btest|spec\b", "test", "var(--blue-glow)"),
    (r"\brefactor|cleanup|clean up\b", "refactor", "var(--blue-glow)"),
    (r"\badd|new|create|implement|built\b", "feature", "var(--green-bg)"),
    (r"\bupdate|improve|enhance\b", "update", "var(--blue-glow)"),
    (r"\bdoc|readme\b", "docs", "var(--purple-bg)"),
]

ICONS = {
    "fix": "🔧",
    "deploy": "🚀",
    "test": "🧪",
    "refactor": "⚙️",
    "feature": "✨",
    "update": "📦",
    "docs": "📄",
    "other": "💬",
}

PROJECT_NAMES = {
    "job-costing": "Job Costing",
    "estimator": "Estimator",
    "pm": "PM Dashboard",
}


def classify_commit(message):
    msg_lower = message.lower()
    for pattern, category, color in CLASSIFICATIONS:
        if re.search(pattern, msg_lower):
            return category, color
    return "other", "var(--blue-glow)"


def get_recent_commits(repo, since_days=7):
    """Fetch commits from a repo using gh CLI."""
    since = (datetime.utcnow() - timedelta(days=since_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/commits", "--jq",
             f'[.[] | select(.commit.committer.date >= "{since}") | '
             '{"sha": .sha, "message": .commit.message, "date": .commit.committer.date}]'],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout) if result.stdout.strip() else []
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"  Warning: Could not fetch commits from {repo}: {e}")
        return []


def main():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data.json")
    data_path = os.path.abspath(data_path)

    with open(data_path) as f:
        data = json.load(f)

    existing_texts = {a["text"] for a in data.get("activity", [])}
    new_activities = []

    for repo, project_id in REPOS.items():
        print(f"Fetching commits from {repo}...")
        commits = get_recent_commits(repo)
        print(f"  Found {len(commits)} recent commits")

        project_name = PROJECT_NAMES.get(project_id, project_id)

        for commit in commits:
            # Use first line of commit message
            msg = commit["message"].split("\n")[0].strip()
            if not msg or msg.startswith("Merge"):
                continue

            category, color = classify_commit(msg)
            icon = ICONS.get(category, "💬")

            # Format the date
            commit_date = datetime.fromisoformat(commit["date"].replace("Z", "+00:00"))
            time_str = commit_date.strftime("%b %d")

            text = f"<strong>{project_name}</strong> — {msg}"

            # Skip if already exists
            if text in existing_texts:
                continue

            new_activities.append({
                "icon": icon,
                "text": text,
                "time": time_str,
                "color": color,
            })

    if new_activities:
        print(f"\nAdding {len(new_activities)} new activity entries")
        data["activity"] = new_activities + data.get("activity", [])

        with open(data_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("data.json updated")
    else:
        print("\nNo new activity entries to add")


if __name__ == "__main__":
    main()
