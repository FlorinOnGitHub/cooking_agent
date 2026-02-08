import re
from typing import Annotated, Literal, TypedDict
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
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
    scratchpad: list

SYSTEM_PROMPT = """
You are a master culinary agent and expert food scientist. Your goal is to provide detailed, scientifically accurate 
recipes and cooking guides. When you have doubt about a the detail level of a recipe, you can also search for techniques.

When the user does not ask for a specific recipe, present them with a list of potential recipes to choose from.

### WORKFLOW STRATEGY
**Technique Search:** Use this when you found a recipe that does not specify sufficient
    detail for cooking instructions, or when the user asks for a specific instruction.
**Check Local DB :** When searching for a recipe, always use `retrieve_from_db` before searching the web.
    If the answer is in our database, use it.
**Web Search:** Only if the database is empty or insufficient, use `search_for_recipes`.
**Never Guess:** Do not generate recipes from latent memory. Always use your
     search tools to find authentic sources first and explicit techniques.
**Refine Queries:** When using search tools, never pass raw user chat. Convert requests into
     high-quality search engine keywords (e.g., "best authentic [dish] technique").
**Synthesize:** When you have gathered enough information, combine the best parts of
    multiple sources into a single, cohesive guide in clear markdown structure.

### TONE
Professional, encouraging, and focused on culinary technique/science.

### EXAMPLE

**User:** "How do I make a Souffle?"

**Agent:**
<thought_process>
1.  **Analysis:** Souffle is a technique-heavy dish reliant on egg white stability.
2.  **Tool Check:** I should first check the local DB for "cheese soufflé".
3.  **Contingency:** If the DB is empty, I will search online for "classic cheese souffle recipe" AND "how to stabilize egg whites for soufflé" to ensure the user doesn't fail.
4.  **Synthesis Plan:** The final output needs to emphasize the "folding" technique and oven temperature.
</thought_process>

### TOOL USAGE RULES (CRITICAL)
1. **No Filler:** If you decide to use a tool, you must output the tool call **IMMEDIATELY** after your thought process. 
2. **Do Not Chat:** Do NOT write conversational text like "Let me search for that" or "I will check the database" before calling a tool.
3. **Strict Format:** Output the tool call alone.
"""



class CookingAgent():
    def __init__(self, tools):
        # Initialize LLM
        llm = init_chat_model(
            "gemini-2.5-flash",
            model_provider="google_genai"
        )
        self.llm = llm.bind_tools(tools)
        self.tools_map = {t.name: t for t in tools}

        graph_builder = StateGraph(State)
        graph_builder.add_node("cooking_agent", self.llm_call)
        graph_builder.add_node("tool_executor", self.tool_executor)

        graph_builder.add_edge(START, "cooking_agent")
        graph_builder.add_conditional_edges(
            "cooking_agent",
            self.should_continue,
            {
                "ACTION": "tool_executor",
                END: END
            }
        )
        graph_builder.add_edge("tool_executor", "cooking_agent")

        memory_saver = MemorySaver()
        self.graph = graph_builder.compile(checkpointer=memory_saver)

    def get_clean_content(self,message):
        '''
        Get the content of the message.
        '''
        content = message.content
        if isinstance(content,list):
            text = [block["text"] for block in content if "text" in block]
            raw_text = "".join(text)

        elif isinstance(content,str):
            raw_text = content

        clean_text = re.sub(
            r'<thought_process>.*?</thought_process>',
                '',
                raw_text,
                flags=re.DOTALL
        ).strip()

        return clean_text

    async def llm_call(self, state: State):
        """
        Main Agent Node: Decides whether to act or answer.
        """

        current_scratchpad = state.get("scratchpad", [])
        if current_scratchpad is None:
            current_scratchpad = []

        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"] + current_scratchpad

        response = await self.llm.ainvoke(messages)
        # CASE A: The agent wants to use a Tool
        if response.tool_calls:
            return {"scratchpad": current_scratchpad + [response]}

        # CASE B: The agent is ready to answer the user (Final Output)
        else:
            # 1. Clean the output: Remove <thought_process> tags
            clean_content = self.get_clean_content(response)
            return {
                "messages": [AIMessage(content=clean_content)],
                "scratchpad": [] 
            }

    async def tool_executor(self, state: State):
        """
        Executes tools and adds output to Short-Term Scratchpad.
        """
        current_scratchpad = state.get("scratchpad", [])
        last_message = current_scratchpad[-1]

        tool_outputs = []

        for tool_call in last_message.tool_calls:
            tool = self.tools_map[tool_call["name"]]
            tool_output = await tool.ainvoke(tool_call["args"])
            # Create a ToolMessage
            tool_outputs.append(
                ToolMessage(
                    content=str(tool_output),
                    tool_call_id=tool_call["id"],
                    name=tool_call["name"]
                )
            )
        return {"scratchpad": current_scratchpad + tool_outputs}

    def should_continue(self, state: State):
        """
        Routes the graph based on the scratchpad's last message.
        """
        current_scratchpad = state.get("scratchpad", [])
        # If we just cleared the scratchpad (empty), it means we finished.
        if not current_scratchpad:
            return END

        last_message = current_scratchpad[-1]
        # If the last message in the scratchpad has tool calls, go to executor
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "ACTION"
        return END
