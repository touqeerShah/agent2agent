import asyncio
import os

import uvicorn
from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent
from google.adk.tools import google_search

from ddgs import DDGS
from google.adk.models.lite_llm import LiteLlm


import logging
import warnings

logging.disable(level=logging.WARNING)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

load_dotenv()

# Authenticate
is_local = os.getenv("IS_LOCAL", "false").strip().lower() in {"true", "1", "yes"}
async def web_search(query: str) -> dict:
    """Search the web and return titles, URLs, and text snippets.

    Args:
        query: The search query.
    """
    results = await asyncio.to_thread(lambda: DDGS().text(query, max_results=5))
    return {"results": results}


if is_local:
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    os.environ["OLLAMA_API_BASE"] = ollama_url

    selected_model = LiteLlm(
        model=f"ollama_chat/{os.getenv('OLLAMA_MODEL', 'qwen2.5:7b-instruct')}",
        api_base=ollama_url,
    )
    selected_tools = [web_search]
else:
    from helpers import authenticate

    credentials, project_id = authenticate(location="global")

    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

    selected_model = os.getenv("RESEARCH_MODEL", "gemini-3.1-pro-preview")
    selected_tools = [google_search]

PORT = int(os.environ.get("RESEARCH_AGENT_PORT"))
HOST = os.environ.get("AGENT_HOST")
instruction=(
    "You are a healthcare research agent. "
    "Use the available web search tool to find information about "
    "conditions, symptoms, treatments, and procedures. "
    "Prefer authoritative healthcare sources. "
    "Cite source URLs supporting your answers. "
    "If search fails or evidence is insufficient, state that clearly."
)
research_agent = LlmAgent(
    # NOTE: This model has been updated since the video was recorded.
    name="HealthResearchAgent",
    model=selected_model,
    tools=selected_tools,
    instruction=instruction,
    description="Provides healthcare information about symptoms, health "
    "conditions, treatments, and procedures using up-to-date web resources.",
)



def main() -> None:
    # Make your agent A2A-compatible
    a2a_app = to_a2a(research_agent, host=HOST, port=PORT)
    print("Running Health Research Agent")
    uvicorn.run(a2a_app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
