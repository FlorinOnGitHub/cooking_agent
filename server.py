
from fastmcp import FastMCP
from typing import Annotated
from langchain_huggingface import HuggingFaceEmbeddings
from utils.online_search import online_search
from utils.summarize_subagents import summarize_recipes, summarize_techniques
from langchain.chat_models import init_chat_model
mcp = FastMCP(name="Recipes Server")
import chromadb

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = chromadb.PersistentClient(
    path="cookbook_db"
)


client = init_chat_model(
    "llama-3.1-8b-instant",
    model_provider="groq",
    max_tokens = 1000
)



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