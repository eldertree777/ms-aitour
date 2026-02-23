import os
from datetime import datetime
from typing import Annotated
from pydantic import Field

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GmailAutomationTools:
    def __init__(self):
        # 1. 환경 변수에서 경로 로드
        self.cred_path = os.getenv("GMAIL_CREDENTIALS_PATH")
        self.token_path = os.getenv("GMAIL_TOKEN_PATH")
        
        # 경로 설정 확인 (에러 방지)
        if not self.cred_path or not self.token_path:
            raise ValueError("환경 변수 'GMAIL_CREDENTIALS_PATH' 또는 'GMAIL_TOKEN_PATH'가 설정되지 않았습니다.")
            
        self.scopes = ["https://www.googleapis.com/auth/gmail.modify"]
        
        # 2. Gmail 서비스 초기화
        self.service = self._authenticate()

    def _authenticate(self):
        """환경 변수 경로를 사용하여 Google 서비스 객체를 생성합니다."""
        creds = None
        
        # token.json 확인
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        
        # 인증 정보가 없거나 만료된 경우
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.cred_path):
                    raise FileNotFoundError(f"Credentials 파일이 없습니다: {self.cred_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(self.cred_path, self.scopes)
                creds = flow.run_local_server(port=0)
            
            # 갱신된 토큰 저장
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
        
        return build("gmail", "v1", credentials=creds)

    def get_unread_email_titles(self) -> str:
        """가장 최근의 확인하지 않은(읽지 않은) 메일들의 제목 목록을 최대 10개 가져옵니다."""
        try:
            results = self.service.users().messages().list(userId='me', q='is:unread', maxResults=10).execute()
            messages = results.get('messages', [])
            
            if not messages:
                return "확인하지 않은 새로운 메일이 없습니다."
            
            titles = []
            for msg in messages:
                txt = self.service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
                headers = txt.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "제목 없음")
                titles.append(f"- {subject}")
            
            return "\n".join(titles)
        except Exception as e:
            return f"메일 제목 호출 중 오류 발생: {str(e)}"

    def get_emails_received_today(self) -> str:
        """오늘 수신된 모든 메일의 제목과 요약 내용을 가져옵니다."""
        try:
            today = datetime.now().strftime('%Y/%m/%d')
            query = f"after:{today}"
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            if not messages:
                return f"{today} 오늘 수신된 메일이 없습니다."
            
            output = [f"--- {today} 수신 메일 리스트 ---"]
            for msg in messages:
                full_msg = self.service.users().messages().get(userId='me', id=msg['id']).execute()
                headers = full_msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "제목 없음")
                snippet = full_msg.get('snippet', '')
                output.append(f"제목: {subject}\n요약: {snippet}\n")
            
            return "\n".join(output)
        except Exception as e:
            return f"오늘 메일 호출 중 오류 발생: {str(e)}"

    def get_recent_emails(self, 
        count: Annotated[int, Field(description="조회할 최근 메일의 개수")] = 5
    ) -> str:
        """최근에 수신된 메일을 지정된 개수만큼 조회하여 날짜와 제목을 반환합니다."""
        try:
            results = self.service.users().messages().list(userId='me', maxResults=count).execute()
            messages = results.get('messages', [])
            
            if not messages:
                return "수신된 메일 기록이 없습니다."
            
            output = []
            for msg in messages:
                full_msg = self.service.users().messages().get(userId='me', id=msg['id']).execute()
                headers = full_msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "제목 없음")
                date = next((h['value'] for h in headers if h['name'] == 'Date'), "날짜 없음")
                output.append(f"[{date}] {subject}")
            
            return "\n".join(output)
        except Exception as e:
            return f"최근 메일 조회 중 오류 발생: {str(e)}"