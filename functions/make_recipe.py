from google.genai import types


def make_detailed_recipe(techniques, found_recipe_text,dish_name):
    '''
    Acts as a reminder for the agent to generate the final recipe and for context injection.
    Args:
        techinques: string containing techniques found online
        found_recipe_text: initial recipe found from scariping
        dish_name: dish that the user requested the recipe for

    Returns:
        String message for final recipe creation.
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

schema_make_recipe = types.FunctionDeclaration(
    name="make_detailed_recipe",
    description="Generates the final output. Use this ONLY after you have successfully found recipe data and techniques from the other tools.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "found_recipe_text": types.Schema(
                type=types.Type.STRING,
                description="The full RAW text of the recipe instructions found using the 'search_for_recipes' tool."
            ),
            "techniques": types.Schema(
                type=types.Type.STRING,
                description="The full RAW text of the techniques or science found using the 'search_for_techniques' tool."
            ),
            "dish_name": types.Schema(
                type=types.Type.STRING,
                description="The name of the dish (e.g., 'Beef Stew')."
            )
        },
        required=["dish_name", "found_recipe_text","techniques"]
    )
)
