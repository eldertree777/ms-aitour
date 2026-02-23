import os
import asyncio
# from azure.ai.projects.models import AzureOpenAIChatClient
# from azure.ai.projects import AzureOpenAIChatClient
from agent_framework.azure import AzureOpenAIChatClient
from tools.gtask_tools import GoogleTasksAutomationTools
from tools.gmail_tools import GmailAutomationTools

from dotenv import load_dotenv

def create_task_management_agent():
    """
    Gmail과 Google Tasks 도구를 통합한 업무 관리 에이전트 생성
    
    기능:
    - 최근 혹은 오늘 온 메일을 조회
    - 메일 본문을 분석하여 실행 가능한 할 일(Action Item) 추출
    - 추출된 할 일을 Google Tasks에 마감 기한과 함께 등록
    """
    
    # 1. 도구 초기화
    gmail_tools = GmailAutomationTools()
    tasks_tools = GoogleTasksAutomationTools()

    # 2. Azure OpenAI 클라이언트 설정
    client = AzureOpenAIChatClient(
        api_key=os.environ.get("FOUNDRY_PROJECT_KEY"),
        deployment_name=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"), # 예: gpt-4o-mini
        endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    )
    
    # 3. 에이전트 생성
    agent = client.as_agent(
        name="Email-to-Task Agent",
        instructions="""당신은 사용자의 이메일을 분석하여 중요한 할 일을 관리하는 '업무 효율화 전문가'입니다.

당신의 주요 워크플로우:
1. 사용자의 요청에 따라 '오늘 온 메일' 혹은 '최근 메일' 목록을 조회합니다.
2. 메일의 제목과 요약 내용을 읽고, 사용자가 직접 수행해야 하거나 기억해야 할 '할 일(Task)'을 식별합니다.
3. 할 일이 발견되면 다음 규칙에 따라 Google Tasks에 등록합니다:
   - 제목: 메일의 핵심 목적을 10자 내외로 요약 (예: [메일] 보고서 수정 요청)
   - 메모(Notes): 메일의 주요 내용 요약 및 발신자 정보 포함
   - 마감 기한(Due Date): 메일 본문에 날짜가 명시되어 있다면 해당 날짜를 입력하고, 없다면 오늘 날짜를 기본값으로 사용합니다.
4. 등록이 완료되면 어떤 메일을 바탕으로 어떤 할 일을 만들었는지 사용자에게 친절하게 보고합니다.

주의 사항:
- 단순 광고성 메일이나 공지사항은 할 일로 등록하지 마세요.
- 할 일을 등록하기 전, 이미 비슷한 이름의 할 일이 'list_tasks'를 통해 확인된다면 중복 등록하지 않도록 주의하세요.
""",
        tools=[
            # Gmail 관련 도구
            gmail_tools.get_unread_email_titles,
            gmail_tools.get_emails_received_today,
            gmail_tools.get_recent_emails,
            
            # Google Tasks 관련 도구
            tasks_tools.add_google_task,
            tasks_tools.list_tasks
        ]
    )
    
    return agent


async def main():
    """업무 관리 에이전트(Gmail & Tasks) 테스트용 메인 함수"""
    
    # 1. 환경 변수 로드 (.env 파일의 설정을 최신 상태로 반영)
    load_dotenv(override=True)
    
    print("🚀 Task Management Agent 초기화 중...")
    # 앞서 만든 에이전트 생성 함수 호출
    agent = create_task_management_agent()
    
    print("✅ Agent 초기화 완료")
    print("   Gmail 조회 및 Google Tasks 등록 도구를 모두 사용할 수 있습니다.")
    print("-" * 50)
    
    # 2. 사용자 명령 입력
    # 예: "오늘 온 메일 확인해서 할 일로 등록해줘" 
    # 또는 "최근 메일 3개 요약하고 중요한 건 테스크에 추가해줘"
    user_query = input("에이전트에게 내릴 명령을 입력하세요: ")
    
    if not user_query.strip():
        user_query = "오늘 온 메일을 읽고 처리해야 할 일들을 Google Tasks에 등록해줘."
        print(f"명령이 입력되지 않아 기본 명령으로 실행합니다: '{user_query}'")

    print("\n🤖 에이전트가 업무를 분석 중입니다...")
    
    # 3. 에이전트 실행 (비동기 호출)
    try:
        result = await agent.run(user_query)
        print("\n" + "=" * 50)
        print(f"✨ 에이전트 실행 결과:\n{result}")
        print("=" * 50)
    except Exception as e:
        print(f"❌ 에이전트 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    # Windows 환경에서 이벤트 루프 관련 경고를 방지하기 위한 설정 (필요 시)
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())