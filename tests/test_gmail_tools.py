import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. 현재 파일(test_google_api_tools.py)의 부모의 부모 폴더(ms-aitour) 경로를 계산
# D:\code\2026\ms-aitour\tests -> D:\code\2026\ms-aitour
root_dir = Path(__file__).resolve().parent.parent

# 2. 파이썬이 모듈을 찾는 경로(sys.path)의 맨 앞에 추가
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# 3. 이제 정상적으로 import 가능
from tools.gmail_tools import GmailAutomationTools

def run_integration_test():
    # 1. 환경 변수 로드
    load_dotenv()
    print("--- Gmail Automation Tools Test Start ---")

    try:
        # 2. 클래스 초기화 (인증 과정 포함)
        gmail_tools = GmailAutomationTools()
        print("[성공] 서비스 초기화 및 인증 완료\n")

        # 3. 읽지 않은 메일 테스트
        print("1. 읽지 않은 메일 목록 조회:")
        unread = gmail_tools.get_unread_email_titles()
        print(unread)
        print("-" * 30)

        # 4. 오늘 받은 메일 테스트
        print("2. 오늘 받은 메일 상세 조회:")
        today_emails = gmail_tools.get_emails_received_today()
        print(today_emails)
        print("-" * 30)

        # 5. 최근 메일 N개 테스트
        print("3. 최근 메일 3개 조회:")
        recent = gmail_tools.get_recent_emails(count=3)
        print(recent)
        print("-" * 30)
        
        # 6. 메일 전송 테스트 (자기 자신에게 전송)
        print("4. 메일 전송 테스트 (셀프 전송):")
        
        # TODO: 아래 이메일 주소를 본인의 Gmail 주소로 수정하세요.
        my_email = "jewon9706@gmail.com" 
        
        test_subject = "오늘의 특별 과제 알림"
        test_body = "오늘까지 받아쓰기 100번 쓰기"
        
        print(f"수신자: {my_email}")
        print(f"내용: {test_body}")
        
        send_result = gmail_tools.send_email(
            to=my_email, 
            subject=test_subject, 
            body=test_body
        )
        print(send_result)
        print("-" * 30)

    except Exception as e:
        print(f"[실패] 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    run_integration_test()