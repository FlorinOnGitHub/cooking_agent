# Cooking Agent V1.3


An intelligent culinary assistant powered by LangGraph and DuckDuckGo Search.

Unlike standard chatbots that hallucinate recipes, this agent performs recipe retrieval real-time web scraping to find authentic recipes and cooking techniques. It is built with MCP architecture for easy interoperability


This is just the beginning of my personal project where I will learn how to build AI Agents and experiment with LLMs. Currently, the agent is limited in tool use, I will add more as I get more ideas.


For this third iteration, I implemented the agentic logic in LangGraph and added a Vector Database of cookbooks I found online.

In the next iteration, I will deploy the agent to cloud alognside proper session management for multiple users.

## Features

**Agentic Workflow**: Main Agent that takes decisions based on gathered data.

**Real-Time Web Scraping**: Fetches live data using DuckDuckGo and Trafilatura (no stale data).

**Vector Database**: Chroma DB

**Chunking**: Documents are chunked either based on headers or pages, according to their structure (cooking books have some structure that can be taken advantage of)

**Smart Filtering**: Automatically strips ads, blog fluff, and SEO narratives from recipe sites.

**Technique Research**: Can research "food science" questions (e.g., Why is my steak tough?) separately from recipe ingredients.

**Grounded Generation**: Forces the LLM to use scraped data for generation to reduce hallucinations.

## Tech Stack

**LLM**: Google Gemini 2.5 Flash

**MCP Server**: FastMCP

**Search** DuckDuckGo Search (duckduckgo_search)

**Vector Database**: ChromaDB

**Scraping**: Trafilatura & Requests

**Environment**: Python 3.13

**Markdown** Rendering: Rich

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

