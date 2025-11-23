from google.genai import types
from functions.online_search import online_search



def search_for_recipes(client,query):
    '''
    Search the internet for relevant recipes and outputs a formated list

    Args:
        client: initialized Client to talk with Gemini
        query: internet query string
    Returns:
        recipes: string containing all the recipes without the errors.
    '''
    raw_recipes = online_search(query)
    recipes = summarize_recipes(client,raw_recipes)
    return recipes



def summarize_recipes(client, recipes):
    '''
    Summarize and cleans recipe data to pass to main agent. Uses an additional API call, but it greatly reduces required context.

    Args:
        client: initialized Client to talk with Gemini
        recipes: raw recipe data from web scraper:
    Returns:
        cleaned and summarized recipes.
    '''

    SYSTEM_PROMPT = """
You are an expert data cleaning agent. Your task is to extract and sanitize recipe data from raw web-scraped text.
Input: A raw string of text containing content from multiple websites.
Instructions:
    Identify Valid Recipes: A valid recipe MUST contain three elements: a Title, an Ingredients List, and
    Preparation Steps. Discard any text that does not meet these criteria.
    Filter Noise: Aggressively remove all:
        Navigation menus, footers, and sidebar content.
        'Access Denied', '403 Forbidden', or 'Captcha' error messages.
        SEO-driven blog narratives, personal stories, or lengthy introductions.
        Advertisements and promotional redirects.
    Format: Return the data as a clean Markdown list. Use ## for the Recipe Title, - for Ingredients, and 1. for Steps.
Constraint: If a extracted segment is a partial recipe or an error message, output nothing for that segment. Do not include any conversational text, 
preambles, or summaries. Just the structured data) """
    response = client.models.generate_content(
        model = "gemini-2.5-flash", contents = recipes,
        config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    )
    return response.text


schema_search_for_recipes = types.FunctionDeclaration(
    name="search_for_recipes",
    description="Search the web for a list of recipes given the specified prompt and will return al the recipes",
    parameters =types.Schema(
        type = types.Type.OBJECT,
        properties = {
            "query" : types.Schema(
                type = types.Type.STRING,
                description= "Query recipe to search the internet for"

            )
        }
    )
)