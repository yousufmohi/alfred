"""
GitHub integration for Alfred
Handles PR reviews and commenting
"""

from typing import Optional, Dict, List, Tuple
from pathlib import Path
import re
from github import Github, GithubException
from github.PullRequest import PullRequest


class GitHubIntegration:
    """Handle GitHub API interactions"""
    
    def __init__(self, github_token: Optional[str] = None, github_auth: Optional['GitHubAuth'] = None):
        """
        Initialize GitHub integration
        
        Args:
            github_token: GitHub access token (optional if github_auth provided)
            github_auth: GitHubAuth instance (will use stored token)
        """
        # Priority: explicit token > auth manager > None
        if github_token:
            self.token = github_token
        elif github_auth and github_auth.is_logged_in():
            self.token = github_auth.get_token()
        else:
            self.token = None
        
        self.client = Github(self.token) if self.token else None
    
    def parse_pr_url(self, url: str) -> Tuple[str, str, int]:
        """
        Parse GitHub PR URL
        
        Args:
            url: GitHub PR URL (e.g., https://github.com/user/repo/pull/123)
            
        Returns:
            Tuple of (owner, repo, pr_number)
        """
        pattern = r'github\.com/([^/]+)/([^/]+)/pull/(\d+)'
        match = re.search(pattern, url)
        
        if not match:
            raise ValueError(
                "Invalid GitHub PR URL. Expected format: "
                "https://github.com/owner/repo/pull/123"
            )
        
        owner, repo, pr_number = match.groups()
        return owner, repo, int(pr_number)
    
    def get_pr(self, owner: str, repo: str, pr_number: int) -> PullRequest:
        """
        Get Pull Request object
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            PullRequest object
        """
        if not self.client:
            raise ValueError("GitHub token required. Run 'alfred github-login'")
        
        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            return repository.get_pull(pr_number)
        except GithubException as e:
            raise ValueError(f"Failed to fetch PR: {e.data.get('message', str(e))}")
    
    def get_pr_files(self, pr: PullRequest) -> List[Dict]:
        """
        Get changed files in PR
        
        Args:
            pr: PullRequest object
            
        Returns:
            List of dicts with file info
        """
        files = []
        
        for file in pr.get_files():
            if file.patch:
                files.append({
                    'filename': file.filename,
                    'patch': file.patch,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'status': file.status,
                    'changes': file.changes
                })
        
        return files
    
    def get_pr_diff(self, pr: PullRequest) -> str:
        """
        Get full diff for PR
        
        Args:
            pr: PullRequest object
            
        Returns:
            Unified diff string
        """
        files = self.get_pr_files(pr)
        
        diff_parts = []
        for file in files:
            diff_parts.append(f"File: {file['filename']}")
            diff_parts.append(f"Status: {file['status']}")
            diff_parts.append(f"Changes: +{file['additions']} -{file['deletions']}")
            diff_parts.append("")
            diff_parts.append(file['patch'])
            diff_parts.append("")
            diff_parts.append("=" * 80)
            diff_parts.append("")
        
        return "\n".join(diff_parts)
    
    def post_pr_comment(self, pr: PullRequest, comment: str) -> bool:
        """
        Post comment on PR
        
        Args:
            pr: PullRequest object
            comment: Comment text (supports Markdown)
            
        Returns:
            True if successful
        """
        try:
            pr.create_issue_comment(comment)
            return True
        except GithubException as e:
            raise ValueError(f"Failed to post comment: {e.data.get('message', str(e))}")
    
    def get_pr_info(self, pr: PullRequest) -> Dict:
        """
        Get PR metadata
        
        Args:
            pr: PullRequest object
            
        Returns:
            Dict with PR info
        """
        return {
            'number': pr.number,
            'title': pr.title,
            'description': pr.body or "",
            'author': pr.user.login,
            'state': pr.state,
            'files_changed': pr.changed_files,
            'additions': pr.additions,
            'deletions': pr.deletions,
            'url': pr.html_url
        }
    
    def format_review_for_pr(self, review: str, pr_info: Dict) -> str:
        """
        Format review for posting as PR comment
        
        Args:
            review: AI-generated review
            pr_info: PR metadata
            
        Returns:
            Formatted markdown comment
        """
        comment_parts = [
            "## 🤖 Alfred AI Code Review",
            "",
            f"**PR:** #{pr_info['number']} - {pr_info['title']}",
            f"**Files changed:** {pr_info['files_changed']}",
            f"**Changes:** +{pr_info['additions']} -{pr_info['deletions']}",
            "",
            "---",
            "",
            review,
            "",
            "---",
            "",
            "*This review was automatically generated by Alfred AI*"
        ]
        
        return "\n".join(comment_parts)