from google.genai import types
from fastmcp import FastMCP
from typing import Annotated
from google import genai
import os

from utils.online_search import online_search
from utils.summarize_subagents import summarize_recipes, summarize_techniques


mcp = FastMCP(name="Recipes Server")

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

mcp.run(transport="sse")

@mcp.prompt
def make_recipe(
    techniques: Annotated[str,"string containing techniques found online"],
    found_recipe_text: Annotated[str, "initial recipe found from scariping"],
    dish_name: Annotated[str,"dish that the user requested the recipe for"]):
    '''
    Generates the final output. Use this ONLY after you have successfully found recipe data and techniques from the other tools.
    '''

    return f"""
    SUCCESS: Data Gathered.
    DISH: {dish_name}
    SOURCE RECIPE DATA:
    {found_recipe_text}

    SOURCE TECHNIQUE DATA:
    {techniques}

    INSTRUCTIONS FOR AGENT:
    Please combine the Source Recipe Data with the Source Technique Data.
    Create a 'Master Recipe' in Markdown format.
    1. Start with a catchy title.
    2. List Ingredients.
    3. Write detailed Instructions, incorporating the specific techniques (explain 'WHY' we do each step). Do not forget to add cooking times.
    """



@mcp.tool
def search_for_recipes(query: Annotated[str,"User recipe query to search the internet with"]):
    '''
    Search the web for a list of recipes given the specified prompt and will return al the recipes
    '''
    raw_recipes = online_search(query)
    recipes = summarize_recipes(client,raw_recipes)
    return recipes


@mcp.tool
def search_for_techniques(query: Annotated[str,"User techniques query to search the internet with"]):
    '''
    Search the web for multiple techniques that can help in giving detailed instructions for a specific recipe or ingredient
    and return a formated list
    '''
    raw_techniques = online_search(query)
    techniques = summarize_techniques(client,raw_techniques)
    return techniques