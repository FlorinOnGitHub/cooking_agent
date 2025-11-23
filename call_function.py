from functions.search_for_recipes import search_for_recipes
from functions.search_for_techniqes import search_for_techniques
from functions.make_recipe import make_detailed_recipe
from google.genai import types


def call_function(function_call_part,client):
    '''
    API For tool hadnling.
    Args:
        function_call_part: FunctionCall object returned from Gemini response
        client: initialized Client to talk with Gemini
    Returns:
        Content object with either the output from the tools or an error.
    '''
    response = ""
    match function_call_part.name:

        case "search_for_recipes":
            print("Searching the web for recipes...")
            response = search_for_recipes(client, **function_call_part.args)

        case "search_for_techniques":
            print("Finding the best way to prepare...")
            response = search_for_techniques(client, **function_call_part.args)

        case "make_detailed_recipe":
            print("Finalizing recipe...")
            response = make_detailed_recipe(**function_call_part.args)
        case _:
            response = ""

    if response == "":
        return types.Content(
            role="tool",
            parts= [
                types.Part.from_function_response(
                    name = function_call_part.name,
                    response= {"error": f"Unknown function: {function_call_part.name}"}
                )
            ]
        )
    else:
        return types.Content(
            role="tool",
            parts= [
                types.Part.from_function_response(
                    name = function_call_part.name,
                    response= {"result": response}
                )
            ]
        )
