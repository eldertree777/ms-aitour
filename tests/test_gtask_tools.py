import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. 경로 설정: 프로젝트 루트를 sys.path에 추가하여 tools 패키지를 찾을 수 있게 함
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# 2. 클래스 임포트 (파일명이 google_api_tools.py라고 가정)
from tools.gtask_tools import GoogleTasksAutomationTools

def run_tasks_integration_test():
    # 3. 환경 변수 로드 (.env 파일 읽기)
    load_dotenv()
    
    print("🚀 Google Tasks Automation Tools 테스트 시작")
    print("-" * 40)

    try:
        # 4. 클래스 초기화 (인증 진행)
        # 처음 실행 시 브라우저가 뜨며 Google Tasks 권한 승인이 필요합니다.
        tasks_tools = GoogleTasksAutomationTools()
        print("[성공] 서비스 초기화 및 인증 완료\n")

        # 5. 할 일 추가 테스트
        test_title = f"테스트 할 일 ({datetime.now().strftime('%H:%M:%S')})"
        test_note = "이것은 파이썬 자동화 도구를 통해 생성된 테스트 작업입니다."
        test_due = datetime.now().strftime('%Y-%m-%d') # 오늘 날짜

        print(f"1. 할 일 추가 시도: {test_title}")
        add_result = tasks_tools.add_google_task(
            title=test_title,
            notes=test_note,
            due_date=test_due
        )
        print(f"결과: {add_result}\n")

        # 6. 할 일 목록 조회 테스트
        print("2. 현재 할 일 목록 조회:")
        tasks_list = tasks_tools.list_tasks(max_results=5)
        print(tasks_list)
        print("-" * 40)

    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    # datetime 임포트 (테스트용 제목 생성 목적)
    from datetime import datetime
    run_tasks_integration_test()