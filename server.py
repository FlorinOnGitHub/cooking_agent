
from fastmcp import FastMCP
from typing import Annotated
from langchain_huggingface import HuggingFaceEmbeddings
from utils.online_search import online_search
from utils.summarize_subagents import summarize_recipes, summarize_techniques
from langchain.chat_models import init_chat_model
mcp = FastMCP(name="Recipes Server")
from langchain_chroma import Chroma

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(
    persist_directory="cookbook_db",
    collection_name="recipes",
    embedding_function=embedding_model
)


client = init_chat_model(
    "llama-3.1-8b-instant",
    model_provider="groq",
    max_tokens = 1000
)

# @mcp.prompt()
# def make_recipe(
#     techniques: Annotated[str,"string containing techniques found online"],
#     found_recipe_text: Annotated[str, "initial recipe found from scariping"],
#     dish_name: Annotated[str,"dish that the user requested the recipe for"]):
#     '''
#     Generates the final output. Use this ONLY after you have successfully found recipe data and techniques from the other tools.
#     '''

#     return f"""
#     SUCCESS: Data Gathered.
#     DISH: {dish_name}
#     SOURCE RECIPE DATA:
#     {found_recipe_text}

#     SOURCE TECHNIQUE DATA:
#     {techniques}

#     INSTRUCTIONS FOR AGENT:
#     Please combine the Source Recipe Data with the Source Technique Data.
#     Create a 'Master Recipe' in Markdown format.
#     1. Start with a catchy title.
#     2. List Ingredients.
#     3. Write detailed Instructions, incorporating the specific techniques (explain 'WHY' we do each step). Do not forget to add cooking times.
#     """

@mcp.tool()
def retrieve_from_db(query: Annotated[str,"Recipe query to search the local database"]):
    '''
    Retrieves verified recipes or techniques from the local vector database (ChromaDB).
    Use this BEFORE searching the web to check if we already have the info.
    '''
    print(f"Querying ChromaDB for: {query}")
    try:

        collection = db.get_collection(name="recipes")
        # Query the database
        results = collection.query(
            query_texts=[query],
            n_results=3
        )

        documents = results['documents'][0]
        metadatas = results['metadatas'][0]

        formatted_output = "Found the following in database:\n"
        for i, doc in enumerate(documents):
            source = metadatas[i].get('source', 'Unknown')
            formatted_output += f"---\nSource: {source}\nContent: {doc}\n"

        return formatted_output

    except Exception as e:
        return f"Error querying database: {str(e)}"


@mcp.tool()
def search_for_recipes(query: Annotated[str,"User recipe query to search the internet with"]):
    '''
    Search the web for a list of recipes given the specified prompt and will return al the recipes
    '''
    print("searching for recipes")
    raw_recipes = online_search(query)
    recipes = summarize_recipes(client,raw_recipes)
    return recipes


@mcp.tool()
def search_for_techniques(query: Annotated[str,"User techniques query to search the internet with"]):
    '''
    Search the web for multiple techniques that can help in giving detailed instructions for a specific recipe or ingredient
    and return a formated list
    '''
    print("searching for techiques")
    raw_techniques = online_search(query)
    techniques = summarize_techniques(client,raw_techniques)
    return techniques

if __name__ == "__main__":
    mcp.run(transport="sse")