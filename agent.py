from typing import Annotated, Literal, TypedDict
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool

class MessageClassifier(BaseModel):
    message_type: Literal["recipes", "technique", ""] = Field(
        ...,
        description="Classify if the message requires "
    )

class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None

SYSTEM_PROMPT = """
You are a master culinary agent and expert food scientist. Your goal is to provide detailed, scientifically accurate 
recipes and cooking guides. When you have doubt about a the detail level of a recipe, you can also search for techniques.

When the user does not ask for a specific recipe, present them with a list of potential recipes to choose from.

### WORKFLOW STRATEGY
1. **Check Local DB First:** Always use `retrieve_from_db` before searching the web.
    If the answer is in our database, use it.
2. **Web Search:** Only if the database is empty or insufficient, use `search_for_recipes`.
3. **Never Guess:** Do not generate recipes from latent memory. Always use your
     search tools to find authentic sources first and explicit techniques.
4. **Refine Queries:** When using search tools, never pass raw user chat. Convert requests into
     high-quality search engine keywords (e.g., "best authentic [dish] technique").
5. **Synthesize:** When you have gathered enough information, combine the best parts of
    multiple sources into a single, cohesive guide in clear markdown structure.

### TONE
Professional, encouraging, and focused on culinary technique/science.
"""


class CookingAgent():

    def __init__(self,tools):
        llm = init_chat_model(
            "llama-3.3-70b-versatile",
            model_provider="groq"
        )
        self.llm = llm.bind_tools(tools)

        graph_builder = StateGraph(State)
        graph_builder.add_node("cooking_agent", self.llm_call)
        graph_builder.add_node("tools", ToolNode(tools))

        graph_builder.add_edge(START,"cooking_agent")
        graph_builder.add_conditional_edges(
            "cooking_agent",
            self.should_continue,
            {
                "ACTION" : "tools",
                END : END
            }
        )
        memory_saver = MemorySaver()
        graph_builder.add_edge("tools", "cooking_agent")
        self.graph = graph_builder.compile(checkpointer=memory_saver)

    async def llm_call(self, state: State):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = await self.llm.ainvoke(messages)
        return {"messages": [response]}

    async def should_continue(self, state: State):

        '''
        Decide to continue with the loop
        '''
        last_message = state['messages'][-1]
        if last_message.tool_calls:
            return "ACTION"
        return END

