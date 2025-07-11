#!/usr/bin/env python3
"""
ArXiv MCP Server - A demonstration server for the MCP 101 presentation.

This server provides access to the ArXiv API through the Model Context Protocol,
demonstrating Tools, Resources, and progress notifications.
"""

import asyncio
import arxiv
from typing import List, Optional
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, EmbeddedResource

# Initialize the MCP server
mcp = FastMCP("ArXiv Research Server")

class Paper(BaseModel):
    """Data model for an ArXiv paper"""
    title: str
    authors: List[str]
    summary: str
    pdf_url: str
    paper_id: str
    published: str

class SearchResult(BaseModel):
    """Search results with metadata"""
    papers: List[Paper]
    query: str
    total_results: int

@mcp.tool()
def search_papers(query: str, max_results: int = 5) -> SearchResult:
    """
    Search the ArXiv database for scientific papers matching the query.
    
    Args:
        query: Search terms (e.g., "transformer models", "quantum computing")
        max_results: Maximum number of papers to return (default: 5, max: 20)
        
    Returns:
        SearchResult containing papers and metadata
    """
    # Limit max_results to prevent abuse
    max_results = min(max_results, 20)
    
    # Create ArXiv search
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    papers = []
    for result in search.results():
        paper = Paper(
            title=result.title.strip(),
            authors=[author.name for author in result.authors],
            summary=result.summary.replace('\n', ' ').strip(),
            pdf_url=result.pdf_url,
            paper_id=result.entry_id.split('/')[-1],  # Extract ID from URL
            published=result.published.strftime('%Y-%m-%d')
        )
        papers.append(paper)
    
    return SearchResult(
        papers=papers,
        query=query,
        total_results=len(papers)
    )

@mcp.tool()
async def download_paper_collection(query: str, max_papers: int = 10) -> dict:
    """
    Download multiple papers based on a search query with progress tracking.
    
    This demonstrates MCP's progress notification system for long-running operations.
    
    Args:
        query: Search terms for papers to download
        max_papers: Maximum number of papers to download
        
    Returns:
        Dictionary with download results and file paths
    """
    import os
    from pathlib import Path
    
    # Create download directory
    download_dir = Path("./downloads")
    download_dir.mkdir(exist_ok=True)
    
    # Search for papers
    search = arxiv.Search(query=query, max_results=max_papers)
    papers = list(search.results())
    
    downloaded_files = []
    
    for i, paper in enumerate(papers):
        # Send progress notification
        await mcp.request_context.session.send_progress_notification(
            progress=i + 1,
            total=len(papers),
            message=f"Downloading: {paper.title[:50]}..."
        )
        
        try:
            # Download the paper
            filename = f"{paper.entry_id.split('/')[-1]}.pdf"
            filepath = download_dir / filename
            paper.download_pdf(dirpath=str(download_dir), filename=filename)
            
            downloaded_files.append({
                "title": paper.title,
                "file_path": str(filepath),
                "paper_id": paper.entry_id.split('/')[-1]
            })
            
            # Simulate processing time
            await asyncio.sleep(0.5)
            
        except Exception as e:
            # Log error but continue with other papers
            await mcp.request_context.session.send_log_message(
                level="warning",
                data={"error": str(e), "paper_id": paper.entry_id}
            )
    
    return {
        "query": query,
        "total_papers": len(papers),
        "downloaded_count": len(downloaded_files),
        "files": downloaded_files
    }

@mcp.resource("arxiv/{paper_id}")
async def get_paper_details(paper_id: str) -> str:
    """
    Get detailed information about a specific ArXiv paper.
    
    Args:
        paper_id: ArXiv paper ID (e.g., "2301.07041")
        
    Returns:
        Detailed paper information as text
    """
    try:
        # Search for the specific paper
        search = arxiv.Search(id_list=[paper_id])
        paper = next(search.results())
        
        details = f"""
Title: {paper.title}

Authors: {', '.join([author.name for author in paper.authors])}

Published: {paper.published.strftime('%Y-%m-%d')}

Abstract:
{paper.summary}

Categories: {', '.join(paper.categories)}

PDF URL: {paper.pdf_url}

ArXiv URL: {paper.entry_id}
        """.strip()
        
        return details
        
    except Exception as e:
        return f"Error retrieving paper {paper_id}: {str(e)}"

@mcp.resource("arxiv/{paper_id}/abstract")
async def get_abstract(paper_id: str) -> str:
    """
    Get just the abstract of a specific ArXiv paper.
    
    Args:
        paper_id: ArXiv paper ID
        
    Returns:
        Paper abstract text
    """
    try:
        search = arxiv.Search(id_list=[paper_id])
        paper = next(search.results())
        return paper.summary.replace('\n', ' ').strip()
    except Exception as e:
        return f"Error retrieving abstract for {paper_id}: {str(e)}"

@mcp.prompt("analyze_paper")
async def analyze_paper_prompt() -> str:
    """
    Prompt template for deep paper analysis workflow.
    
    This demonstrates MCP's prompt system for encapsulating best practices.
    """
    return """
You are an AI research assistant. Follow this workflow to analyze a research paper:

1. First, ask the user for an ArXiv paper ID or search query
2. If given a search query, use search_papers() to find relevant papers
3. Use get_paper_details() to retrieve the full paper information
4. Analyze the paper considering:
   - Research contribution and novelty
   - Methodology and experimental design
   - Results and their significance
   - Limitations and future work
   - Relevance to current research trends

5. Provide a structured summary including:
   - One-sentence summary
   - Key contributions (3-5 bullet points)
   - Methodology overview
   - Critical assessment
   - Related work suggestions

Please be thorough but concise in your analysis.
    """.strip()

if __name__ == "__main__":
    # Run the server
    mcp.run(
        transport="stdio",  # Use stdio for local development
        # transport="streamable-http",  # Use HTTP for remote access
        # port=8002
    )