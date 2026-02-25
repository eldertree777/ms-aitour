import asyncio
import os
import logging
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv(override=True)

from agent_framework import Agent  
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential
from agents.mail_agent import create_mail_agent
from agents.task_agent import create_tasks_agent

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MasterAgent")

# 2. 에이전트 생성 함수
def create_master_agent():
    chat_client = AzureOpenAIChatClient(credential=DefaultAzureCredential())
    
    # 각 하위 에이전트를 도구로 변환
    # Tip: 하위 에이전트 생성 시에도 같은 chat_client를 전달하면 리소스를 아낄 수 있습니다.
    mail_agent_tool = create_mail_agent().as_tool(
        name="MailAgent",
        description="이메일 조회, 분석 및 발송 작업을 수행합니다."
    )
    
    tasks_agent_tool = create_tasks_agent().as_tool(
        name="TasksAgent",
        description="구글 태스크(할 일) 조회 및 관리 작업을 수행합니다."
    )
    
    return Agent(
        client=chat_client,
        name="Master-Agent",
        instructions="""당신은 이메일과 태스크를 관리하는 통합 비서입니다. 
        1. 이메일 관련 요청은 MailAgent를 통해 처리하세요.
        2. 할 일(태스크) 관련 요청은 TasksAgent를 통해 처리하세요.
        3. 두 정보를 조합해 사용자에게 최적화된 비서 업무를 수행하세요.
        """,
        tools=[mail_agent_tool, tasks_agent_tool]
    )

async def main():
    logger.info("🛠️ 에이전트 로컬 테스트 모드를 시작합니다.")
    agent = create_master_agent()
    
    logger.info("="*50)
    logger.info("🤖 마스터 에이전트가 준비되었습니다.")
    logger.info("명령을 입력하세요 (종료하려면 'exit' 입력)")
    logger.info("="*50)

    while True:
        try:
            user_input = input("\n[User]: ").strip()
        except EOFError:
            break

        if user_input.lower() in ["exit", "quit", "종료"]:
            break

        if not user_input:
            continue

        logger.info("⏳ 처리 중...")

        try:
            # 👈 RC1에서 agent.run()은 AgentResponse 객체를 반환합니다.
            response = await agent.run(user_input)
            
            # 👈 에이전트의 마지막 응답 텍스트를 추출하는 가장 안전한 방법
            # AgentResponse는 여러 개의 메시지를 담고 있을 수 있으므로 마지막 메시지의 텍스트를 가져옵니다.
            final_text = ""
            if response.messages:
                last_msg = response.messages[-1]
                # last_msg.text는 DurableAgentStateMessage의 편리한 속성입니다.
                final_text = getattr(last_msg, "text", str(last_msg))

            logger.info("-" * 50)
            print(f"\n✨ [Agent]: {final_text}")
            logger.info("-" * 50)
            
        except Exception as e:
            logger.error(f"❌ 오류 발생: {e}")
            
if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    
    logger.info("🚀 로컬 테스트 종료.")