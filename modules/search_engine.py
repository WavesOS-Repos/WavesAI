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
                
                # Get page URL
                if data.get('content_urls', {}).get('desktop', {}).get('page'):
                    page_url = data['content_urls']['desktop']['page']
                    result_parts.append(f"*Source: [Wikipedia]({page_url})*")
                
                if result_parts:
                    return "\n\n".join(result_parts)
            
            # If direct page doesn't exist, try search
            return self.search_wikipedia_articles(query)
            
        except Exception as e:
            return f"Wikipedia search failed: {str(e)}"
    
    def search_wikipedia_articles(self, query: str) -> str:
        """Search for Wikipedia articles when direct page doesn't exist"""
        try:
            # Wikipedia search API
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': 3,
                'srprop': 'snippet|size'
            }
            
            headers = {'User-Agent': self.user_agent}
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                if data.get('query', {}).get('search'):
                    for article in data['query']['search'][:3]:
                        title = article.get('title', '')
                        snippet = article.get('snippet', '')
                        
                        # Clean up HTML entities in snippet
                        snippet = unescape(snippet)
                        snippet = snippet.replace('<span class="searchmatch">', '').replace('</span>', '')
                        
                        if title and snippet:
                            results.append(f"**{title}**\n{snippet}")
                
                if results:
                    return "**Wikipedia Search Results:**\n\n" + "\n\n".join(results)
            
            return "No Wikipedia articles found for that query."
            
        except Exception as e:
            return f"Wikipedia search failed: {str(e)}"
    
    def get_wikipedia_content(self, title: str) -> str:
        """Get full Wikipedia article content"""
        try:
            # Get page content
            content_url = f"https://en.wikipedia.org/api/rest_v1/page/html/{title.replace(' ', '_')}"
            headers = {'User-Agent': self.user_agent}
            response = requests.get(content_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Extract main content (simplified parsing)
                # Remove HTML tags but keep structure
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content).strip()
                content = unescape(content)
                
                # Get first few paragraphs (approximately 1000 characters)
                paragraphs = content.split('.')
                summary = ""
                for para in paragraphs:
                    if len(summary + para) < 1000:
                        summary += para + "."
                    else:
                        break
                
                return summary.strip() if summary else content[:1000] + "..."
            
            return "Could not retrieve Wikipedia content."
            
        except Exception as e:
            return f"Wikipedia content retrieval failed: {str(e)}"
    
    def search_web(self, query: str) -> str:
        """Enhanced web search using DuckDuckGo's full potential"""
        try:
            # Try DuckDuckGo Instant Answer API first with enhanced parameters
            api_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1&t=wavesai"
            api_response = requests.get(api_url, timeout=10)
            api_data = api_response.json()
            
            result_parts = []
            
            # Get instant answer/abstract
            if api_data.get('AbstractText'):
                abstract = api_data['AbstractText']
                abstract_source = api_data.get('AbstractSource', 'Wikipedia')
                result_parts.append(f"**{api_data.get('Abstract', 'Information')}:**\n{abstract}\n*Source: {abstract_source}*")
            
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
            
            # Get definitions from definitions array
            if api_data.get('Definitions'):
                definitions = []
                for def_item in api_data['Definitions'][:3]:
                    if isinstance(def_item, dict) and 'Definition' in def_item:
                        definitions.append(f"• {def_item['Definition']}")
                if definitions:
                    result_parts.append("**Definitions:**\n" + '\n'.join(definitions))
            
            # Get infobox data for biographical information
            if api_data.get('Infobox'):
                infobox = api_data['Infobox']
                if isinstance(infobox, dict):
                    infobox_info = []
                    for key, value in infobox.items():
                        if isinstance(value, str) and len(value) > 5:
                            infobox_info.append(f"• **{key.replace('_', ' ').title()}:** {value}")
                    if infobox_info:
                        result_parts.append("**Key Details:**\n" + '\n'.join(infobox_info[:8]))
            
            # If we have good results from API, return them
            if result_parts:
                return "\n\n".join(result_parts)
            
            # If API doesn't have enough info, try HTML search
            html_result = self.search_web_html(query)
            
            # If HTML search also fails, try to provide some basic info
            if ("couldn't extract" in html_result.lower() or 
                "couldn't find" in html_result.lower() or
                "no results were found" in html_result.lower()):
                
                # Try one more fallback: return basic API info even if minimal
                if api_data.get('AbstractText') or api_data.get('RelatedTopics'):
                    fallback_parts = []
                    if api_data.get('AbstractText'):
                        fallback_parts.append(f"**Basic Information:** {api_data['AbstractText']}")
                    if api_data.get('RelatedTopics'):
                        related = []
                        for topic in api_data['RelatedTopics'][:2]:
                            if isinstance(topic, dict) and 'Text' in topic:
                                related.append(f"• {topic['Text']}")
                        if related:
                            fallback_parts.append("**Related:**\n" + '\n'.join(related))
                    
                    if fallback_parts:
                        return "\n\n".join(fallback_parts) + "\n\n*Note: Limited information available.*"
            
            return html_result
            
        except Exception as e:
            return f"Search failed: {str(e)}. Please try again or check your internet connection, sir."
    
    def search_web_html(self, query: str) -> str:
        """Enhanced HTML search using DuckDuckGo for comprehensive results"""
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            headers = {'User-Agent': self.browser_agent}
            
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                results = []
                
                # Try DuckDuckGo's current HTML structure patterns
                result_patterns = [
                    r'<div class="result"[^>]*>(.*?)</div>',
                    r'<div class="web-result"[^>]*>(.*?)</div>',
                    r'<div class="result__body"[^>]*>(.*?)</div>',
                    r'<article[^>]*>(.*?)</article>',
                    r'<div class="result__snippet"[^>]*>(.*?)</div>'
                ]
                
                for pattern in result_patterns:
                    result_blocks = re.findall(pattern, content, re.DOTALL)
                    if result_blocks:
                        for block in result_blocks[:5]:
                            # Extract title
                            title_match = re.search(r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*>(.*?)</a>', block)
                            title = title_match.group(1) if title_match else ""
                            title = re.sub(r'<[^>]+>', '', title).strip()
                            
                            # Extract snippet
                            snippet_match = re.search(r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>', block)
                            if not snippet_match:
                                snippet_match = re.search(r'class="[^"]*snippet[^"]*"[^>]*>(.*?)</div>', block)
                            snippet = snippet_match.group(1) if snippet_match else ""
                            snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                            snippet = unescape(snippet)
                            
                            if title and snippet:
                                results.append(f"**{title}**\n{snippet}")
                        
                        if results:
                            break
                
                if results:
                    return "**Web Search Results:**\n\n" + "\n\n".join(results[:5])
                else:
                    return "Couldn't extract search results. The search page structure may have changed."
            
            return "Couldn't find any results for that query."
            
        except Exception as e:
            return f"HTML search failed: {str(e)}"
    
    def combined_search(self, query: str) -> tuple:
        """Perform both Wikipedia and web search, return both results"""
        wiki_results = self.search_wikipedia(query)
        web_results = self.search_web(query)
        return wiki_results, web_results
