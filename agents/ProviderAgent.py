import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from langchain_ollama import ChatOllama


class ProviderAgent:
    def __init__(self) -> None:
        load_dotenv()

        self.is_local = os.getenv("IS_LOCAL", "false").strip().lower() in {
            "true",
            "1",
            "yes",
        }

        if self.is_local:
            self.model = ChatOllama(
                model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct"),
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=0,
                num_ctx=16384,
                num_predict=1024,
            )
        else:
            self.model = ChatAnthropic(
                model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
                temperature=0,
                max_tokens=1024,
            )

        # Assumes this file is agents/ProviderAgent.py.
        project_root = Path(__file__).resolve().parents[1]
        server_path = Path(os.getenv("MCP_SERVER_PATH", "mcp/mcpserver.py"))
        if not server_path.is_absolute():
            server_path = project_root / server_path

        if not server_path.is_file():
            raise FileNotFoundError(
                f"MCP server not found: {server_path}. "
                "Set MCP_SERVER_PATH to its actual location."
            )

        self.mcp_client = MultiServerMCPClient(
            {
                "find_healthcare_providers": StdioConnection(
                    transport="stdio",
                    command="uv",
                    args=["run", str(server_path)],
                    cwd=str(project_root),
                )
            }
        )
        self.agent = None

    async def initialize(self):
        tools = await self.mcp_client.get_tools()

        self.agent = create_agent(
            model=self.model,
            tools=tools,
            name="HealthcareProviderAgent",
            system_prompt=(
                "Find healthcare providers using the "
                "find_healthcare_providers MCP tool. "
                "Only list providers returned by the tool. "
                "Never invent provider information. "
                "Ask for clarification if required search details "
                "are missing. Present results in a Markdown table. "
                "If the tool returns no matches, state that clearly."
            ),
        )
        return self

    async def answer_query(self, prompt: str) -> str:
        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        response = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": prompt}]}
        )

        content = response["messages"][-1].content
        if isinstance(content, str):
            return content

        return "\n".join(
            block if isinstance(block, str) else block.get("text", "")
            for block in content
            if isinstance(block, (str, dict))
        )
