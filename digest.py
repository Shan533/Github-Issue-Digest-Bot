#!/usr/bin/env python3
# Script to query GitHub issues and generate an HTML digest
import os
import sys
import argparse
import requests
from urllib.parse import quote
from datetime import datetime, timezone
from dateutil import parser as dtparser

GH_API = "https://api.github.com"


def env_list(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def fetch_issues(token: str, queries: list[str], limit: int) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    results = {}
    per_page = 50

    for q in queries:
        q = q.strip()
        if not q:
            continue
        url = f"{GH_API}/search/issues?q={quote(q)}&sort=updated&order=desc&per_page={per_page}"
        page = 1
        while True:
            resp = requests.get(url + f"&page={page}", headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                if item.get("pull_request"):
                    # Skip PRs, only keep issues
                    continue
                results[item["html_url"]] = item
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break
            # GitHub Search API max 1000 results, stop if fewer than per_page returned
            if len(data.get("items", [])) < per_page:
                break
            page += 1
        if len(results) >= limit:
            break

    return list(results.values())


def to_lower_set(items: list[str]) -> set[str]:
    return {x.lower() for x in items}


def label_names(issue: dict) -> list[str]:
    return [lbl.get("name", "") for lbl in issue.get("labels", [])]


def keep_issue(issue: dict, priority_labels: set[str], exclude_labels: set[str], exclude_assignees: set[str]) -> bool:
    names = label_names(issue)
    names_lower = to_lower_set(names)

    # Must match at least one priority label (if priority_labels not empty)
    if priority_labels and not (names_lower & priority_labels):
        return False

    # Exclude if issue has excluded labels
    if exclude_labels and (names_lower & exclude_labels):
        return False

    # Exclude if issue is already assigned to excluded users
    assignees = {a.get("login", "").lower() for a in issue.get("assignees", [])}
    if exclude_assignees and (assignees & exclude_assignees):
        return False

    return True


def render_html(issues: list[dict]) -> str:
    now = datetime.now(timezone.utc)
    head = f"""
<!doctype html>
<html><head><meta charset='utf-8'/>
<title>Daily GitHub Issue Digest</title>
<style>
  body {{ font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif; line-height:1.5; color:#111; }}
  .issue {{ border-bottom:1px solid #eee; padding:12px 0; }}
  .repo {{ color:#555; font-size:12px; }}
  .labels span {{ display:inline-block; margin-right:6px; padding:2px 6px; border:1px solid #ddd; border-radius:10px; font-size:12px; }}
  .meta {{ color:#666; font-size:12px; }}
</style>
</head><body>
<h2>Daily GitHub Issue Digest</h2>
<p class='meta'>Generated at {now.strftime('%Y-%m-%d %H:%M UTC')}</p>
"""

    if not issues:
        return head + "<p>No matching issues today 🎉</p></body></html>"

    parts = [head]
    for it in issues:
        title = it.get("title", "(no title)")
        url = it.get("html_url", "")
        repo_full = it.get("repository_url", "").replace(f"{GH_API}/repos/", "")
        labels = label_names(it)
        updated_at = dtparser.parse(it.get("updated_at"))
        created_at = dtparser.parse(it.get("created_at"))
        parts.append(
            f"<div class='issue'>"
            f"<div><a href='{url}' target='_blank'>{title}</a></div>"
            f"<div class='repo'>{repo_full}</div>"
            f"<div class='labels'>{''.join(f'<span>{l}</span>' for l in labels)}</div>"
            f"<div class='meta'>Created: {created_at.strftime('%Y-%m-%d')} · Updated: {updated_at.strftime('%Y-%m-%d')}</div>"
            f"</div>"
        )

    parts.append("</body></html>")
    return "".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="digest.html")
    args = ap.parse_args()

    token = os.getenv("GH_TOKEN", "").strip()
    if not token:
        print("GH_TOKEN is required", file=sys.stderr)
        sys.exit(1)

    queries = env_list("SEARCH_QUERIES")
    priority_labels = to_lower_set(env_list("PRIORITY_LABELS"))
    exclude_labels = to_lower_set(env_list("EXCLUDE_LABELS"))
    exclude_assignees = to_lower_set(env_list("EXCLUDE_ASSIGNEES"))
    max_issues = int(os.getenv("MAX_ISSUES", "100"))

    issues = fetch_issues(token, queries, max_issues)
    filtered = [it for it in issues if keep_issue(it, priority_labels, exclude_labels, exclude_assignees)]

    # Sort final results by updated date descending
    filtered.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

    html = render_html(filtered)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {args.out} with {len(filtered)} issues.")


if __name__ == "__main__":
    main()
