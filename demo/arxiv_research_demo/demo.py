#!/usr/bin/env python3
"""
ArXiv Research Demo - Combined demo that:
1. Searches ArXiv for relevant papers
2. Extracts key information from them
3. Creates a GitHub gist with the extracted information using OAuth

Usage:
    uv run demo.py --query "quantum computing" --max-papers 3
"""

import asyncio
from typing import List, Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from arxiv_research_demo.arxiv_search import ArxivSearcher
from arxiv_research_demo.extractor import InformationExtractor
from arxiv_research_demo.github_gist import GitHubGistCreator
from arxiv_research_demo.models import Paper, ExtractedInfo, GistInfo

# Load environment variables
load_dotenv()

console = Console()
app = typer.Typer(help="ArXiv Research Demo with GitHub Gist integration")


@app.command()
def run_command(
    query: str = typer.Argument(..., help="Search query for ArXiv papers"),
    max_papers: int = typer.Option(5, help="Maximum number of papers to analyze"),
    skip_auth: bool = typer.Option(False, help="Skip GitHub authentication (for testing)"),
    dry_run: bool = typer.Option(False, help="Don't create gist, just show extracted info")
):
    """
    Search ArXiv, extract key information, and create a GitHub gist.
    """
    asyncio.run(run_demo(query, max_papers, skip_auth, dry_run))

def main():
    """Entry point for the CLI."""
    app()


async def run_demo(query: str, max_papers: int, skip_auth: bool, dry_run: bool):
    """Run the complete demo workflow."""
    console.print("🚀 Starting ArXiv Research Demo")
    console.print(f"📋 Query: [bold]{query}[/bold]")
    console.print(f"📊 Max papers: {max_papers}")
    console.print()
    
    # Initialize components
    searcher = ArxivSearcher()
    extractor = InformationExtractor()
    gist_creator = GitHubGistCreator()
    
    try:
        # Step 1: Search for papers
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Searching ArXiv...", total=None)
            papers = searcher.search_papers(query, max_papers)
            progress.update(task, completed=True)
        
        if not papers:
            console.print("❌ No papers found for the given query.")
            return
        
        # Display found papers
        display_papers(papers)
        
        # Step 2: Extract information from papers
        extracted_info: List[ExtractedInfo] = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting information...", total=len(papers))
            
            for paper in papers:
                info = extractor.extract_info(paper)
                extracted_info.append(info)
                progress.update(task, advance=1)
        
        # Display extracted information
        display_extracted_info(extracted_info)
        
        if dry_run:
            console.print("🏁 Dry run completed - no gist created")
            return
        
        # Step 3: Create GitHub gist
        if not skip_auth:
            # Authenticate with GitHub
            auth_success = await gist_creator.authenticate()
            if not auth_success:
                console.print("❌ Authentication failed. Exiting.")
                return
            
            # Create gist
            gist_info = await gist_creator.create_gist(extracted_info, query)
            if gist_info:
                display_gist_info(gist_info)
            else:
                console.print("❌ Failed to create gist")
        else:
            console.print("⏭️  Skipping GitHub authentication")
        
        console.print("🎉 Demo completed successfully!")
        
    except Exception as e:
        console.print(f"❌ Error during demo: {str(e)}")
        raise


def display_papers(papers: List[Paper]):
    """Display found papers in a table."""
    console.print("\n📄 Found Papers:")
    
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("ID", style="cyan", width=12)
    table.add_column("Title", style="green", width=50)
    table.add_column("Authors", style="yellow", width=25)
    table.add_column("Published", style="magenta", width=12)
    
    for paper in papers:
        authors_str = ", ".join(paper.authors[:2])  # Show first 2 authors
        if len(paper.authors) > 2:
            authors_str += f" +{len(paper.authors) - 2} more"
        
        table.add_row(
            paper.paper_id,
            paper.title[:47] + "..." if len(paper.title) > 50 else paper.title,
            authors_str,
            paper.published
        )
    
    console.print(table)


def display_extracted_info(extracted_info: List[ExtractedInfo]):
    """Display extracted information."""
    console.print("\n🔍 Extracted Information:")
    
    for i, info in enumerate(extracted_info, 1):
        console.print(f"\n[bold blue]{i}. {info.title}[/bold blue]")
        console.print(f"   ArXiv ID: {info.paper_id}")
        
        if info.key_findings:
            console.print("   [bold green]Key Findings:[/bold green]")
            for finding in info.key_findings:
                console.print(f"   • {finding}")
        
        console.print(f"   [bold yellow]Methodology:[/bold yellow] {info.methodology}")
        
        if info.datasets_used:
            console.print(f"   [bold cyan]Datasets:[/bold cyan] {', '.join(info.datasets_used)}")
        
        if info.limitations:
            console.print("   [bold red]Limitations:[/bold red]")
            for limitation in info.limitations:
                console.print(f"   • {limitation}")


def display_gist_info(gist_info: GistInfo):
    """Display gist creation information."""
    console.print("\n📝 GitHub Gist Created:")
    console.print(f"   [bold green]Gist ID:[/bold green] {gist_info.gist_id}")
    console.print(f"   [bold blue]URL:[/bold blue] {gist_info.gist_url}")
    console.print(f"   [bold yellow]Filename:[/bold yellow] {gist_info.filename}")
    console.print(f"   [bold magenta]Created:[/bold magenta] {gist_info.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    app()
