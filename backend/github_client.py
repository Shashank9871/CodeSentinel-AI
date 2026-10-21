"""
GitHub REST API Client for fetching Pull Requests, diffs, and posting review comments.
"""
import re
import requests
from typing import Dict, Any, Optional, Tuple

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeSentinel-AI-Reviewer"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    @staticmethod
    def parse_pr_url(url: str) -> Optional[Tuple[str, str, int]]:
        """Parses a github pull request URL into (owner, repo, pr_number)."""
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, url)
        if match:
            owner, repo, pr_num = match.groups()
            return owner, repo, int(pr_num)
        return None

    def fetch_pr_data(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Fetches PR metadata, diff, and changed files."""
        # 1. PR Metadata
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        res = requests.get(pr_url, headers=self.headers, timeout=15)
        if res.status_code != 200:
            error_msg = f"GitHub API returned {res.status_code}: {res.json().get('message', res.text)}"
            if res.status_code == 403 and "API rate limit exceeded" in res.text:
                error_msg += " (GitHub rate limit reached. Add a GitHub Token in Settings to bypass)."
            raise Exception(error_msg)
        pr_info = res.json()

        # 2. PR Diff
        diff_headers = dict(self.headers)
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        diff_res = requests.get(pr_url, headers=diff_headers, timeout=15)
        diff_content = diff_res.text if diff_res.status_code == 200 else ""

        # 3. Changed Files list
        files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
        files_res = requests.get(files_url, headers=self.headers, timeout=15)
        files_list = files_res.json() if files_res.status_code == 200 else []

        return {
            "id": f"gh-{owner}-{repo}-{pr_number}",
            "title": pr_info.get("title", ""),
            "author": pr_info.get("user", {}).get("login", "unknown"),
            "author_avatar": pr_info.get("user", {}).get("avatar_url", ""),
            "state": pr_info.get("state", "open"),
            "html_url": pr_info.get("html_url", ""),
            "branch": f"{pr_info.get('head', {}).get('ref', '')} -> {pr_info.get('base', {}).get('ref', '')}",
            "additions": pr_info.get("additions", 0),
            "deletions": pr_info.get("deletions", 0),
            "changed_files_count": pr_info.get("changed_files", 0),
            "diff": diff_content,
            "files": [
                {
                    "filename": f.get("filename"),
                    "status": f.get("status"),
                    "additions": f.get("additions"),
                    "deletions": f.get("deletions"),
                    "patch": f.get("patch", "")
                }
                for f in files_list if isinstance(f, dict)
            ]
        }

    def post_review(self, owner: str, repo: str, pr_number: int, event: str, body: str) -> Dict[str, Any]:
        """Posts an overall review to GitHub PR (event: APPROVE, REQUEST_CHANGES, COMMENT)."""
        if not self.token:
            raise Exception("A valid GitHub Personal Access Token is required to post reviews back to GitHub.")
            
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        payload = {
            "event": event,
            "body": body
        }
        res = requests.post(url, headers=self.headers, json=payload, timeout=15)
        if res.status_code not in (200, 201):
            raise Exception(f"Failed to post review: {res.status_code} {res.text}")
        return res.json()
