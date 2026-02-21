# PE — Project Management Dashboard

## What This Is

Pacific Enclosures development project management dashboard. Tracks all PE software projects — progress, milestones, timeline, and activity. Single-page static dashboard deployed via GitHub Pages.

## Project Structure

```
index.html   — Dashboard UI, styling, and render logic (DO NOT put data here)
data.json    — All project data (this is the ONLY file to update for content changes)
.github/     — GitHub Pages deployment workflow
```

## Critical Rule

**All data updates go in `data.json`. Never hardcode data in `index.html`.**

The HTML file contains only layout, styling, and render functions. It fetches `data.json` at load time. When updating projects, milestones, timeline entries, or activity — edit `data.json` only.

## data.json Schema

### projects[]

```json
{
  "id": "kebab-case-id",
  "name": "Display Name",
  "description": "What this project does.",
  "status": "active | planning | review | paused | pipeline",
  "version": "v1.0 | v0.1-dev | —",
  "tech": ["Python", "Flask", "SQLite"],
  "deployment": "Heroku | GitHub Pages | Not deployed | TBD",
  "repo": "GitHub repo name",
  "milestones": [
    { "text": "Milestone description", "done": true, "date": "Feb 2026" },
    { "text": "Current task", "done": false, "current": true, "date": "In Progress" },
    { "text": "Future task", "done": false, "date": "Upcoming | Planned | TBD" }
  ]
}
```

- Progress is auto-calculated from milestones (done count / total count)
- Only one or a few milestones should have `"current": true` at a time
- Milestone dates use short formats: `"Feb 2026"`, `"In Progress"`, `"Upcoming"`, `"Planned"`, `"TBD"`

### timeline[]

```json
{
  "date": "Feb 19, 2026",
  "title": "Short event title",
  "desc": "What happened.",
  "project": "job-costing | estimator | pm",
  "color": "green | blue | amber | purple"
}
```

- `green` = completed/shipped, `blue` = progress/built, `amber` = in-progress/warning, `purple` = PM/meta
- Timeline renders newest first — keep entries in reverse chronological order

### activity[]

```json
{
  "icon": "emoji",
  "text": "<strong>Project Name</strong> — what happened",
  "time": "Yesterday | Feb 12 | Feb 2026",
  "color": "var(--green-bg) | var(--blue-glow) | var(--amber-bg) | var(--purple-bg)"
}
```

- Activity text uses `<strong>` tags for project names (rendered as HTML)
- Time is relative/short format

## Status Types

| Status     | Badge Color | Use When                        |
|------------|-------------|---------------------------------|
| `active`   | Green       | Currently being worked on       |
| `planning` | Amber       | Scoping / designing             |
| `review`   | Purple      | In review or testing            |
| `paused`   | Red         | On hold                         |
| `pipeline` | Gray        | Future project, not started     |

## Current PE Projects

1. **Job Costing Dashboard** (`job-costing`) — Live on Heroku. SAGE 50 integration, budget tracking, GP margins.
2. **Estimator App** (`estimator`) — In development. Generator enclosure quoting tool replacing Excel.
3. **Project Management App** (`project-management`) — Pipeline. Scope TBD.
4. **Purchasing App** (`purchasing`) — Pipeline. Scope TBD.

## Deployment

GitHub Pages via `.github/workflows`. Push to main branch to deploy.

## Weekly Archive

The dashboard has a "Weekly Summary" button that generates a markdown snapshot and saves it to the archive.

**How it works:**
- On click, generates a `.md` summary and downloads it
- Also auto-saves to `localStorage` (tagged as "Local")
- The "Weekly Archive" section on the dashboard shows all past summaries
- To make a summary permanent, add it to `data.json` under `weeklySummaries` (tagged as "Committed")

### weeklySummaries[] schema

```json
{
  "dateSlug": "2026-02-20",
  "weekStart": "Feb 13, 2026",
  "weekEnd": "Feb 20, 2026",
  "generatedAt": "2026-02-20T16:30:00.000Z",
  "markdown": "# Pacific Enclosures — Weekly Summary\n..."
}
```

- `dateSlug` is the unique key (one summary per date)
- Entries in `data.json` take priority over localStorage entries with the same `dateSlug`

## Common Tasks

- **Add a milestone**: Add entry to the project's `milestones` array in `data.json`
- **Mark milestone done**: Set `"done": true`, remove `"current": true`
- **Add timeline event**: Add entry to top of `timeline` array in `data.json`
- **Add activity**: Add entry to top of `activity` array in `data.json`
- **Add a new project**: Add full project object to `projects` array in `data.json`
- **Update progress**: Just update milestones — progress bar calculates automatically
- **Commit a weekly summary**: Copy a localStorage summary into `data.json`'s `weeklySummaries` array to make it permanent
