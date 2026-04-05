#!/usr/bin/env python3
import json
import os
import subprocess
from datetime import datetime, timezone
from urllib import request
from urllib.error import URLError, HTTPError


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPLAIN_PATH = os.path.join(ROOT, "EXPLAIN.md")
CHANGELOG_PATH = os.path.join(ROOT, "CHANGELOG.md")


def run_git(*args):
  cmd = ["git"] + list(args)
  result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
  if result.returncode != 0:
    return ""
  return result.stdout.strip()


def get_recent_commits(limit=12):
  raw = run_git("log", f"-n{limit}", "--pretty=format:%h|%ad|%s", "--date=short")
  if not raw:
    return []
  commits = []
  for line in raw.splitlines():
    parts = line.split("|", 2)
    if len(parts) != 3:
      continue
    commits.append({"hash": parts[0], "date": parts[1], "subject": parts[2]})
  return commits


def get_open_issues(limit=12):
  repo = os.getenv("GITHUB_REPOSITORY", "")
  token = os.getenv("GITHUB_TOKEN", "")
  if not repo or not token:
    return []

  url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page={limit}"
  req = request.Request(
      url,
      headers={
          "Accept": "application/vnd.github+json",
          "Authorization": f"Bearer {token}",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "aegisos-auto-docs",
      },
  )
  try:
    with request.urlopen(req, timeout=15) as resp:
      payload = json.loads(resp.read().decode("utf-8"))
  except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
    return []

  items = []
  for item in payload:
    if "pull_request" in item:
      continue
    items.append(
        {
            "number": item.get("number"),
            "title": item.get("title", ""),
            "labels": [lbl.get("name", "") for lbl in item.get("labels", [])],
        }
    )
  return items


def render_explain(now_iso, commits, issues):
  issue_lines = []
  for issue in issues:
    labels = ", ".join([x for x in issue["labels"] if x])
    if labels:
      issue_lines.append(f"- #{issue['number']} {issue['title']} ({labels})")
    else:
      issue_lines.append(f"- #{issue['number']} {issue['title']}")
  if not issue_lines:
    issue_lines = ["- Open issues are tracked on GitHub and loaded during CI automation runs."]

  recent_lines = [f"- `{c['hash']}` ({c['date']}): {c['subject']}" for c in commits]
  if not recent_lines:
    recent_lines = ["- No commits detected yet."]

  return f"""# EXPLAIN

Auto-updated project explainer for contributors.
Last generated: {now_iso}

## What AegisOS Is Building

AegisOS is a security-first operating system designed to combine the strongest traits of major platforms in one coherent product:

- iOS: secure defaults, trusted update path, cohesive platform behavior.
- Linux: customization, openness, privacy-first control.
- Windows: practical compatibility strategy for apps and workflows.
- macOS: polish, consistency, and efficiency.
- Android: broad device profile flexibility.

## How We Build It

We implement in vertical slices:

1. Core kernel and scheduler primitives.
2. Security controls (capabilities, sandbox policies, enforcement engine).
3. Packaging and update integrity.
4. UX and compatibility layers.
5. Observability, reliability, and contributor scale-out.

## Current Technical Baseline

- Kernel simulation target with round-robin scheduler skeleton and tests.
- Capability token lifecycle (`issue`, `revoke`, authorization checks).
- Sandbox policy schema validator and test suite.
- CI/docs workflows and contributor-ready GitHub templates.

## Live Backlog Snapshot

{os.linesep.join(issue_lines)}

## Recent Engineering Changes

{os.linesep.join(recent_lines)}
"""


def render_changelog(now_iso, commits):
  recent_lines = [f"- {c['date']} `{c['hash']}` {c['subject']}" for c in commits]
  if not recent_lines:
    recent_lines = ["- No entries yet."]
  return f"""# CHANGELOG

Auto-updated by workflow.
Last generated: {now_iso}

## Unreleased

{os.linesep.join(recent_lines)}
"""


def write_file(path, content):
  existing = ""
  if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
      existing = f.read()
  if existing == content:
    return False
  with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
  return True


def main():
  now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
  commits = get_recent_commits(limit=15)
  issues = get_open_issues(limit=20)

  explain = render_explain(now_iso, commits, issues)
  changelog = render_changelog(now_iso, commits)

  changed = False
  changed |= write_file(EXPLAIN_PATH, explain)
  changed |= write_file(CHANGELOG_PATH, changelog)

  print("updated" if changed else "no-change")


if __name__ == "__main__":
  main()
