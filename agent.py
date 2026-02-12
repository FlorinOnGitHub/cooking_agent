import re
from typing import Annotated, TypedDict, Optional
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from operator import add
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool
import yaml


def none_add(a, b) :

    if b is not None:
        return a +b
    return a

class State(TypedDict):
    messages: Annotated[list, add_messages]
    recipes: Annotated[list, none_add]
    techniques: Annotated[list,none_add]
    recipe_query: str
    technique_query: str
    tool_calls : str
    finished_techniques : bool
    finished_recipes: bool

class SearchPlan(BaseModel):
    recipe_query: Optional[str] = Field(
        default= None ,
        description= "Query used to search for recipes. Can be null if the user does not ask for a recipe"
    )
    technique_query: Optional[str] = Field(
        default= None ,
        description= "Query used to search for recipes. Can be null if the user does" \
        "not ask for a specific recipe or only about ingredients"
    )


class Techniques(BaseModel):
    techniques : Optional[list[str]] = Field(
        default= None,
        description= "The techniques found so far. Can be none if no techniqes are needed"
    )
    technique_query : Optional[str] = Field(
        default= None,
        description= "Query to search for techniqes. If the given techniques are sufficient, " \
        "this field can be null (no more search is needed)"
    )



def load_agent_config(agent_name, yaml_path="agents.yaml"):
    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)

    agent_cfg = config["agents"].get(agent_name)
    if not agent_cfg:
        raise ValueError(f"Agent {agent_name} not found in YAML")

    return agent_cfg

