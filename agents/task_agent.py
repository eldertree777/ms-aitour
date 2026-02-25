import asyncio
import os
import logging
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv(override=True)

# 2. 필수 클래스 임포트
from agent_framework import Agent  
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential
from tools.gtask_tools import GoogleTasksAutomationTools

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GoogleTasksAgent")

# 3. 에이전트 생성 함수 (태스크 전용으로 명칭 수정)
def create_tasks_agent():
    # 클라이언트는 이제 '엔진' 역할만 수행합니다.
    chat_client = AzureOpenAIChatClient(credential=DefaultAzureCredential())
    
    tasks_tools = GoogleTasksAutomationTools()
    
    return Agent(
        client=chat_client,
        name="Google-Tasks-Agent",
        instructions="""구글 태스크를 조회하고 분석하는 전문가입니다. 
        1. 사용자의 요청에 따라 '오늘의 태스크' 혹은 '최근 태스크' 목록을 조회합니다. 
        2. 태스크의 제목과 상세 내용을 읽고, 사용자가 직접 수행해야 하거나 기억해야 할 '할 일(Action Item)'을 식별합니다.
        3. 필요한 경우 새로운 태스크를 생성하거나 기존 태스크 목록을 정리합니다. 
        4. 태스크 생성 시에는 제목, 설명, 마감일 등을 명확히 작성하여 생성하도록 합니다. 정보가 부족한 경우 사용자에게 추가 정보를 요청합니다.
        """,
        tools=[
            tasks_tools.add_google_task,
            tasks_tools.list_tasks
        ]
    )

async def main():
    logger.info("🛠️ 구글 태스크 에이전트 로컬 테스트 모드를 시작합니다.")
    
    # 에이전트 인스턴스 생성
    agent = create_tasks_agent()
    
    logger.info("="*50)
    logger.info("🤖 구글 태스크 관리 에이전트가 준비되었습니다.")
    logger.info("명령을 입력하세요. (예: '내 할 일 목록 보여줘', '오늘 마감인 태스크 추가해줘')")
    logger.info("종료하려면 'exit' 또는 'quit'을 입력하세요.")
    logger.info("="*50)

    while True:
        try:
            # 사용자로부터 입력 받기
            user_input = input("\n[User]: ").strip()
        except EOFError:
            break

        if user_input.lower() in ["exit", "quit", "종료"]:
            logger.info("테스트를 종료합니다.")
            break

        if not user_input:
            continue

        logger.info("⏳ 에이전트가 태스크 데이터를 분석 중입니다...")

        try:
            # 에이전트 실행 (비동기 호출)
            response = await agent.run(user_input)
            
            logger.info("-" * 50)
            logger.info(f"✨ [Agent]: {response}")
            logger.info("-" * 50)
            
        except Exception as e:
            logger.error(f"❌ 실행 중 오류 발생: {e}")
            logger.error("문제가 발생했습니다. 설정값(API 권한 등)을 확인해 주세요.")
            
if __name__ == "__main__":
    # Windows 환경에서 ProactorEventLoop 이슈 방지
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 비동기 main 함수 실행
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("사용자에 의해 테스트가 중단되었습니다.")
    
    logger.info("🚀 에이전트 서버 준비 완료. 실제 배포 환경은 'func start'로 실행하세요.")