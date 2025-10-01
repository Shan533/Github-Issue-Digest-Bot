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
                # Include both issues and PRs
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


def get_priority_score(issue: dict) -> int:
    """Get priority score for sorting (lower number = higher priority)"""
    labels = label_names(issue)
    labels_lower = [l.lower() for l in labels]
    
    # Priority order: P0 > P1 > P2 > others
    if any("priority:p0" in l or l == "p0" for l in labels_lower):
        return 0
    elif any("priority:p1" in l or l == "p1" for l in labels_lower):
        return 1
    elif any("priority:p2" in l or l == "p2" for l in labels_lower):
        return 2
    else:
        return 3  # No priority label


def get_priority_label(issue: dict) -> str:
    """Get priority label for display"""
    labels = label_names(issue)
    labels_lower = [l.lower() for l in labels]
    
    if any("priority:p0" in l or l == "p0" for l in labels_lower):
        return "P0"
    elif any("priority:p1" in l or l == "p1" for l in labels_lower):
        return "P1"
    elif any("priority:p2" in l or l == "p2" for l in labels_lower):
        return "P2"
    else:
        return ""


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
    
    # Separate PRs and Issues
    prs = [item for item in issues if item.get("pull_request")]
    issues_only = [item for item in issues if not item.get("pull_request")]
    
    head = f"""
<!doctype html>
<html><head><meta charset='utf-8'/>
<title>Daily GitHub Issues & PRs Digest</title>
<style>
  body {{ font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif; line-height:1.5; color:#111; }}
  .item {{ border-bottom:1px solid #eee; padding:12px 0; }}
  .pr {{ border-left: 3px solid #28a745; padding-left: 8px; }}
  .issue {{ border-left: 3px solid #007bff; padding-left: 8px; }}
  .repo {{ color:#555; font-size:12px; }}
  .labels span {{ display:inline-block; margin-right:6px; padding:2px 6px; border:1px solid #ddd; border-radius:10px; font-size:12px; }}
  .meta {{ color:#666; font-size:12px; }}
  .type-badge {{ display:inline-block; padding:2px 6px; border-radius:10px; font-size:11px; font-weight:bold; margin-right:8px; }}
  .pr-badge {{ background:#28a745; color:white; }}
  .issue-badge {{ background:#007bff; color:white; }}
  .priority-badge {{ display:inline-block; padding:2px 6px; border-radius:10px; font-size:10px; font-weight:bold; margin-right:6px; }}
  .priority-p0 {{ background:#dc3545; color:white; }}
  .priority-p1 {{ background:#fd7e14; color:white; }}
  .priority-p2 {{ background:#ffc107; color:black; }}
  .section {{ margin-bottom:20px; }}
  .section h3 {{ margin-bottom:10px; color:#333; }}
  .item-title {{ display:flex; align-items:center; margin-bottom:4px; }}
</style>
</head><body>
<h2>Daily GitHub Issues & PRs Digest</h2>
<p class='meta'>Generated at {now.strftime('%Y-%m-%d %H:%M UTC')}</p>
"""

    if not issues:
        return head + "<p>No matching issues or PRs today 🎉</p></body></html>"

    parts = [head]
    
    # Render PRs section
    if prs:
        parts.append('<div class="section">')
        parts.append(f'<h3>📋 Pull Requests ({len(prs)})</h3>')
        for pr in prs:
            title = pr.get("title", "(no title)")
            url = pr.get("html_url", "")
            repo_full = pr.get("repository_url", "").replace(f"{GH_API}/repos/", "")
            labels = label_names(pr)
            updated_at = dtparser.parse(pr.get("updated_at"))
            created_at = dtparser.parse(pr.get("created_at"))
            priority = get_priority_label(pr)
            priority_badge = f"<span class='priority-badge priority-{priority.lower()}'>{priority}</span>" if priority else ""
            
            parts.append(
                f"<div class='item pr'>"
                f"<div class='item-title'><span class='type-badge pr-badge'>PR</span>{priority_badge}<a href='{url}' target='_blank'>{title}</a></div>"
                f"<div class='repo'>{repo_full}</div>"
                f"<div class='labels'>{''.join(f'<span>{l}</span>' for l in labels)}</div>"
                f"<div class='meta'>Created: {created_at.strftime('%Y-%m-%d')} · Updated: {updated_at.strftime('%Y-%m-%d')}</div>"
                f"</div>"
            )
        parts.append('</div>')
    
    # Render Issues section
    if issues_only:
        parts.append('<div class="section">')
        parts.append(f'<h3>🐛 Issues ({len(issues_only)})</h3>')
        for issue in issues_only:
            title = issue.get("title", "(no title)")
            url = issue.get("html_url", "")
            repo_full = issue.get("repository_url", "").replace(f"{GH_API}/repos/", "")
            labels = label_names(issue)
            updated_at = dtparser.parse(issue.get("updated_at"))
            created_at = dtparser.parse(issue.get("created_at"))
            priority = get_priority_label(issue)
            priority_badge = f"<span class='priority-badge priority-{priority.lower()}'>{priority}</span>" if priority else ""
            
            parts.append(
                f"<div class='item issue'>"
                f"<div class='item-title'><span class='type-badge issue-badge'>ISSUE</span>{priority_badge}<a href='{url}' target='_blank'>{title}</a></div>"
                f"<div class='repo'>{repo_full}</div>"
                f"<div class='labels'>{''.join(f'<span>{l}</span>' for l in labels)}</div>"
                f"<div class='meta'>Created: {created_at.strftime('%Y-%m-%d')} · Updated: {updated_at.strftime('%Y-%m-%d')}</div>"
                f"</div>"
            )
        parts.append('</div>')

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

    # Get queries for both issues and PRs
    issue_queries = env_list("SEARCH_QUERIES")
    pr_queries = env_list("PR_QUERIES")
    
    priority_labels = to_lower_set(env_list("PRIORITY_LABELS"))
    exclude_labels = to_lower_set(env_list("EXCLUDE_LABELS"))
    exclude_assignees = to_lower_set(env_list("EXCLUDE_ASSIGNEES"))
    max_issues = int(os.getenv("MAX_ISSUES", "100"))
    max_prs = int(os.getenv("MAX_PRS", "100"))

    all_items = []
    
    # Fetch issues
    if issue_queries:
        issues = fetch_issues(token, issue_queries, max_issues)
        filtered_issues = [it for it in issues if not it.get("pull_request") and keep_issue(it, priority_labels, exclude_labels, exclude_assignees)]
        all_items.extend(filtered_issues)
    
    # Fetch PRs
    if pr_queries:
        prs = fetch_issues(token, pr_queries, max_prs)
        filtered_prs = [it for it in prs if it.get("pull_request") and keep_issue(it, priority_labels, exclude_labels, exclude_assignees)]
        all_items.extend(filtered_prs)

    # Sort final results by priority first (ascending), then by updated date descending
    def sort_key(x):
        priority_score = get_priority_score(x)
        # Convert timestamp to sortable number for descending order
        timestamp = x.get("updated_at", "2025-01-01T00:00:00Z")
        try:
            from dateutil import parser as dtparser
            dt = dtparser.parse(timestamp)
            time_num = int(dt.timestamp())
            return (priority_score, -time_num)  # Negative for descending time
        except:
            return (priority_score, 0)
    
    all_items.sort(key=sort_key)

    html = render_html(all_items)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    
    pr_count = len([item for item in all_items if item.get("pull_request")])
    issue_count = len([item for item in all_items if not item.get("pull_request")])
    print(f"Wrote {args.out} with {issue_count} issues and {pr_count} PRs.")


if __name__ == "__main__":
    main()
