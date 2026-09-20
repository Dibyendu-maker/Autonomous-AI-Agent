"""Configurable web search tool supporting Tavily, DuckDuckGo, and Mock providers."""
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from app.config import settings

logger = logging.getLogger(__name__)


class SearchResultItem(BaseModel):
    title: str = Field(description="Title of the search result")
    url: str = Field(description="URL link of the source")
    content: str = Field(description="Snippet or content excerpt")


class SearchResponse(BaseModel):
    query: str
    provider: str
    results: List[SearchResultItem] = Field(default_factory=list)


def search_web(query: str, max_results: Optional[int] = None) -> SearchResponse:
    """Execute a web search using the configured provider (Tavily, DuckDuckGo, or Mock)."""
    provider = settings.SEARCH_PROVIDER.lower().strip()
    limit = max_results or settings.MAX_SEARCH_RESULTS

    if provider == "tavily":
        if not settings.TAVILY_API_KEY:
            logger.warning("TAVILY_API_KEY is not set. Falling back to DuckDuckGo search.")
            return _search_duckduckgo(query, limit)
        return _search_tavily(query, limit)

    elif provider == "duckduckgo":
        return _search_duckduckgo(query, limit)

    elif provider == "mock":
        return _search_mock(query, limit)

    else:
        raise ValueError(
            f"Unsupported SEARCH_PROVIDER: '{provider}'. Supported: 'tavily', 'duckduckgo', 'mock'."
        )


def _search_tavily(query: str, max_results: int) -> SearchResponse:
    """Search the web using Tavily API."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"
        )
        
        items = []
        for res in response.get("results", []):
            items.append(
                SearchResultItem(
                    title=res.get("title", "Untitled"),
                    url=res.get("url", ""),
                    content=res.get("content", "")
                )
            )
        return SearchResponse(query=query, provider="tavily", results=items)
    except Exception as e:
        logger.error(f"Tavily search failed: {e}. Falling back to DuckDuckGo.")
        return _search_duckduckgo(query, max_results)


def _search_duckduckgo(query: str, max_results: int) -> SearchResponse:
    """Search using DuckDuckGo without requiring an API key."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
            for r in raw_results:
                results.append(
                    SearchResultItem(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        content=r.get("body", "")
                    )
                )
        return SearchResponse(query=query, provider="duckduckgo", results=results)
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}. Falling back to Mock search.")
        return _search_mock(query, max_results)


def _search_mock(query: str, max_results: int) -> SearchResponse:
    """Synthetic search responses for local testing and offline execution."""
    mock_items = [
        SearchResultItem(
            title=f"Industry Trends: Analysis of {query}",
            url=f"https://example.com/reports/{query.replace(' ', '-').lower()}",
            content=f"Comprehensive market breakdown regarding {query}. Highlights shifting talent demands, increased automation, and agentic workflows."
        ),
        SearchResultItem(
            title=f"Statistical Brief & Benchmarks for {query}",
            url=f"https://example.org/stats/{query.replace(' ', '-').lower()}",
            content=f"Recent enterprise survey reveals a 45% increase in production agent deployments and rapid integration of multimodal capabilities."
        ),
        SearchResultItem(
            title=f"Key Challenges and Best Practices: {query}",
            url=f"https://example.net/best-practices",
            content=f"Leading engineering teams cite verification, guardrails, and deterministic state management as the foremost priorities for {query}."
        ),
    ]
    return SearchResponse(query=query, provider="mock", results=mock_items[:max_results])
