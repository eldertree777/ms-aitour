from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
import asyncio
from dotenv import load_dotenv
import os


async def get_jira_tools():
    """
    JIRA MCP 도구를 가져와서 반환합니다.
    Agent에서 사용할 수 있도록 formatted tools를 반환합니다.
    """

    async with stdio_client(
        StdioServerParameters(command="uvx",
                                args=["mcp-atlassian"],
                                env={"JIRA_URL": os.getenv("JIRA_URL"),
                                    "JIRA_API_TOKEN": os.getenv("JIRA_API_TOKEN"),
                                    "JIRA_USERNAME": os.getenv("JIRA_USERNAME")}),
    ) as (r, w):

        async with ClientSession(r, w) as session:
            await session.initialize()

            tools = await session.list_tools()

            formatted_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    }
                } for tool in tools.tools
            ]

            return formatted_tools


async def main():
    load_dotenv(override=True)
    tools = await get_jira_tools()
    print(f"Available JIRA tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool['function']['name']}: {tool['function']['description']}")
    return tools


if __name__ == "__main__":
    load_dotenv(override=True)
    asyncio.run(main())