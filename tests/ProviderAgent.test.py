import asyncio

from agents.ProviderAgent import ProviderAgent


async def main():
    agent = await ProviderAgent().initialize()
    response = await agent.answer_query(
        "Find cardiologists in US Phoenix."
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())