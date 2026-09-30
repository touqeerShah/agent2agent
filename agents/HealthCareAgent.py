from dotenv import load_dotenv

# from helpers import authenticate
from typing import Any
import asyncio
import os
from beeai_framework.adapters.a2a.serve.server import A2AServer, A2AServerConfig
from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.adapters.vertexai import VertexAIChatModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import (
    ConditionalRequirement,
)
from beeai_framework.adapters.ollama import OllamaChatModel
from beeai_framework.adapters.vertexai import VertexAIChatModel

from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import EventMeta, GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool, tool
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.tools.think import ThinkTool


# Log only tool calls
class ConciseGlobalTrajectoryMiddleware(GlobalTrajectoryMiddleware):
    def _format_prefix(self, meta: EventMeta) -> str:
        prefix = super()._format_prefix(meta)
        return prefix.rstrip(": ")

    def _format_payload(self, value: Any) -> str:
        return ""


def HealthCareAgent():
    print(f"Running A2A Orchestrator Agent")
    load_dotenv()
    # _, project_id = authenticate()

    host = os.environ.get("AGENT_HOST")
    policy_agent_port = os.environ.get("POLICY_AGENT_PORT")
    research_agent_port = os.environ.get("RESEARCH_AGENT_PORT")
    provider_agent_port = os.environ.get("PROVIDER_AGENT_PORT")
    healthcare_agent_port = int(os.environ.get("HEALTHCARE_AGENT_PORT"))

    # Log only tool calls
    middlewares = (
        [
            GlobalTrajectoryMiddleware(included=[Tool]),
        ],
    )
    policy_agent = A2AAgent(
        url=f"http://{host}:{policy_agent_port}", memory=UnconstrainedMemory()
    )
    # Run `check_agent_exists()` to fetch and populate AgentCard
    asyncio.run(policy_agent.check_agent_exists())
    print("\tℹ️", f"{policy_agent.name} initialized")

    research_agent = A2AAgent(
        url=f"http://{host}:{research_agent_port}", memory=UnconstrainedMemory()
    )
    asyncio.run(research_agent.check_agent_exists())
    print("\tℹ️", f"{research_agent.name} initialized")

    provider_agent = A2AAgent(
        url=f"http://{host}:{provider_agent_port}", memory=UnconstrainedMemory()
    )
    asyncio.run(provider_agent.check_agent_exists())
    print("\tℹ️", f"{provider_agent.name} initialized")
    is_local = os.getenv("IS_LOCAL", "false").strip().lower() in {"true", "1", "yes"}

    if is_local:
        llm = OllamaChatModel(os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct"))
        llm.parameters.temperature = 0
    else:
        from helpers import authenticate

        _, project_id = authenticate()

        llm = VertexAIChatModel(
            model_id=os.getenv("VERTEX_MODEL", "gemini-2.5-flash"),
            project=project_id,
            location="global",
            allow_parallel_tool_calls=True,
            settings={
                "api_base": os.getenv("GOOGLE_VERTEX_BASE_URL"),
                "use_psc_endpoint_format": True,
            },
        )
    healthcare_agent = RequirementAgent(
        name="Healthcare Agent",
        description="A personal concierge for Healthcare Information, customized to your policy.",
        llm=llm,
        tools=[
            thinktool := ThinkTool(),
            policy_tool := HandoffTool(
                target=policy_agent,
                # name=policy_agent.name,
                name="policy_lookup",
                description=policy_agent.agent_card.description,
            ),
            research_tool := HandoffTool(
                target=research_agent,
                # name=research_agent.name,
                name="research_lookup",
                description=research_agent.agent_card.description,
            ),
            provider_tool := HandoffTool(
                target=provider_agent,
                # name=provider_agent.name,
                name="provider_lookup",
                description=provider_agent.agent_card.description,
            ),
        ],
        requirements=[
            ConditionalRequirement(
                policy_tool.name, consecutive_allowed=False  # String; matches by name
            ),
            ConditionalRequirement(
                ThinkTool, force_at_step=1, force_after=Tool, consecutive_allowed=False
            ),
        ],
        role="Healthcare Concierge",
        instructions=(
            f"""You are a concierge for healthcare services. Your task is to handoff to one or more agents to answer questions and provide a detailed summary of their answers. Be sure that all of their questions are answered before responding.
            Use `{policy_agent.name}` to answer insurance-related questions.
            
            IMPORTANT: When returning answers about providers, only output providers from `{provider_agent.name}` and only provide insurance information based on the results from `{policy_agent.name}`.
    
            In your output, put which agent gave you the information!"""
        ),
    )

    print("\tℹ️", f"{healthcare_agent.meta.name} initialized")
    from importlib.metadata import version

    async def check_registration():
        print("Loaded file:", __file__, flush=True)
        print("BeeAI version:", version("beeai-framework"), flush=True)

        original_names = [t.name for t in healthcare_agent.meta.tools]
        copied_agent = await healthcare_agent.clone()
        copied_names = [t.name for t in copied_agent.meta.tools]

        print("Original tools:", original_names, flush=True)
        print("Copied tools:", copied_names, flush=True)

        assert policy_tool.name in original_names, "Policy tool missing before cloning"
        assert policy_tool.name in copied_names, "Policy tool missing after cloning"
    asyncio.run(check_registration())
    return healthcare_agent
