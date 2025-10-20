#!/usr/bin/env python3
"""
WavesAI Search Engine Module
Handles Wikipedia and DuckDuckGo web searches
"""

import requests
import re
from html import unescape
from typing import Optional


class SearchEngine:
    """Handles all search operations for WavesAI"""
    
    def __init__(self):
        self.user_agent = 'WavesAI/1.0 (https://github.com/wavesai/wavesai)'
        self.browser_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    def search_wikipedia(self, query: str) -> str:
        """Search Wikipedia for comprehensive information"""
        try:
            # Wikipedia API search
            search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(' ', '_')
            
            headers = {'User-Agent': self.user_agent}
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result_parts = []
                
                # Get title
                if data.get('title'):
                    result_parts.append(f"**{data['title']}**")
                
                # Get extract (summary)
                if data.get('extract'):
                    extract = data['extract']
                    result_parts.append(f"**Summary:**\n{extract}")
                
                # Get description
                if data.get('description'):
                    result_parts.append(f"**Description:** {data['description']}")
                
                # Get coordinates for places
                if data.get('coordinates'):
                    coords = data['coordinates']
                    result_parts.append(f"**Location:** {coords.get('lat', 'N/A')}°N, {coords.get('lon', 'N/A')}°E")
                
                if result_parts:
                    return "\n\n".join(result_parts)
            
            # If direct search fails, try search API
            search_api_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': 3
            }
            
            search_response = requests.get(search_api_url, params=search_params, headers=headers, timeout=10)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data.get('query', {}).get('search'):
                    results = []
                    for result in search_data['query']['search'][:3]:
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        # Clean HTML tags from snippet
                        snippet = re.sub(r'<[^>]+>', '', snippet)
                        snippet = unescape(snippet)
                        
                        if title and snippet:
                            results.append(f"**{title}**\n{snippet}")
                    
                    if results:
                        return "**Wikipedia Search Results:**\n\n" + "\n\n".join(results)
            
            return "No Wikipedia articles found for that query."
            
        except Exception as e:
            return f"Wikipedia search failed: {str(e)}"
    
    def search_news(self, query: str = "latest news", region: str = "world") -> str:
        """Simple news search using web search"""
        try:
            # Simple news query construction
            if region.lower() == "world":
                news_query = f"latest world news today"
            else:
                news_query = f"latest {region} news today"
            
            # Just do a simple web search
            return self.search_web(news_query)
            
        except Exception as e:
            return f"Unable to fetch news at the moment. Please try again later."
    
    
    def search_web(self, query: str) -> str:
        """Enhanced web search using DuckDuckGo's full potential"""
        try:
            # Try DuckDuckGo Instant Answer API first
            api_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1&t=wavesai"
            api_response = requests.get(api_url, timeout=10)
            api_data = api_response.json()
            
            result_parts = []
            
            # Get instant answer/abstract
            if api_data.get('AbstractText'):
                abstract = api_data['AbstractText']
                abstract_source = api_data.get('AbstractSource', 'Wikipedia')
                result_parts.append(f"**Information:**\n{abstract}\n*Source: {abstract_source}*")
            
            # Get definition if available
            if api_data.get('Definition'):
                result_parts.append(f"**Definition:** {api_data['Definition']}")
            
            # Get answer (for direct questions)
            if api_data.get('Answer'):
                result_parts.append(f"**Answer:** {api_data['Answer']}")
            
            # Get related topics
            if api_data.get('RelatedTopics'):
                related_info = []
                for topic in api_data['RelatedTopics'][:5]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        related_info.append(f"• {topic['Text']}")
                if related_info:
                    result_parts.append("**Related Information:**\n" + '\n'.join(related_info))
            
            # If we have good results from API, return them
            if result_parts:
                return "\n\n".join(result_parts)
            
            # If no API results, provide helpful fallback
            return self.search_web_fallback(query)
            
        except Exception as e:
            return f"Search failed: {str(e)}"
    
    def search_web_fallback(self, query: str) -> str:
        """Provide helpful fallback when web search fails"""
        # For news queries, provide simple response
        if any(keyword in query.lower() for keyword in ['news', 'latest', 'breaking', 'current']):
            return "Unable to fetch live news at the moment. Please visit news websites like BBC, Reuters, or CNN for the latest updates."
        
        # For other queries, provide helpful alternatives
        return f"""**Web Search Information**

I'm currently unable to fetch live web results due to technical limitations.

**Suggested alternatives for '{query}':**
• Use your browser: `open firefox` then search for "{query}"
• Try Wikipedia search for factual information
• Use specific commands like `weather` for weather info
• Ask me to open relevant websites

**Quick commands:**
• `open firefox` - Open web browser
• `weather [location]` - Get weather info

Would you like me to help you with any of these alternatives?"""
