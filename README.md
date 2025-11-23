# Cooking Agent


An intelligent culinary assistant powered by Google Gemini 2.5 Flash and DuckDuckGo Search.

Unlike standard chatbots that hallucinate recipes, this agent performs real-time web scraping to find authentic recipes and cooking techniques. It uses a Function Calling architecture to research methods before synthesizing a final "Master Recipe."

This is just the beginning of my personal project where I will learn how to build with AI Agents and experiment with LLMs.
In the next iteration, I will experiment with different design paradigms for agent architecture, and create a better front-end for the application(currently text-based).

## Features

Agentic Workflow: Uses a "Tool Use" loop to decide when to search and when to write.

Real-Time Web Scraping: Fetches live data using DuckDuckGo and Trafilatura (no stale data).

Smart Filtering: Automatically strips ads, blog fluff, and SEO narratives from recipe sites.

Technique Research: Can research "food science" questions (e.g., Why is my steak tough?) separately from recipe ingredients.

Grounded Generation: Forces the LLM to use scraped data for generation to reduce hallucinations.

## Tech Stack

LLM: Google Gemini (via google-genai SDK)

Search: DuckDuckGo Search (duckduckgo_search)

Scraping: Trafilatura & Requests

Environment: Python 3.13


▶️ Usage

Run the main agent loop:

python main.py


Example Interaction:

User: I have some leftover chicken and heavy cream. What can I make?

Agent: Searches web for "chicken heavy cream recipes"...

Agent: I found a great recipe for Creamy Garlic Chicken. Would you like the full recipe or just the shopping list?

