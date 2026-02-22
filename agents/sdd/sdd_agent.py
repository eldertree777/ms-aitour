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
- "사양" 티켓을 읽고, "개발" 티켓을 생성 후 이 내용 기반으로 github issue를 생성해야 합니다.
- 명확하고 유용한 이슈를 작성해야 합니다.
- 사양 티켓이 변경 되었고 기존 개발 티켓이 이미 존재한다면, 개발 티켓과 github issue 및 PR도 업데이트 해야 합니다. 
  - AI Search Tool을 이용하면, 비슷한 "개발" 티켓 이름과 description을 조회할 수 있습니다.
  - 변경된 내용을 PR에 코멘트로 추가해야 합니다.
""",
    tools=[
            jira_tools.create_jira_issue,
            jira_tools.update_jira_issue,
            jira_tools.get_jira_issue,
            github_tools.create_github_issue,
            github_tools.add_pr_comment,
            github_tools.get_issue
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


