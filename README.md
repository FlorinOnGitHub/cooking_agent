# Cooking Agent V1.2


An intelligent culinary assistant powered by Google Gemini 2.5 Flash and DuckDuckGo Search.

Unlike standard chatbots that hallucinate recipes, this agent performs real-time web scraping to find authentic recipes and cooking techniques. It is built with MCP architecture for easy interoperability


This is just the beginning of my personal project where I will learn how to build AI Agents and experiment with LLMs. Currently, the agent is limited in tool use, I will add more as I get more ideas.


For this second iteration, i have switch the architecture from FunctionCalling to MCP, as I find it an important next step in my learning process.
 
In the next iteration, I will switch the framework to LangGraph to allow for other types of models(currently only Gemini Is supported) and to learn the framework. A better front-end for the application(currently text-based) is still needed. 

## Features

Agentic Workflow: MCP architecture

Real-Time Web Scraping: Fetches live data using DuckDuckGo and Trafilatura (no stale data).

Smart Filtering: Automatically strips ads, blog fluff, and SEO narratives from recipe sites.

Technique Research: Can research "food science" questions (e.g., Why is my steak tough?) separately from recipe ingredients.

Grounded Generation: Forces the LLM to use scraped data for generation to reduce hallucinations.

## Tech Stack

LLM: Google Gemini (via Google ADK)

MCP Server: FastMCP

Search: DuckDuckGo Search (duckduckgo_search)

Scraping: Trafilatura & Requests

Environment: Python 3.13

Markdown Rendering: Rich

▶️ Usage

1. First run the server:

```
python server.py
```

2. In a separate terminal, run the main agent loop:

```
python main.py
```

Now all that is left is to get cooking!
Eet Smakelijk!

