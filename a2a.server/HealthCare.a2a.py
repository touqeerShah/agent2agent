from dotenv import load_dotenv
import asyncio
import os
from beeai_framework.adapters.a2a.serve.server import A2AServer, A2AServerConfig
from agents.HealthCareAgent import HealthCareAgent
from beeai_framework.serve.utils import LRUMemoryManager


def main():
    print(f"Running A2A Orchestrator Agent")
    load_dotenv()
    host = os.environ.get("AGENT_HOST")
    healthcare_agent_port = int(os.environ.get("HEALTHCARE_AGENT_PORT"))
    # Register the agent with the A2A server and run the HTTP server
    # we use LRU memory manager to keep limited amount of sessions in the memory
    healthcare_agent = HealthCareAgent()
    A2AServer(
        config=A2AServerConfig(
            port=healthcare_agent_port, protocol="jsonrpc", host=host
        ),
        memory_manager=LRUMemoryManager(maxsize=100),
    ).register(healthcare_agent, send_trajectory=True).serve()


if __name__ == "__main__":
    main()
