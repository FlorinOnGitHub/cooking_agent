from google.genai import types




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
        model = "gemini-2.5-flash-lite", contents = recipes,
        config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    )
    return response.text


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
        model = "gemini-2.5-flash-lite", contents = techniques,
        config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    )
    return response.text