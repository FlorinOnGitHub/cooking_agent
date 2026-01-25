import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage
from agent import CookingAgent
from rich.markdown import Markdown
from rich.console import Console

load_dotenv()

async def main():

    client = MultiServerMCPClient({
        "localhost": {
            "url": "http://localhost:8000/sse",
            "transport": "sse"
        }
    })

    tools = await client.get_tools()

    console = Console()
    bot = CookingAgent(tools)
    config = {
        "configurable": {"thread_id": "session_1"},
        "recursion_limit": 10
        }
    console.print(Markdown("## Welcome to your personal cooking agent!"))
    console.print(Markdown("If you wish to close the chat, type 'exit'"))
    console.print(Markdown("\n# What are you craving?"))

    while True:
        user_input = input("[USER]")
        if user_input.lower() in ["quit", "exit"]:
            break

        inputs = {"messages": [HumanMessage(content=user_input)]}

        # Run the agent
        console.print(Markdown("[POCKET GORDON RAMSAY]"))
        async for event in bot.graph.astream(inputs, config=config, stream_mode="values"):
            message = event["messages"][-1]
            if message.type == "ai":

                console.print(Markdown(message.content))

        console.print("\n")
        console.print(Markdown("Anything else I can help you with"))

if __name__ == "__main__":
    asyncio.run(main())