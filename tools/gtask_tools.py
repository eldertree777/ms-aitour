import os
from datetime import datetime
from typing import Annotated, Optional
from pydantic import Field

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class GoogleTasksAutomationTools:
    def __init__(self):
        # 1. 환경 변수에서 경로 로드 (Gmail과 같은 credentials를 쓰되, 토큰은 별도 관리를 권장합니다)
        self.cred_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
        self.token_path = os.getenv("GTASK_TOKEN_PATH")

        # 경로 설정 확인 (에러 방지)
        if not self.token_path:
            raise ValueError("환경 변수 'GTASK_TOKEN_PATH'가 설정되지 않았습니다.")
            
        # Google Tasks 관리 권한 설정
        self.scopes = ["https://www.googleapis.com/auth/tasks"]
        
        # 2. Tasks 서비스 초기화
        self.service = self._authenticate()

    def _authenticate(self):
        """환경 변수 경로를 사용하여 Tasks 서비스 객체를 생성합니다."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.cred_path, self.scopes)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
        
        return build("tasks", "v1", credentials=creds)

    def add_google_task(self,
        title: Annotated[str, Field(description="추가할 할 일의 제목")],
        notes: Annotated[Optional[str], Field(description="할 일에 대한 상세 설명(메모)")] = None,
        due_date: Annotated[Optional[str], Field(description="마감 기한 (형식: YYYY-MM-DD)")] = None
    ) -> str:
        """Google Tasks의 기본 목록(@default)에 새로운 할 일을 추가합니다."""
        try:
            # 할 일 객체 구성
            task_body = {
                "title": title,
                "notes": notes
            }
            
            # 마감일이 있으면 RFC 3339 형식으로 변환하여 추가
            if due_date:
                task_body["due"] = f"{due_date}T00:00:00Z"

            # 기본 작업 목록(@default)에 삽입
            result = self.service.tasks().insert(tasklist='@default', body=task_body).execute()
            
            return f"성공적으로 할 일이 추가되었습니다: {result.get('title')} (ID: {result.get('id')})"
        except Exception as e:
            return f"할 일 추가 중 오류 발생: {str(e)}"

    def list_tasks(self, 
        max_results: Annotated[int, Field(description="가져올 할 일의 최대 개수")] = 10
    ) -> str:
        """기본 목록에서 완료되지 않은 할 일들을 가져옵니다."""
        try:
            results = self.service.tasks().list(tasklist='@default', maxResults=max_results, showCompleted=False).execute()
            items = results.get('items', [])

            if not items:
                return "남은 할 일이 없습니다."

            task_list = ["--- 현재 할 일 목록 ---"]
            for item in items:
                task_list.append(f"- {item['title']} (ID: {item['id']})")
            
            return "\n".join(task_list)
        except Exception as e:
            return f"할 일 목록 조회 중 오류 발생: {str(e)}"