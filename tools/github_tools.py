from github import Github
import os
from typing import Annotated, Optional
from pydantic import Field

class GitHubAutomationTools:
    def __init__(self):
        # 환경 변수에서 설정 로드
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo_name = os.getenv("GITHUB_REPO_NAME") # 예: "owner/repo"
        
        # GitHub 클라이언트 및 레포지토리 초기화
        self.client = Github(self.token)
        self.repo = self.client.get_repo(self.repo_name)

    def create_github_issue(self,
        title: Annotated[str, Field(description="Title of the GitHub issue for the Copilot agent")],
        body: Annotated[str, Field(description="Detailed instructions for the Copilot agent to implement")]
    ) -> str:
        """Creates a new GitHub issue to trigger Copilot agent development."""
        try:
            issue = self.repo.create_issue(title=title, body=body)
            return f"Successfully created GitHub issue #{issue.number} at {issue.html_url}"
        except Exception as e:
            return f"Error creating GitHub issue: {str(e)}"

    def add_pr_comment(self,
        pr_number: Annotated[int, Field(description="The number of the Pull Request")],
        body: Annotated[str, Field(description="The comment text to post on the PR")]
    ) -> str:
        """Adds a comment to a specific Pull Request when changes or feedbacks occur."""
        try:
            pr = self.repo.get_pull(pr_number)
            pr.create_issue_comment(body)
            return f"Successfully added comment to PR #{pr_number}."
        except Exception as e:
            return f"Error adding comment to PR: {str(e)}"

    def get_issue(self,
        issue_number: Annotated[int, Field(description="The issue number to retrieve")]
    ) -> str:
        """Retrieves details of a specific GitHub issue."""
        try:
            issue = self.repo.get_issue(issue_number)
            return f"Issue #{issue.number}: {issue.title}\nState: {issue.state}\nBody:\n{issue.body}\nURL: {issue.html_url}"
        except Exception as e:
            return f"Error retrieving issue: {str(e)}"

    def get_issues(self,
        state: Annotated[str, Field(description="Issue state: 'open', 'closed', or 'all'")] = "open"
    ) -> str:
        """Retrieves list of GitHub issues filtered by state."""
        try:
            issues = self.repo.get_issues(state=state)
            if issues.totalCount == 0:
                return f"No issues found with state '{state}'."
            
            issue_list = []
            for issue in issues[:10]:  # 최대 10개까지만 반환
                issue_list.append(f"#{issue.number}: {issue.title} ({issue.state})")
            
            return "\n".join(issue_list)
        except Exception as e:
            return f"Error retrieving issues: {str(e)}"

    def get_issue_by_title(self,
        title: Annotated[str, Field(description="Title to search for in issues")]
    ) -> str:
        """Searches for issues by title."""
        try:
            issues = self.repo.get_issues(state="all")
            matching_issues = [issue for issue in issues if title.lower() in issue.title.lower()]
            
            if not matching_issues:
                return f"No issues found with title containing '{title}'."
            
            issue_list = []
            for issue in matching_issues[:10]:  # 최대 10개까지만 반환
                issue_list.append(f"#{issue.number}: {issue.title} ({issue.state})")
            
            return "\n".join(issue_list)
        except Exception as e:
            return f"Error searching issues: {str(e)}"