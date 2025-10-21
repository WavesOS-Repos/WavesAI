#!/usr/bin/env python3
"""
WavesAI Search Engine Module
Handles Wikipedia and DuckDuckGo web searches
"""

import requests
import re
from html import unescape
from typing import Optional
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
import time
import hashlib

class SearchEngine:
    """Handles all search operations for WavesAI"""
    
    def __init__(self):
        self.user_agent = 'WavesAI/1.0 (https://github.com/wavesai/wavesai)'
        self.browser_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        # Caching system (5 minute cache)
        self.cache = {}
        self.cache_duration = 300  # 5 minutes in seconds
    
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
    
    def _get_cache_key(self, prefix: str, query: str) -> str:
        """Generate cache key"""
        return f"{prefix}:{hashlib.md5(query.encode()).hexdigest()}"
    
    def _get_cached(self, cache_key: str):
        """Get cached data if still valid"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def _set_cache(self, cache_key: str, data):
        """Set cache data"""
        self.cache[cache_key] = (data, time.time())
    
    def _fetch_google_news_rss(self, query: str = "india", language: str = "en") -> list:
        """Fetch news from Google News RSS (Free, No API key, Unlimited)"""
        try:
            # Check cache first
            cache_key = self._get_cache_key("google_news", query)
            cached = self._get_cached(cache_key)
            if cached:
                return cached
            
            url = f"https://news.google.com/rss/search?q={query}&hl={language}&gl=IN&ceid=IN:en"
            response = requests.get(url, headers={'User-Agent': self.browser_agent}, timeout=10)
            
            root = ET.fromstring(response.content)
            articles = []
            
            for item in root.findall('.//item')[:10]:
                title = item.find('title').text if item.find('title') is not None else ''
                description = item.find('description').text if item.find('description') is not None else ''
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                
                # Clean HTML from description
                if description:
                    description = re.sub(r'<[^>]+>', '', description)
                    description = unescape(description)
                
                articles.append({
                    'title': title,
                    'description': description[:200] + "..." if len(description) > 200 else description,
                    'date': pub_date,
                    'source': 'Google News'
                })
            
            # Cache the results
            self._set_cache(cache_key, articles)
            return articles
        except:
            return []
    
    def _fetch_reddit_trending(self, subreddit: str = 'worldnews') -> list:
        """Fetch trending from Reddit (Free, No login, Unlimited)"""
        try:
            # Check cache first
            cache_key = self._get_cache_key("reddit", subreddit)
            cached = self._get_cached(cache_key)
            if cached:
                return cached
            
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
            headers = {'User-Agent': self.browser_agent}
            response = requests.get(url, headers=headers, timeout=10)
            
            data = response.json()
            articles = []
            
            for post in data.get('data', {}).get('children', [])[:10]:
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                score = post_data.get('score', 0)
                
                articles.append({
                    'title': title,
                    'description': selftext[:200] + "..." if len(selftext) > 200 else selftext,
                    'score': score,
                    'source': f'Reddit r/{subreddit}'
                })
            
            # Cache the results
            self._set_cache(cache_key, articles)
            return articles
        except:
            return []
    
    def _fetch_hackernews(self) -> list:
        """Fetch top stories from HackerNews (Free, No login, Unlimited)"""
        try:
            # Check cache first
            cache_key = self._get_cache_key("hackernews", "top")
            cached = self._get_cached(cache_key)
            if cached:
                return cached
            
            # Get top story IDs
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(url, timeout=10)
            story_ids = response.json()[:10]
            
            articles = []
            for story_id in story_ids:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                story_response = requests.get(story_url, timeout=5)
                story = story_response.json()
                
                if story:
                    articles.append({
                        'title': story.get('title', ''),
                        'description': story.get('text', '')[:200] if story.get('text') else '',
                        'score': story.get('score', 0),
                        'source': 'HackerNews'
                    })
            
            # Cache the results
            self._set_cache(cache_key, articles)
            return articles
        except:
            return []
    
    def get_enhanced_news(self, query: str = "india", region: str = "india") -> str:
        """Get news from multiple free sources"""
        try:
            all_articles = []
            
            # Get from Google News RSS (best coverage)
            google_articles = self._fetch_google_news_rss(query)
            all_articles.extend(google_articles)
            
            # Get from Reddit for trending discussions
            if region.lower() in ["india", "indian"]:
                reddit_articles = self._fetch_reddit_trending('india')
            elif region.lower() in ["world", "global"]:
                reddit_articles = self._fetch_reddit_trending('worldnews')
            elif region.lower() in ["tech", "technology"]:
                reddit_articles = self._fetch_reddit_trending('technology')
                # Also get HackerNews for tech
                hn_articles = self._fetch_hackernews()
                all_articles.extend(hn_articles)
            else:
                reddit_articles = self._fetch_reddit_trending('worldnews')
            
            all_articles.extend(reddit_articles)
            
            # Format results - LIMIT to 7 articles to fit context window
            if all_articles:
                formatted = f"**Enhanced News** (as of {datetime.now().strftime('%B %d, %Y')})\n\n"
                
                # Only include top 7 articles to avoid context window overflow
                for i, article in enumerate(all_articles[:7], 1):
                    formatted += f"{i}. **{article['title']}**\n"
                    if article.get('description'):
                        # Limit description to 150 chars to save tokens
                        desc = article['description'][:150]
                        formatted += f"   {desc}...\n" if len(article['description']) > 150 else f"   {desc}\n"
                    if article.get('score'):
                        formatted += f"   Score: {article['score']} | "
                    formatted += f"*Source: {article['source']}*\n\n"
                
                return formatted
            else:
                return "Unable to fetch news at the moment."
        except Exception as e:
            return f"News fetch error: {str(e)}"

    def search_news(self, query: str = "latest news", region: str = "india") -> str:
        """Fetch real-time news from multiple FREE sources (Google News, Reddit, HackerNews, etc.)"""
        try:
            # Use enhanced news with multiple free sources
            enhanced_results = self.get_enhanced_news(query, region)
            
            if enhanced_results and "Unable to fetch" not in enhanced_results:
                return enhanced_results
            
            # Fallback to direct scraping if enhanced fails
            news_results = []
            
            # Determine news source based on region
            if region.lower() in ["india", "indian"]:
                # Fetch from Indian news sources
                news_results.extend(self._fetch_ndtv_news())
                news_results.extend(self._fetch_times_of_india_news())
            elif region.lower() in ["world", "global", "international"]:
                # Fetch from international sources
                news_results.extend(self._fetch_bbc_news())
                news_results.extend(self._fetch_reuters_news())
            else:
                # Default to web search for specific topics
                return self.search_web(f"latest {region} news today")
            
            if news_results:
                # Format news articles - LIMIT to 7 to fit context window
                formatted_news = f"**Latest {region.title()} News** (as of {datetime.now().strftime('%B %d, %Y')})\n\n"
                
                # Only include top 7 articles to avoid context overflow
                for i, article in enumerate(news_results[:7], 1):
                    formatted_news += f"{i}. **{article['title']}**\n"
                    if article.get('description'):
                        # Limit description to 150 chars
                        desc = article['description'][:150]
                        formatted_news += f"   {desc}...\n" if len(article['description']) > 150 else f"   {desc}\n"
                    if article.get('source'):
                        formatted_news += f"   *Source: {article['source']}*\n"
                    formatted_news += "\n"
                
                return formatted_news
            else:
                return "Unable to fetch news at the moment. Please try again later or visit news websites directly."
                
        except Exception as e:
            return f"News fetch error: {str(e)}. Please visit news websites for latest updates."
