#!/usr/bin/env python3
"""Generate a weekly PM report as HTML with progress charts, emailed via Resend."""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

def load_data():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data.json")
    with open(os.path.abspath(data_path)) as f:
        return json.load(f)

def get_recent_items(items, date_key="date", days=7):
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    for item in items:
        try:
            parsed = datetime.strptime(item[date_key], "%b %d, %Y")
            if parsed >= cutoff:
                recent.append(item)
        except (ValueError, KeyError):
            pass
    return recent

def strip_html(s):
    import re
    return re.sub(r'<[^>]*>', '', s)

def generate_report(data):
    projects = data.get("projects", [])
    timeline = data.get("timeline", [])
    activity = data.get("activity", [])

    now = datetime.now()
    week_ago = now - timedelta(days=7)
    date_str = now.strftime("%B %d, %Y")
    week_start = week_ago.strftime("%b %d")
    week_end = now.strftime("%b %d, %Y")

    recent_timeline = get_recent_items(timeline)
    recent_activity = activity[:10]  # Most recent 10

    # Calculate stats
    total_milestones = sum(len(p["milestones"]) for p in projects)
    done_milestones = sum(sum(1 for m in p["milestones"] if m.get("done")) for p in projects)
    in_progress = []
    for p in projects:
        for m in p["milestones"]:
            if m.get("current"):
                in_progress.append({"project": p["name"], "text": m["text"]})

    # Build project rows with progress bars
    project_rows = ""
    for p in projects:
        total = len(p["milestones"])
        done = sum(1 for m in p["milestones"] if m.get("done"))
        pct = round((done / total) * 100) if total > 0 else 0

        status_colors = {
            "production": "#22c55e",
            "beta": "#f59e0b",
            "active": "#22c55e",
            "planning": "#f59e0b",
            "review": "#a78bfa",
            "paused": "#ef4444",
            "pipeline": "#64748b",
        }
        status_color = status_colors.get(p.get("status", ""), "#64748b")
        bar_color = "#22c55e" if pct >= 60 else "#3b82f6" if pct >= 30 else "#f59e0b"

        # Current tasks for this project
        current_tasks = [m["text"] for m in p["milestones"] if m.get("current")]
        current_html = ""
        if current_tasks:
            current_html = '<div style="font-size:12px;color:#94a3b8;margin-top:4px;">Current: ' + ", ".join(current_tasks) + '</div>'

        project_rows += f'''
        <tr>
            <td style="padding:12px 16px;">
                <div style="font-weight:600;color:#f1f5f9;">{p["name"]}</div>
                <div style="font-size:12px;color:#64748b;">{p.get("version", "")}</div>
                {current_html}
            </td>
            <td style="padding:12px 16px;text-align:center;">
                <span style="display:inline-block;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:700;text-transform:uppercase;color:{status_color};background:rgba({int(status_color[1:3],16)},{int(status_color[3:5],16)},{int(status_color[5:7],16)},0.15);">{p.get("status", "—")}</span>
            </td>
            <td style="padding:12px 16px;text-align:center;color:#94a3b8;font-size:13px;">{done}/{total}</td>
            <td style="padding:12px 16px;width:200px;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="flex:1;height:8px;background:#1e293b;border-radius:4px;overflow:hidden;">
                        <div style="width:{pct}%;height:100%;background:{bar_color};border-radius:4px;transition:width 0.3s;"></div>
                    </div>
                    <span style="font-size:13px;font-weight:600;color:{bar_color};min-width:36px;text-align:right;">{pct}%</span>
                </div>
            </td>
        </tr>'''

    # Timeline highlights
    timeline_html = ""
    if recent_timeline:
        for t in recent_timeline[:8]:
            dot_colors = {"green": "#22c55e", "blue": "#3b82f6", "amber": "#f59e0b", "purple": "#a78bfa"}
            dot = dot_colors.get(t.get("color", ""), "#3b82f6")
            timeline_html += f'''
            <div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #1e293b;">
                <div style="width:8px;height:8px;border-radius:50%;background:{dot};margin-top:6px;flex-shrink:0;"></div>
                <div>
                    <div style="font-size:12px;color:#64748b;">{t.get("date", "")}</div>
                    <div style="font-size:13px;color:#f1f5f9;font-weight:600;">{t.get("title", "")}</div>
                    <div style="font-size:12px;color:#94a3b8;margin-top:2px;">{t.get("desc", "")}</div>
                </div>
            </div>'''
    else:
        timeline_html = '<div style="padding:16px;color:#64748b;font-size:13px;">No timeline events this week.</div>'

    # Activity feed
    activity_html = ""
    for a in recent_activity:
        activity_html += f'''
        <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #1e293b;">
            <span style="font-size:16px;">{a.get("icon", "")}</span>
            <span style="flex:1;font-size:13px;color:#94a3b8;">{a.get("text", "")}</span>
            <span style="font-size:11px;color:#64748b;white-space:nowrap;">{a.get("time", "")}</span>
        </div>'''

    # Overall progress donut (CSS-based)
    overall_pct = round((done_milestones / total_milestones) * 100) if total_milestones > 0 else 0
    donut_color = "#22c55e" if overall_pct >= 60 else "#3b82f6" if overall_pct >= 30 else "#f59e0b"

    # In-progress items
    in_progress_html = ""
    if in_progress:
        for item in in_progress:
            in_progress_html += f'<div style="padding:6px 0;font-size:13px;color:#94a3b8;border-bottom:1px solid #1e293b;">⚡ <strong style="color:#f1f5f9;">{item["project"]}</strong> — {item["text"]}</div>'

    # Build in-progress section
    in_progress_section = ""
    if in_progress:
        in_progress_section = f'''
    <div style="background:#1e293b;border-radius:12px;border:1px solid #334155;overflow:hidden;margin-bottom:24px;">
        <div style="padding:16px 16px 12px;border-bottom:1px solid #334155;">
            <div style="font-size:16px;font-weight:700;color:#f1f5f9;">🔥 In Progress</div>
        </div>
        <div style="padding:12px 16px;">
            {in_progress_html}
        </div>
    </div>'''

    # Build completed projects section
    completed_section = ""
    completed_projects = []
    for p in projects:
        total = len(p["milestones"])
        done = sum(1 for m in p["milestones"] if m.get("done"))
        if total > 0 and done == total:
            completed_projects.append(p)

    if completed_projects:
        cp_items = ""
        for p in completed_projects:
            total = len(p["milestones"])
            tech_str = ", ".join(p.get("tech", []))
            deploy = p.get("deployment", "")
            cp_items += f'''
            <div style="display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #1e293b;">
                <span style="font-size:20px;">🏆</span>
                <div style="flex:1;">
                    <div style="font-weight:600;color:#f1f5f9;">{p["name"]}</div>
                    <div style="font-size:12px;color:#94a3b8;">{total}/{total} milestones • {tech_str} • {deploy}</div>
                </div>
                <span style="display:inline-block;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:700;color:#22c55e;background:rgba(34,197,94,0.15);">100%</span>
            </div>'''
        completed_section = f'''
    <div style="background:#1e293b;border-radius:12px;border:1px solid rgba(34,197,94,0.3);overflow:hidden;margin-bottom:24px;">
        <div style="padding:16px 16px 12px;border-bottom:1px solid #334155;">
            <div style="font-size:16px;font-weight:700;color:#22c55e;">🏆 Completed Projects</div>
        </div>
        <div style="padding:12px 16px;">
            {cp_items}
        </div>
    </div>'''

    remaining = total_milestones - done_milestones

    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:700px;margin:0 auto;padding:24px;">

    <!-- Header -->
    <div style="text-align:center;padding:32px 0 24px;">
        <div style="font-size:24px;font-weight:800;color:#f1f5f9;">Pacific Enclosures</div>
        <div style="font-size:14px;color:#64748b;margin-top:4px;">Weekly Project Report</div>
        <div style="font-size:13px;color:#3b82f6;margin-top:8px;">{week_start} – {week_end}</div>
    </div>

    <!-- Summary Stats -->
    <div style="display:flex;gap:12px;margin-bottom:24px;">
        <div style="flex:1;background:#1e293b;border-radius:12px;padding:20px;text-align:center;border:1px solid #334155;">
            <div style="font-size:28px;font-weight:800;color:{donut_color};">{overall_pct}%</div>
            <div style="font-size:11px;color:#64748b;margin-top:4px;">Overall Progress</div>
        </div>
        <div style="flex:1;background:#1e293b;border-radius:12px;padding:20px;text-align:center;border:1px solid #334155;">
            <div style="font-size:28px;font-weight:800;color:#22c55e;">{done_milestones}</div>
            <div style="font-size:11px;color:#64748b;margin-top:4px;">Tasks Done</div>
        </div>
        <div style="flex:1;background:#1e293b;border-radius:12px;padding:20px;text-align:center;border:1px solid #334155;">
            <div style="font-size:28px;font-weight:800;color:#f59e0b;">{remaining}</div>
            <div style="font-size:11px;color:#64748b;margin-top:4px;">Remaining</div>
        </div>
        <div style="flex:1;background:#1e293b;border-radius:12px;padding:20px;text-align:center;border:1px solid #334155;">
            <div style="font-size:28px;font-weight:800;color:#a78bfa;">{len(projects)}</div>
            <div style="font-size:11px;color:#64748b;margin-top:4px;">Projects</div>
        </div>
    </div>

    <!-- Project Progress Table -->
    <div style="background:#1e293b;border-radius:12px;border:1px solid #334155;overflow:hidden;margin-bottom:24px;">
        <div style="padding:16px 16px 12px;border-bottom:1px solid #334155;">
            <div style="font-size:16px;font-weight:700;color:#f1f5f9;">Project Progress</div>
        </div>
        <table style="width:100%;border-collapse:collapse;">
            <thead>
                <tr style="border-bottom:1px solid #334155;">
                    <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;">Project</th>
                    <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;">Status</th>
                    <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;">Done</th>
                    <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;">Progress</th>
                </tr>
            </thead>
            <tbody>
                {project_rows}
            </tbody>
        </table>
    </div>

    {completed_section}

    {in_progress_section}

    <!-- This Week's Highlights -->
    <div style="background:#1e293b;border-radius:12px;border:1px solid #334155;overflow:hidden;margin-bottom:24px;">
        <div style="padding:16px 16px 12px;border-bottom:1px solid #334155;">
            <div style="font-size:16px;font-weight:700;color:#f1f5f9;">📅 This Week</div>
        </div>
        <div style="padding:12px 16px;">
            {timeline_html}
        </div>
    </div>

    <!-- Recent Activity -->
    <div style="background:#1e293b;border-radius:12px;border:1px solid #334155;overflow:hidden;margin-bottom:24px;">
        <div style="padding:16px 16px 12px;border-bottom:1px solid #334155;">
            <div style="font-size:16px;font-weight:700;color:#f1f5f9;">⚡ Recent Activity</div>
        </div>
        <div style="padding:12px 16px;">
            {activity_html}
        </div>
    </div>

    <!-- Footer -->
    <div style="text-align:center;padding:24px 0;color:#64748b;font-size:12px;">
        Generated from PE PM Dashboard — {date_str}<br>
        <a href="https://claytonjamescreed-sudo.github.io/pe-pm-dashboard/" style="color:#3b82f6;text-decoration:none;">View Dashboard →</a>
    </div>

