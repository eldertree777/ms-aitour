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
from tools.gmail_tools import GmailAutomationTools

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EmailTaskAgent")

# 3. 에이전트 생성 함수
def create_mail_agent():
    # 클라이언트는 이제 '엔진' 역할만 수행합니다.
    chat_client = AzureOpenAIChatClient(credential=DefaultAzureCredential())
    
    gmail_tools = GmailAutomationTools()
    
    return Agent(
        client=chat_client,
        name="Email-Agent",
        instructions="""이메일을 조회하고 분석하는 전문가입니다. 
        1. 사용자의 요청에 따라 메일을 조회합니다. (기간 명시 없을시 오늘의 메일을 조회) 
        2. 메일의 제목과 요약 내용을 읽고, 사용자가 직접 수행해야 하거나 기억해야 할 '할 일(Task)'을 식별합니다.
        3. 필요한경우 메일을 발송할 수도 있습니다. 
        4. 메일 발송 시에는 이메일 주소, 제목, 본문을 명확히 작성하여 보내도록 합니다. 필요한 경우 사용자에게 요청합니다.
        """,
        tools=[
            gmail_tools.get_unread_email_titles,
            gmail_tools.get_emails_received_today,
            gmail_tools.get_recent_emails,
            gmail_tools.send_email
        ]
    )

async def main():
    logger.info("🛠️ 에이전트 로컬 테스트 모드를 시작합니다.")
    
    # 에이전트 인스턴스 생성
    agent = create_mail_agent()
    
    logger.info("="*50)
    logger.info("🤖 메일 에이전트가 준비되었습니다.")
    logger.info("명령을 입력하세요 (종료하려면 'exit' 또는 'quit' 입력)")
    logger.info("="*50)

    while True:
        # 사용자로부터 입력 받기 (input은 사용자 입력을 대기해야 하므로 유지하되, 안내는 로깅 가능)
        try:
            user_input = input("\n[User]: ").strip()
        except EOFError:
            break

        if user_input.lower() in ["exit", "quit", "종료"]:
            logger.info("테스트를 종료합니다.")
            break

        if not user_input:
            continue

        logger.info("⏳ 에이전트가 요청을 처리 중입니다...")

        try:
            # 에이전트 실행 (비동기 호출)
            response = await agent.run(user_input)
            
            logger.info("-" * 50)
            logger.info(f"✨ [Agent]: {response}")
            logger.info("-" * 50)
            
        except Exception as e:
            logger.error(f"❌ 실행 중 오류 발생: {e}")
            logger.error("오류가 발생했습니다. 위 로그 내용을 확인해주세요.")
            
if __name__ == "__main__":
    # Windows 환경에서 발생할 수 있는 ProactorEventLoop 관련 이슈 방지
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 비동기 main 함수 실행
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("사용자에 의해 종료되었습니다.")
    
    # 이 부분은 main() 종료 후에 실행됩니다.
    logger.info("🚀 에이전트 서버 준비 완료. 'func start' 명령어로 실행하세요.")