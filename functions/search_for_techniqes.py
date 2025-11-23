from functions.online_search import online_search
from google.genai import types



def search_for_techniques(client,query):
    '''
    Search the internet for relevant cooking techniques and outputs a formated list

    Args:
        client: initialized Client to talk with Gemini
        query: internet query string
    Returns:
        recipes: string containing all the techniques without the errors.
    '''
    raw_techniques = online_search(query)
    techniques = summarize_techniques(client,raw_techniques)
    return techniques



def summarize_techniques(client, techniques):
    '''
    Summarize and cleans techique data to pass to main agent. Again, used for reducing context size.

    Args:
        client: initialized Client to talk with Gemini
        recipes: raw recipe data from web scraper:
    Returns:
        cleaned and summarized techniques.
    '''

    SYSTEM_PROMPT = """
You are an expert data cleaning agent. Your task is to extract and sanitize recipe instructions and cooking techniques from raw web-scraped text.
Input: A raw string of text containing content from multiple websites.
Instructions:
    Identify Valid Instructions: A valid instruction must refer to the ingredient or recipe related to the recipe
    Preparation Steps: Discard any text that does not meet these criteria.
    Filter Noise: Aggressively remove all:
        Navigation menus, footers, and sidebar content.
        'Access Denied', 'system', '403 Forbidden', or 'Captcha' error messages.
        SEO-driven blog narratives, personal stories, or lengthy introductions.
        Advertisements and promotional redirects.
    Format: Return the data as a text list of instructions. Format it in such a way that it will be clear to an LLM that these are techniques.
Constraint: If a extracted segment is a partial recipe or an error message, output nothing for that segment. Do not include any conversational text,
preambles, or summaries. Just the structured data) """
    response = client.models.generate_content(
        model = "gemini-2.5-flash", contents = techniques,
        config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    )
    return response.text

schema_search_for_techniques = types.FunctionDeclaration(
    name="search_for_techniques",
    description="Search the web for multiple techniques that can help in giving detailed instructions for a specific recipe or ingredient",
    parameters =types.Schema(
        type = types.Type.OBJECT,
        properties = {
            "query" : types.Schema(
                type = types.Type.STRING,
                description= "Query technique to search the internet for"

            )
        }
    )
)