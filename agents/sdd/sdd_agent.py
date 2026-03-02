"""
SDD Agent - JIRA와 GitHub 통합 이슈 관리 Agent
JIRA와 GitHub의 도구를 모두 사용하여 이슈를 종합적으로 관리합니다.

도구 출처:
- GitHub 도구: @ai_function 데코레이터로 정의 (tools/github_mcp_tool.py)
- JIRA 도구: @ai_function 데코레이터로 정의 (tools/jira_mcp_tool.py)
"""

import asyncio
import os
from dotenv import load_dotenv
from agent_framework.azure import AzureOpenAIChatClient
from tools.jira_tools import JiraAutomationTools
from tools.github_tools import GitHubAutomationTools
from tools.ai_search_tools import AISearchTools


def create_sdd_agent():
    """
    JIRA와 GitHub 도구를 통합한 SDD Agent 생성
    
    - GitHub 도구: @ai_function으로 정의된 동기식 함수들
    - JIRA 도구: @ai_function으로 정의된 동기식 함수들
    
    Returns:
        통합 Agent
    """
    
    jira_tools = JiraAutomationTools()
    github_tools = GitHubAutomationTools()
    ai_search_tools = AISearchTools()

    
    # Agent 생성
    client = AzureOpenAIChatClient(
        api_key=os.environ.get("FOUNDRY_PROJECT_KEY"),
        deployment_name=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
        endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    )
    
    agent = client.as_agent(
        name="Coding Agent",
        instructions="""당신은 JIRA와 GitHub 이슈를 통합으로 관리하는 도움이 되는 어시스턴트입니다.

당신의 역할:
- JIRA 이슈를 생성, 수정, 조회할 수 있습니다.
- GitHub Issue를 생성, 수정, 조회할 수 있습니다.

## 처리 흐름

사용자가 사양 티켓 링크를 입력하면 아래 순서대로 처리하세요:

### 1단계: 사양 티켓 내용 조회
- `get_jira_issue`를 사용하여 사양 티켓의 description을 가져옵니다.

### 2단계: 기존 티켓 검색
- `search_similar_tickets`를 사용하여 사양 티켓의 description으로 유사한 기존 개발 티켓을 검색합니다.
- 유사 티켓이 이미 존재하면: 기존 개발 티켓 링크와 GitHub 이슈 링크, 티켓 내용을 사용자에게 반환하고 종료합니다.

### 3단계: 새 티켓 생성 (기존 티켓이 없는 경우)
- `create_jira_issue`를 사용하여 사양 내용 기반 개발 티켓("개발" 타입)을 생성합니다.
- `create_github_issue`를 사용하여 개발 티켓 내용 기반 GitHub 이슈를 생성합니다.

### 4단계: 결과 저장
- `save_ticket_mapping`을 사용하여 아래 정보를 저장합니다:
  - 사양 티켓 링크
  - 사양 티켓 내용(description)
  - 생성된 개발 티켓 링크
  - 생성된 GitHub 이슈 링크

### 히스토리 조회
- 사용자가 히스토리/이력을 요청하면 `get_ticket_history`를 사용하여 최근 티켓 기록을 보여줍니다.
- 기본 5개를 반환하며, 사용자가 더 많은 수를 요청하면 해당 수만큼 반환합니다.

명확하고 유용한 이슈를 작성해야 합니다. 기술적인 내용보다는 어떤 기능이 필요한 지에 초점을 맞춰 작성하세요. 
사양 티켓의 description을 최대한 활용하여 이슈를 작성하되, 불필요한 내용은 제거하고 실제 개발에 도움이 되도록 작성하는 것이 좋습니다.
""",
        tools=[
            jira_tools.create_jira_issue,
            jira_tools.update_jira_issue,
            jira_tools.get_jira_issue,
            github_tools.create_github_issue,
            github_tools.add_pr_comment,
            github_tools.get_issue,
            ai_search_tools.search_similar_tickets,
            ai_search_tools.save_ticket_mapping,
            ai_search_tools.get_ticket_history,
        ]
    )
    
    return agent


async def main():
    """SDD Agent 테스트용 메인 함수"""
    
    load_dotenv(override=True)
    
    print("🚀 SDD Agent 초기화 중...")
    agent = create_sdd_agent()
    
    print("✅ Agent 초기화 완료")
    print("   JIRA 도구(@ai_function)와 GitHub 도구(@ai_function)를 모두 사용할 수 있습니다.")
    
    link = input("jira 사양 link 입력하세요.")
    
    result = await agent.run(f"지라 사양 티켓 링크: {link}")
    print(f"Agent 실행 결과: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


