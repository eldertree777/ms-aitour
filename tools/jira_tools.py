import os
import logging
from typing import Annotated, Optional
from pydantic import Field
from jira import JIRA

# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class JiraAutomationTools:
    def __init__(self):
        logger.info("JiraAutomationTools 초기화 시작")
        # 환경 변수에서 설정 로드
        self.server = os.getenv("JIRA_SERVER_URL")
        self.email = os.getenv("JIRA_USER_EMAIL")
        self.token = os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY")
        
        logger.debug(f"JIRA_SERVER_URL: {self.server}")
        logger.debug(f"JIRA_USER_EMAIL: {self.email}")
        logger.debug(f"JIRA_PROJECT_KEY: {self.project_key}")
        self._client = None
        
        # 아래처럼 하면 에러 발생. 추후 해결 필요.
        # try:
        #     # Jira 클라이언트 초기화
        #     self.client = JIRA(server=self.server, basic_auth=(self.email, self.token), options={'resilient' : False})
        #     logger.info("JIRA 클라이언트 초기화 성공")
        # except Exception as e:
        #     logger.error(f"JIRA 클라이언트 초기화 실패: {str(e)}")
        #     raise
        
    @property
    def client(self):
        # 실제 호출될 때 클라이언트를 생성하여 에러 방지 및 세션 유지
        if self._client is None:
            self._client = JIRA(server=self.server, basic_auth=(self.email, self.token), options={'resilient' : False})
        return self._client

    def get_jira_issue(self, 
        issue_key: Annotated[str, Field(description="The key of the Jira issue (e.g., 'KAN-123')")]
    ) -> str:
        """Retrieves details of a specific Jira issue to read specifications."""
        logger.info(f"JIRA 이슈 조회 시작: {issue_key}")
        try:
            issue = self.client.issue(issue_key)
            issue_type = issue.fields.issuetype.name if issue.fields.issuetype else "Unknown"
            result = f"Key: {issue.key}, Type: {issue_type}, Summary: {issue.fields.summary}, Description: {issue.fields.description}"
            logger.info(f"JIRA 이슈 조회 성공: {issue_key}")
            logger.debug(f"응답: {result}")
            return result
        except Exception as e:
            logger.error(f"JIRA 이슈 조회 실패: {issue_key} - {str(e)}", exc_info=True)
            return f"Error fetching Jira issue: {str(e)}"

    def create_jira_issue(self,
        summary: Annotated[str, Field(description="Title of the development ticket")],
        description: Annotated[str, Field(description="Detailed content of the development ticket")],
        issue_type: Annotated[str, Field(description="Type of the issue, e.g., '사양', '개발'")]
    ) -> str:
        """Creates a new development ticket in Jira based on provided specifications."""
        logger.info(f"JIRA 이슈 생성 시작: {summary}")
        logger.debug(f"Issue Type: {issue_type}, Project: {self.project_key}")
        try:
            new_issue = self.client.create_issue(fields={
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
            })
            logger.info(f"JIRA 이슈 생성 성공: {new_issue.key}")
            return f"Successfully created Jira issue: {new_issue.key}"
        except Exception as e:
            logger.error(f"JIRA 이슈 생성 실패: {summary} - {str(e)}", exc_info=True)
            return f"Error creating Jira issue: {str(e)}"

    def update_jira_issue(self,
        issue_key: Annotated[str, Field(description="The key of the Jira issue to update")],
        comment: Annotated[str, Field(description="Comment to add or update details")]
    ) -> str:
        """Updates an existing Jira issue by adding a comment or changing details."""
        logger.info(f"JIRA 이슈 업데이트 시작: {issue_key}")
        logger.debug(f"Comment: {comment[:100]}...")  # 처음 100자만 로깅
        try:
            self.client.add_comment(issue_key, comment)
            logger.info(f"JIRA 이슈 업데이트 성공: {issue_key}")
            return f"Successfully updated Jira issue {issue_key} with a comment."
        except Exception as e:
            logger.error(f"JIRA 이슈 업데이트 실패: {issue_key} - {str(e)}", exc_info=True)
            return f"Error updating Jira issue: {str(e)}"