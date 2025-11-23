from google import genai
import os
from dotenv import load_dotenv
from google.genai import types
from functions.search_for_recipes import schema_search_for_recipes
from functions.make_recipe import schema_make_recipe
from functions.search_for_techniqes import schema_search_for_techniques
from call_function import call_function
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


SYSTEM_PROMPT = """You are a master culinary agent and exper food scientist. Your goal is to provide either a list of recipes or
        detailed instructions for a specific recipe
        You have 3 tools available which you can use to respond to requests. Do not guess recipes, always search for them.

        ### TOOL USAGE GUIDLINES
        1. search_for_recipes:
            - **WHEN TO USE**: when the user asks for a broad recipe or when presented with some specific ingredients(e.g.
              "I have some bananas, what can I make with them", "Easy beef stir fry recipes" )
            - **QUERY OPTIMIZATION:** You must convert the user's natural language into a targeted search engine query.
                - BAD: "I want a recipe for beef stew"
                - GOOD: "best classic beef stew recipe authentic ingredients instructions"

        2. search_for_techniques:
            - **WHEN TO USE**: use this when the user asks for how to make a specific recipe or when current instruction are not clear enough
            - **QUERY OPTIMIZATION:** Focus on guides, science, and tips.
                - BAD: "How to make fries"
                - GOOD: "best way to make french fries technique guide and instructions"
        3. make_detailed_recipe:
            - **WHEN TO USE**: use this tool when you have gathered enough information about the requested recipe and are confident you
            can give detailed instructions.

        ### CRITICAL INSTRUCTION: QUERY REFINEMENT
        Do not pass the user's raw input into the tools. You are the "Query Refiner". You must strip conversational filler
        ("Hello", "Please", "I'm hungry") and extract only the core culinary keywords to ensure the web scraper finds high-quality results.
                    """

def main():
    """
    Main loop that records messages and calls tools.
    """

    load_dotenv()
    API_KEY = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=API_KEY)
    console = Console()

    available_functions = types.Tool(
    function_declarations=[
        schema_search_for_recipes,
        schema_search_for_techniques,
        schema_make_recipe
    ])

    messages = []
    max_iters = 10

    console.print(Markdown("## Welcome to your personal cooking agent!"))
    console.print(Markdown("If you wish to close the chat, type 'exit'"))
    while True:

        console.print(Markdown("Ask me anything"))
        user_prompt = input()

        if user_prompt == "exit":
            break
        messages.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))

        for _ in range(max_iters): # upper bound on the number of consecutive tool calls
            response = client.models.generate_content(
                model = "gemini-2.5-flash", contents= messages,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, tools=[available_functions])
            )

            if response.candidates:
                for candidate in response.candidates:
                    messages.append(candidate.content)

            if response.function_calls:
                for function_call_part in response.function_calls:
                    response = call_function(function_call_part, client)
                    messages.append(response)
            else:
                console.print(Markdown(response.text))
                break


if __name__ == "__main__":
    main()