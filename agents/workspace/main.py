import os
import logging
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv(override=True)

# 2. 필수 클래스 임포트 (Agent 클래스가 추가되었습니다)
from agent_framework import Agent  
from agent_framework.azure import AgentFunctionApp, AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential
from tools.gtask_tools import GoogleTasksAutomationTools
from tools.gmail_tools import GmailAutomationTools

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EmailTaskAgent")

# 3. 에이전트 생성 함수 수정
def create_agent():
    # 클라이언트는 이제 '엔진' 역할만 수행합니다.
    chat_client = AzureOpenAIChatClient(credential=DefaultAzureCredential())
    
    gmail_tools = GmailAutomationTools()
    tasks_tools = GoogleTasksAutomationTools()
    
    # 👈 핵심 변경: chat_client.create_agent(...) 대신 Agent(...)를 직접 생성합니다.
    return Agent(
        client=chat_client,  # 생성한 클라이언트를 주입합니다.
        name="Email-to-Task-Agent",
        instructions="이메일을 분석하여 Google Tasks에 등록하는 전문가입니다.",
        tools=[
            gmail_tools.get_unread_email_titles,
            tasks_tools.add_google_task,
            tasks_tools.list_tasks
        ]
    )

# 4. 앱 정의
app = AgentFunctionApp(
    agents=[create_agent()], 
    enable_health_check=True, 
    max_poll_retries=50
)

if __name__ == "__main__":
    logger.info("🚀 에이전트 서버 준비 완료. 'func start' 명령어로 실행하세요.")