class CookingAgent():
    def __init__(self, tools):
        # Initialize LLM
        self.base_llm = init_chat_model(
           # "qwen/qwen3-32b",
            "llama-3.3-70b-versatile",
            model_provider="groq",
        )

        self.tools_map = {t.name: t for t in tools}

        self.planner_llm, self.planner_prompt = self.get_planner_llm(self.base_llm)
        self.technique_llm, self.techniqe_refiner_prompt = self.get_technique_refiner_llm(self.base_llm)
        self.recipe_llm, self.recipe_prompt = self.get_recipe_refiner_llm(self.base_llm)
        self.writer_prompt = load_agent_config("writer")["system_prompt"]


        self.graph = self.build_graph()
        self.graph.get_graph().draw_mermaid_png(output_file_path="agent.png")


    def get_planner_llm(self,base_llm):

        planner_cfg = load_agent_config("planner")
        planner_llm = base_llm.with_structured_output(SearchPlan)
        planner_prompt = planner_cfg["system_prompt"]
        return planner_llm, planner_prompt
    
    def get_technique_refiner_llm(self,base_llm):
        technique_cfg = load_agent_config("technique_refiner")
        technique_llm = base_llm.with_structured_output(Techniques)
        techniques_refiner_prompt = technique_cfg["system_prompt"]
        return technique_llm, techniques_refiner_prompt

    def get_recipe_refiner_llm(self,base_llm):

        recipe_config = load_agent_config("recipe_refiner")
        recipe_prompt = recipe_config["system_prompt"]
        recipe_tools = [self.tools_map[t] for t in recipe_config["tools"]]
        recipe_llm = base_llm.bind_tools(recipe_tools)
        return recipe_llm, recipe_prompt

    def build_graph(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("technique_search", self.technique_search)
        graph_builder.add_node("technique_refiner", self.techniqe_refiner)
        graph_builder.add_node("recipe_refiner", self.recipe_refiner)
        graph_builder.add_node("tool_executor", self.tool_executor)
        graph_builder.add_node("database_search", self.database_search)
        graph_builder.add_node("writer", self.writer)
        graph_builder.add_node("aggregator", self.aggregator)

        graph_builder.add_edge(START, "planner")
        graph_builder.add_conditional_edges(
            "planner",
            self.should_start_recipes,
            {
                "Search DB": "database_search",
                "Writer": "writer",
                END : END
            }
        )

        graph_builder.add_edge("database_search", "recipe_refiner")

        graph_builder.add_conditional_edges(
            "recipe_refiner",
            self.should_continue_recipes,
            {
                "Search Again": "tool_executor",
                "Finish Recipe": "aggregator"
               
            }
           
        )
        graph_builder.add_edge("tool_executor", "recipe_refiner")
        graph_builder.add_conditional_edges(
            "planner",
            self.should_continue_techniques,
            {
                "Search Technique": "technique_search",
                "Writer": "writer",
                "Finish Recipe": "aggregator",
                END : END
              
            },

        )

        graph_builder.add_conditional_edges(
            "aggregator",
            self.should_start_writing,
            {
                END: END,
                "Write" : "writer"
            }
        )

        graph_builder.add_edge("technique_search", "technique_refiner")

        graph_builder.add_conditional_edges(
            "technique_refiner",
            self.should_continue_techniques,
            {
                "Search Technique": "technique_search",
                "Finish Recipe": "aggregator"
            }
        )

        graph_builder.add_edge("writer", END)


        memory_saver = MemorySaver()
        graph = graph_builder.compile(checkpointer=memory_saver)
        return graph

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
    


    async def planner(self,state:State):
        """
        Subagent that plans recipe creation
        """
        messages = [SystemMessage(content=self.planner_prompt)] + state["messages"]

        response = await self.planner_llm.ainvoke(messages)

        finished_recipes = response.recipe_query is None
        finished_techniques = response.technique_query is None
        return {
            "messages": state["messages"],
            "recipe_query": response.recipe_query,
            "technique_query": response.technique_query,
            "finished_recipes": finished_recipes,
            "finished_techniques": finished_techniques
        }
    


    async def technique_search(self,state:State):
        """
        Tool Node to search for Techniques
        """
        tool = self.tools_map["search_for_techniques"]
        technique_query = state.get("technique_query", None)

        tool_output = await tool.ainvoke({"query": technique_query})

        return {"techniques":  [str(tool_output)]}


    async def techniqe_refiner(self,state:State):

        messages = [SystemMessage(content=self.techniqe_refiner_prompt)]

        response = await self.technique_llm.ainvoke(messages)

        finished_techniques =  response.technique_query is None

        return {
            "techniques" :  response.techniques,
            "technique_query" : response.technique_query,
            "finished_techniques": finished_techniques
        }


    async def database_search(self, state:State):

        tool = self.tools_map["retrieve_from_db"]
        recipe_query = state.get("recipe_query", None)
        if recipe_query == None:
            return state
        tool_output = await tool.ainvoke({"query": recipe_query})
        return {"recipes":  [str(tool_output)]}
    

    async def recipe_refiner(self,state:State):

        current_recipes = state.get("recipes")
        
        current_tool_calls = state.get("tool_calls", [])
  
        messages = [SystemMessage(content=self.recipe_prompt + str(current_recipes) + "PAST TOOL CALLS" + str(current_tool_calls))]

        response = await self.recipe_llm.ainvoke(messages)
        

        if response.tool_calls:
            return {
                "tool_calls" : current_tool_calls + [response],
            }
        else:
            # 1. Clean the output: Remove <thought_process> tags
            clean_content = self.get_clean_content(response)
            return {
                "recipes" :  [clean_content],
                "recipe_query" : None,
                "tool_calls" : None,
                "finished_recipes": True
            }
        
    async def aggregator(self, state:State):
        """
        Aggregator dummy node to check if both paths are finished.
        """
        return {}

    async def should_start_recipes(self,state:State):

        finished_recipes= state.get("finished_recipes")
        finished_techniques= state.get("finished_techniques")
    
        # Both are empty (User said "Hello") -> Go to Writer to chat
        if finished_recipes and finished_techniques:
            return "Writer"
        elif finished_recipes:
            return END
        return "Search DB"


    async def should_start_writing(self,state:State):

        finished_recipes = state.get("finished_recipes")
        finished_techniques = state.get("finished_techniques")

        if finished_recipes and finished_techniques:
            return "Write"
        else:
            return END

    async def should_continue_recipes(self,state:State):

        tool_called = state.get("tool_calls", [])
        if tool_called is not None and len(tool_called) >= 2:
            return "Finish Recipe"
        if tool_called == None:
            return "Finish Recipe"
        else:
            return "Search Again"

    async def should_continue_techniques(self,state:State):

        if state["finished_techniques"] is True:
            return "Finish Recipe"
        else :
            return "Search Technique"


    async def tool_executor(self, state: State):
        """
        Executes tools and adds output to Short-Term Scratchpad.
        """
        current_tools = state.get("tool_calls", [])
        last_message = current_tools[-1]
        tool_outputs = []

        for tool_call in last_message.tool_calls:
            tool = self.tools_map[tool_call["name"]]
            tool_output = await tool.ainvoke(tool_call["args"])
            # Create a ToolMessage
            tool_outputs.append(str(tool_output))
        return {"recipes":  tool_outputs}

    async def writer(self,state:State):
        """
        Subagent that plans recipe creation
        """
        messages = [SystemMessage(content=self.writer_prompt)] + state["messages"]

        response = await self.base_llm.ainvoke(messages)
        message = AIMessage(content=response.content)
        return {
            "messages": state["messages"] + [message],
            "recipe_query": None,
            "technique_query": None,
            "recipes": None,
            "techniques": None,
            "tool_calls": None,
        }
