"""
Scraping Agent - Lightweight web scraping for the autonomous agent
Uses httpx + BeautifulSoup for static pages, falls back to Playwright for JS-heavy sites
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger('NeuroSurf.ScrapingAgent')


class ScrapingAgent:
    """
    Lightweight web scraper for the autonomous agent
    Supports:
    - Static HTML scraping with CSS selectors
    - Link extraction and crawling
    - Text content extraction
    - Structured data extraction
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize scraping agent
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with realistic headers"""
        if self._client is None or self._client.is_closed:
            # Use a more modern and consistent User-Agent
            self.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Upgrade-Insecure-Requests': '1'
            })
            self._client = httpx.AsyncClient(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def fetch_page(self, url: str) -> Dict[str, Any]:
        """
        Fetch a web page
        
        Args:
            url: URL to fetch
            
        Returns:
            Page content and metadata
        """
        logger.info(f"🌐 Fetching: {url}")
        
        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()
            
            return {
                "url": str(response.url),
                "status": response.status_code,
                "content_type": response.headers.get('content-type', ''),
                "html": response.text,
                "success": True
            }
        except httpx.HTTPStatusError as e:
            return {
                "url": url,
                "status": e.response.status_code,
                "error": f"HTTP {e.response.status_code}",
                "success": False
            }
        except Exception as e:
            logger.error(f"Fetch failed: {e}")
            return {
                "url": url,
                "error": str(e),
                "success": False
            }
    
    async def scrape(
        self,
        url: str,
        selectors: Optional[Dict[str, str]] = None,
        extract_links: bool = False,
        extract_text: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape a web page with optional CSS selectors
        
        Args:
            url: URL to scrape
            selectors: Dict of {name: css_selector} to extract specific elements
            extract_links: Whether to extract all links
            extract_text: Whether to extract main text content
            
        Returns:
            Scraped data
        """
        page = await self.fetch_page(url)
        
        if not page.get("success"):
            return page
        
        soup = BeautifulSoup(page["html"], "lxml")
        result = {
            "url": page["url"],
            "title": soup.title.string if soup.title else "",
            "success": True
        }
        
        # Extract specific elements with selectors
        if selectors:
            result["data"] = {}
            for name, selector in selectors.items():
                try:
                    elements = soup.select(selector)
                    if elements:
                        if len(elements) == 1:
                            result["data"][name] = elements[0].get_text(strip=True)
                        else:
                            result["data"][name] = [el.get_text(strip=True) for el in elements]
                except Exception as e:
                    result["data"][name] = f"Error: {e}"
        
        # Extract main text content
        if extract_text:
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            # Clean up excessive whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            result["text"] = text[:10000]  # Limit text size
        
        # Extract all links
        if extract_links:
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('#'):
                    continue
                full_url = urljoin(url, href)
                if urlparse(full_url).scheme in ('http', 'https'):
                    links.append({
                        "url": full_url,
                        "text": a.get_text(strip=True)[:100]
                    })
            result["links"] = links[:50]  # Limit links
        
        return result
    
    async def scrape_multiple(
        self,
        urls: List[str],
        selectors: Optional[Dict[str, str]] = None,
        concurrency: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs concurrently
        
        Args:
            urls: List of URLs to scrape
            selectors: CSS selectors to apply to all pages
            concurrency: Max concurrent requests
            
        Returns:
            List of scraped results
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def scrape_with_limit(url):
            async with semaphore:
                return await self.scrape(url, selectors)
        
        tasks = [scrape_with_limit(url) for url in urls]
        return await asyncio.gather(*tasks)
    
    async def extract_structured_data(
        self,
        url: str,
        schema: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extract structured data from a page using a schema
        
        Args:
            url: URL to scrape
            schema: Dict mapping field names to CSS selectors
            
        Returns:
            Extracted data matching schema
        """
        return await self.scrape(url, selectors=schema, extract_text=False)
    
    async def get_headlines(self, url: str) -> List[str]:
        """
        Extract headlines (h1, h2, h3) from a page
        
        Args:
            url: URL to scrape
            
        Returns:
            List of headlines
        """
        page = await self.fetch_page(url)
        if not page.get("success"):
            return []
        
        soup = BeautifulSoup(page["html"], "lxml")
        headlines = []
        
        for tag in ['h1', 'h2', 'h3']:
            for h in soup.find_all(tag):
                text = h.get_text(strip=True)
                if text and len(text) > 5:
                    headlines.append(text)
        
        return headlines[:20]  # Limit to 20 headlines

    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform a web search trying multiple backends
        """
        logger.info(f"🔍 Searching: {query}")
        
        # Try 1: DuckDuckGo Search Library
        try:
            from duckduckgo_search import DDGS
            results = []
            # Newer version doesn't always need context manager, but we'll try both
            with DDGS(timeout=20) as ddgs:
                for r in ddgs.text(query, max_results=num_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href") or r.get("link") or r.get("url", ""),
                        "snippet": r.get("body") or r.get("snippet", "")
                    })
            if results:
                logger.info(f"🔍 DDGS found {len(results)} results")
                return results
        except Exception as e:
            logger.warning(f"DDGS error: {e}")

        # Try 2: Bing Fallback (Often less aggressive blocking than Google/DDG)
        try:
            bing_results = await self._search_bing_fallback(query, num_results)
            if bing_results:
                logger.info(f"🔍 Bing fallback found {len(bing_results)} results")
                return bing_results
        except Exception as e:
            logger.warning(f"Bing fallback error: {e}")

        # Try 3: DuckDuckGo Lite Fallback (Highly resilient)
        try:
            ddg_lite_results = await self._search_ddg_lite_fallback(query, num_results)
            if ddg_lite_results:
                logger.info(f"🔍 DDG Lite fallback found {len(ddg_lite_results)} results")
                return ddg_lite_results
        except Exception as e:
            logger.warning(f"DDG Lite fallback error: {e}")

        # Try 4: DuckDuckGo HTML Fallback
        return await self._search_html_fallback(query, num_results)
    
    async def _search_ddg_lite_fallback(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Fallback search using DuckDuckGo Lite (no JS, very stable)"""
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"
        
        page = await self.fetch_page(url)
        if not page.get("success"):
            return []
            
        soup = BeautifulSoup(page["html"], "lxml")
        results = []
        
        # DDG Lite results are in tables
        for i, row in enumerate(soup.select("tr")):
            # Look for rows that look like results (usually have a result-link class)
            link = row.select_one("a.result-link")
            snippet = row.find_next_sibling("tr").select_one("td.result-snippet") if row.find_next_sibling("tr") else None
            
            if link and link.get("href"):
                results.append({
                    "title": link.get_text(strip=True),
                    "url": link["href"],
                    "snippet": snippet.get_text(strip=True) if snippet else ""
                })
                if len(results) >= num_results:
                    break
        
        return results

    async def _search_bing_fallback(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Fallback search using Bing with multiple selector support"""
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.bing.com/search?q={encoded_query}"
        
        page = await self.fetch_page(url)
        if not page.get("success"):
            return []
            
        soup = BeautifulSoup(page["html"], "lxml")
        results = []
        
        # Bing organic results li.b_algo, but also check other common patterns
        items = soup.select(".b_algo") or soup.select(".b_result") or soup.select("li[data-bm]")
        
        for i, item in enumerate(items):
            if len(results) >= num_results:
                break
                
            title_el = item.select_one("h2 a") or item.select_one("a")
            snippet_el = item.select_one(".b_caption p") or item.select_one(".b_line_clamp") or item.select_one(".content p")
            
            if title_el and title_el.get("href") and title_el["href"].startswith("http"):
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": title_el["href"],
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else ""
                })
        
        return results

    async def _search_html_fallback(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Fallback HTML-based search if duckduckgo_search library fails"""
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        page = await self.fetch_page(search_url)
        if not page.get("success"):
            return []
            
        soup = BeautifulSoup(page["html"], "lxml")
        results = []
        
        for i, result in enumerate(soup.select(".result")):
            if i >= num_results:
                break
                
            title_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")
            
            if title_el and snippet_el:
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": title_el["href"],
                    "snippet": snippet_el.get_text(strip=True)
                })
                
        return results


# Singleton instance
_scraping_agent: Optional[ScrapingAgent] = None


def get_scraping_agent() -> ScrapingAgent:
    """Get or create singleton scraping agent"""
    global _scraping_agent
    if _scraping_agent is None:
        _scraping_agent = ScrapingAgent()
    return _scraping_agent
