"""ArXiv search functionality."""

import arxiv
from typing import List
from rich.console import Console
from arxiv_research_demo.models import Paper

console = Console()


class ArxivSearcher:
    """Handles ArXiv paper search and retrieval."""
    
    def search_papers(self, query: str, max_results: int = 5) -> List[Paper]:
        """Search ArXiv for papers matching the query."""
        console.print(f"🔍 Searching ArXiv for: [bold]{query}[/bold]")
        
        # Create ArXiv search
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        papers = []
        for result in search.results():
            paper = Paper(
                title=result.title.strip(),
                authors=[author.name for author in result.authors],
                summary=result.summary.strip(),
                pdf_url=result.pdf_url,
                paper_id=result.get_short_id(),
                published=result.published.strftime("%Y-%m-%d"),
                categories=[cat for cat in result.categories],
                doi=result.doi
            )
            papers.append(paper)
        
        console.print(f"✅ Found {len(papers)} papers")
        return papers
