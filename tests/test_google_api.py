"""
1. google workspace 앱 생성
2. 필요 API 활성화 (예: Gmail API)
3. OAuth 2.0 클라이언트 ID 생성
4. credentials.json 파일 다운로드
5. 해당 코드 실행 -> token.json 파일 생성 (처음 실행 시 자동 생성) 
6. 이후 실행 시 token.json 파일을 사용하여 인증 처리
"""
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 권한 범위 (수정 시 token.json 삭제 필요)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service(token_path=os.getenv("GMAIL_TOKEN_PATH"), credentials_path=os.getenv("GMAIL_CREDENTIALS_PATH")):
    """
    인증을 수행하고 Gmail API 서비스 객체를 반환합니다.
    """
    creds = None

    # 1. 기존에 생성된 token.json이 있는지 확인
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # 2. 유효한 인증 정보가 없으면 새로 인증 진행
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # 토큰 만료 시 갱신
            creds.refresh(Request())
        else:
            # 새로운 인증 플로우 시작
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"인증 파일이 없습니다: {credentials_path}")
            
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # 새로운 인증 정보를 token.json에 저장
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    try:
        # 3. Gmail API 서비스 빌드 및 반환
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        print(f"Gmail 서비스 빌드 중 오류 발생: {e}")
        return None

def main():
    # 사용 예시
    # credentials.json이 다른 경로에 있다면 인자로 넘겨주세요.
    service = get_gmail_service(
        token_path="token.json", 
        credentials_path="credentials.json"
    )

    if service:
        try:
            results = service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])
            print(f"총 {len(labels)}개의 라벨을 찾았습니다.")
        except HttpError as error:
            print(f"API 호출 중 오류 발생: {error}")

if __name__ == "__main__":
    main()