</div>
</body>
</html>'''

    return html


def send_email(html, to_email):
    """Send the report via Resend API using subprocess curl (avoids Cloudflare blocks on urllib)."""
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("ERROR: RESEND_API_KEY not set")
        sys.exit(1)

    now = datetime.now()
    subject = f"PE Weekly Report — {now.strftime('%b %d, %Y')}"

    payload = json.dumps({
        "from": "PE Dashboard <reports@taplaunch.ai>",
        "to": [to_email],
        "subject": subject,
        "html": html,
    })

    result = subprocess.run(
        ["curl", "-s", "-w", "\n%{http_code}",
         "https://api.resend.com/emails",
         "-H", f"Authorization: Bearer {api_key}",
         "-H", "Content-Type: application/json",
         "-d", payload],
        capture_output=True, text=True
    )

    lines = result.stdout.strip().split("\n")
    status_code = lines[-1] if lines else "0"
    body = "\n".join(lines[:-1])

    if status_code.startswith("2"):
        print(f"Email sent successfully: {body}")
    else:
        print(f"Email failed (HTTP {status_code}): {body}")
        sys.exit(1)


def save_to_archive(data):
    """Save a weekly summary entry into data.json's weeklySummaries array."""
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    fmt = lambda d: d.strftime("%b %d, %Y")
    date_slug = now.strftime("%Y-%m-%d")

    # Build a markdown summary for the archive
    strip_html = lambda s: __import__('re').sub(r'<[^>]*>', '', s)
    projects = data.get("projects", [])
    md = f"# Pacific Enclosures — Weekly Report\n"
    md += f"**{fmt(week_ago)} – {fmt(now)}**\n\n"
    md += "## Progress\n"
    md += "| Project | Progress | Status |\n|---------|----------|--------|\n"
    for p in projects:
        total = len(p["milestones"])
        done = sum(1 for m in p["milestones"] if m.get("done"))
        pct = round((done / total) * 100) if total > 0 else 0
        md += f"| {p['name']} | {pct}% ({done}/{total}) | {p.get('status', '—')} |\n"
    md += "\n"

    # Completed projects
    completed = [p for p in projects if len(p["milestones"]) > 0 and all(m.get("done") for m in p["milestones"])]
    if completed:
        md += "## Completed Projects\n"
        for p in completed:
            total = len(p["milestones"])
            tech_str = ", ".join(p.get("tech", []))
            md += f"- **{p['name']}** — {total}/{total} milestones | {tech_str} | {p.get('deployment', '')}\n"
        md += "\n"

    in_prog = [(p["name"], m["text"]) for p in projects for m in p["milestones"] if m.get("current")]
    if in_prog:
        md += "## In Progress\n"
        for pname, text in in_prog:
            md += f"- **{pname}** — {text}\n"
        md += "\n"

    activity = data.get("activity", [])[:10]
    if activity:
        md += "## Recent Activity\n"
        for a in activity:
            md += f"- {strip_html(a.get('text', ''))} _({a.get('time', '')})_\n"
        md += "\n"

    md += f"---\n_Generated from PE PM Dashboard — {fmt(now)}_\n"

    entry = {
        "dateSlug": date_slug,
        "weekStart": fmt(week_ago),
        "weekEnd": fmt(now),
        "generatedAt": now.isoformat(),
        "markdown": md,
    }

    summaries = data.get("weeklySummaries", [])
    # Replace if same date exists
    existing = next((i for i, s in enumerate(summaries) if s.get("dateSlug") == date_slug), None)
    if existing is not None:
        summaries[existing] = entry
    else:
        summaries.insert(0, entry)
    data["weeklySummaries"] = summaries

    data_path = os.path.join(os.path.dirname(__file__), "..", "data.json")
    data_path = os.path.abspath(data_path)
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Weekly summary archived to data.json ({date_slug})")


def main():
    data = load_data()
    html = generate_report(data)

    # Save locally for preview
    out_path = os.path.join(os.path.dirname(__file__), "..", "weekly-report.html")
    out_path = os.path.abspath(out_path)
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Report saved to {out_path}")

    # Save to weekly archive in data.json
    if os.environ.get("SAVE_ARCHIVE", "").lower() in ("1", "true", "yes"):
        save_to_archive(data)

    # Send email if recipient provided
    to_email = os.environ.get("REPORT_EMAIL", "")
    if to_email:
        send_email(html, to_email)
    else:
        print("No REPORT_EMAIL set — skipping email send")


if __name__ == "__main__":
    main()
