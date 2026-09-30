import asyncio
from typing import Any

from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.emitter import EventMeta
from beeai_framework.errors import FrameworkError
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool


class ConciseGlobalTrajectoryMiddleware(GlobalTrajectoryMiddleware):
    def _format_prefix(self, meta: EventMeta) -> str:
        return super()._format_prefix(meta).rstrip(": ")

    def _format_payload(self, value: Any) -> str:
        return ""


async def main() -> None:
    agent = A2AAgent(
        url="http://127.0.0.1:9996",
        memory=UnconstrainedMemory(),
    )

    await agent.check_agent_exists()
    print(f"Connected to: {agent.name}", flush=True)

    prompt = (
        "I'm based in Austin, TX. How do I get mental health "
        "therapy near me and what does my insurance cover?"
    )
    print(f"\nQuestion: {prompt}\n", flush=True)

    response = await agent.run(prompt).middleware(
        ConciseGlobalTrajectoryMiddleware(included=[Tool])
    )

    text = response.last_message.text
    if not text or not text.strip():
        raise RuntimeError("The orchestrator returned an empty answer.")

    print("\nOrchestrator response:\n")
    print(text)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except FrameworkError as error:
        raise SystemExit(error.explain()) from error