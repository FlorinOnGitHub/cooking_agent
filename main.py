import asyncio
from google import genai
import os
from dotenv import load_dotenv
from google.genai import types
from mcp import StdioServerParameters
from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv
import sys
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.runners import InMemoryRunner


load_dotenv()

SYSTEM_PROMPT = """
You are a master culinary agent and expert food scientist. Your goal is to provide detailed, scientifically accurate 
recipes and cooking guides.

### WORKFLOW STRATEGY
1. **Never Guess:** Do not generate recipes from latent memory. Always use your
     search tools to find authentic sources first.
2. **Refine Queries:** When using search tools, never pass raw user chat. Convert requests into
     high-quality search engine keywords (e.g., "best authentic [dish] technique").
3. **Synthesize:** When you have gathered enough information, combine the best parts of 
    multiple sources into a single, cohesive guide.

### TONE
Professional, encouraging, and focused on culinary technique/science.
"""


async def main():
    """
    Main loop that records messages and calls tools.
    """

    console = Console()

    connection_params = SseConnectionParams(url="http://localhost:8000/sse")

    # 4. Initialize the Toolset
    # Note: This is now a SINGLE object, not a list of tools yet.
    mcp_tools = MCPToolset(connection_params=connection_params)
    client = LlmAgent(
        name = "cooking_agent",
        model = "gemini-2.5-flash",
        tools = [mcp_tools],
        instruction=SYSTEM_PROMPT
    )


    runner = InMemoryRunner(agent=client)

    console.print(Markdown("## Welcome to your personal cooking agent!"))
    console.print(Markdown("If you wish to close the chat, type 'exit'"))
    console.print(Markdown("\n# What are you craving?"))
    while True:

        user_prompt = await asyncio.to_thread(input, ">> ")
        if user_prompt == "exit":
            break

        response = await runner.run_debug(user_prompt,quiet=True)

        console.print(Markdown(response[-1].content.parts[-1].text))

if __name__ == "__main__":
    asyncio.run(main())