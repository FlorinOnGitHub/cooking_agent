from ddgs import DDGS
import requests
import trafilatura

def online_search(query,max_results = 10):
    '''
    Search using DuckDuckGo for the most relevant links related to the query
    Args:
        query: search text
        max_results: maximum number of websites to search for
    Returns:
        result: the formated result from the internet search
    '''
    results = DDGS().text(query, max_results=max_results)
    results = [j['href'] for j in results]
    result = _extract_text(results)
    return result

def _extract_text(links):
    '''
    Extracts the text from all the links.

    ArgsL:
        links: list of links to search and extract data from

    Returns:
        result: resulting data from the internet search
    '''
    result = ""
    i = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    for link in links:
        session = requests.Session()
        session.headers.update(headers)
        # Timeout is critical so the agent doesn't hang on slow sites
        try:
            response = session.get(link, timeout=10, allow_redirects=True)
            content = response.content
            response = trafilatura.extract(
                content,
                include_comments=False,
                include_tables=True,
                include_images=False,
                output_format='markdown'
            )
            if response is not None : # additional check for denied access to website
                i+=1
                result += f"Option {i}\n" + response + "\n"
        except Exception as e:
            continue

    if result == "":
        print("could not open any recipes")
        return "need new prompt"
    return result