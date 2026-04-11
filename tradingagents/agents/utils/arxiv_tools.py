from langchain_core.tools import tool
from typing import Annotated
import requests
import xml.etree.ElementTree as ET

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ARXIV_NS = "{http://www.w3.org/2005/Atom}"


def _query_arxiv(search_query: str, max_results: int) -> str:
    """Execute an arXiv API query and format results as a readable string."""
    params = {
        "search_query": search_query,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    try:
        resp = requests.get(ARXIV_API_URL, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return f"arXiv API request failed: {e}"

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        return f"Failed to parse arXiv response: {e}"

    entries = root.findall(f"{ARXIV_NS}entry")
    if not entries:
        return "No relevant arXiv papers found for the given query."

    results = []
    for entry in entries:
        title = (entry.findtext(f"{ARXIV_NS}title") or "").strip().replace("\n", " ")
        summary = (entry.findtext(f"{ARXIV_NS}summary") or "").strip().replace("\n", " ")
        if len(summary) > 500:
            summary = summary[:500] + "..."
        published = (entry.findtext(f"{ARXIV_NS}published") or "")[:10]
        id_elem = entry.find(f"{ARXIV_NS}id")
        link = id_elem.text.strip() if id_elem is not None else "N/A"
        authors = [
            (a.findtext(f"{ARXIV_NS}name") or "")
            for a in entry.findall(f"{ARXIV_NS}author")
        ]
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += f" et al. ({len(authors)} total)"

        results.append(
            f"**Title:** {title}\n"
            f"**Published:** {published}\n"
            f"**Authors:** {author_str}\n"
            f"**Abstract:** {summary}\n"
            f"**Link:** {link}"
        )

    return "\n\n---\n\n".join(results)


@tool
def get_arxiv_papers(
    query: Annotated[str, "Search query (e.g. company name, ticker, sector, or financial topic)"],
    max_results: Annotated[int, "Maximum number of papers to return"] = 5,
) -> str:
    """
    Search arXiv for recent academic papers relevant to a company, sector, or financial topic.
    Searches across all arXiv categories including computer science, economics, and finance.
    Useful for finding AI/ML research, quantitative methods, and company or sector-specific studies.

    Args:
        query: Search terms such as company name, ticker symbol, or financial topic
        max_results: Number of papers to retrieve (default 5)

    Returns:
        Formatted string with paper titles, authors, abstracts, and links
    """
    search_query = f"all:{query.replace(' ', '+')}"
    return _query_arxiv(search_query, max_results)


@tool
def get_arxiv_finance_papers(
    query: Annotated[str, "Financial or economic topic to search for"],
    max_results: Annotated[int, "Maximum number of papers to return"] = 5,
) -> str:
    """
    Search arXiv for recent quantitative finance and economics papers.
    Restricts results to q-fin (quantitative finance) and econ (economics) categories,
    which cover portfolio theory, risk management, market microstructure, asset pricing,
    econometrics, and macroeconomic research.

    Args:
        query: Financial or economic topic (e.g. "momentum factor", "interest rate risk", "market volatility")
        max_results: Number of papers to retrieve (default 5)

    Returns:
        Formatted string with paper titles, authors, abstracts, and links
    """
    search_query = f"(cat:q-fin+OR+cat:econ)+AND+all:{query.replace(' ', '+')}"
    return _query_arxiv(search_query, max_results)
