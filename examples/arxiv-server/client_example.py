#!/usr/bin/env python3
"""
Example MCP client demonstrating how to connect to and use the ArXiv MCP server.

This script shows how to:
1. Connect to an MCP server
2. List available capabilities 
3. Call tools and access resources
4. Handle responses and errors

Run this alongside the ArXiv server to see MCP in action!
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("❌ MCP client libraries not found. Install with: uv add mcp")
    sys.exit(1)


class ArXivMCPClient:
    """Example client for the ArXiv MCP server."""
    
    def __init__(self):
        self.session = None
    
    async def connect(self):
        """Connect to the ArXiv MCP server."""
        print("🔌 Connecting to ArXiv MCP server...")
        
        # Start the server process
        server_params = StdioServerParameters(
            command="python",
            args=["server.py"],
            env=None
        )
        
        # Create client session
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                
                # Initialize the connection
                await session.initialize()
                print("✅ Connected successfully!")
                
                # Run the demo
                await self.run_demo()
    
    async def run_demo(self):
        """Run a demonstration of the ArXiv server capabilities."""
        print("\n🚀 Starting ArXiv MCP Server Demo")
        print("=" * 50)
        
        # 1. List server capabilities
        await self.list_capabilities()
        
        # 2. Search for papers
        await self.search_papers_demo()
        
        # 3. Get paper details
        await self.get_paper_details_demo()
        
        # 4. Try the analysis prompt
        await self.analysis_prompt_demo()
        
        print("\n🎉 Demo completed!")
    
    async def list_capabilities(self):
        """List all available tools, resources, and prompts."""
        print("\n📋 Server Capabilities:")
        print("-" * 30)
        
        # List tools
        tools = await self.session.list_tools()
        print(f"🔧 Tools ({len(tools.tools)}):")
        for tool in tools.tools:
            print(f"  • {tool.name}: {tool.description}")
        
        # List resources
        try:
            resources = await self.session.list_resources()
            print(f"\n📄 Resources ({len(resources.resources)}):")
            for resource in resources.resources:
                print(f"  • {resource.uri}: {resource.name}")
        except Exception as e:
            print(f"\n📄 Resources: Unable to list ({e})")
        
        # List prompts
        try:
            prompts = await self.session.list_prompts()
            print(f"\n📝 Prompts ({len(prompts.prompts)}):")
            for prompt in prompts.prompts:
                print(f"  • {prompt.name}: {prompt.description}")
        except Exception as e:
            print(f"\n📝 Prompts: Unable to list ({e})")
    
    async def search_papers_demo(self):
        """Demonstrate paper search functionality."""
        print("\n🔍 Searching for papers on 'quantum computing'...")
        print("-" * 40)
        
        try:
            result = await self.session.call_tool(
                "search_papers",
                {
                    "query": "quantum computing",
                    "max_results": 3
                }
            )
            
            if result.content:
                papers_data = json.loads(result.content[0].text)
                print(f"Found {papers_data['total_results']} papers:")
                
                for i, paper in enumerate(papers_data['papers'], 1):
                    print(f"\n{i}. {paper['title']}")
                    print(f"   Authors: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
                    print(f"   Published: {paper['published']}")
                    print(f"   ID: {paper['paper_id']}")
                    
        except Exception as e:
            print(f"❌ Error searching papers: {e}")
    
    async def get_paper_details_demo(self):
        """Demonstrate resource access for paper details."""
        print("\n📖 Getting details for a specific paper...")
        print("-" * 40)
        
        # Use a well-known paper ID
        paper_id = "2301.07041"  # Example ArXiv ID
        
        try:
            result = await self.session.read_resource(
                f"arxiv/{paper_id}"
            )
            
            if result.contents:
                details = result.contents[0].text
                print(f"Paper Details:\n{details}")
                
        except Exception as e:
            print(f"❌ Error getting paper details: {e}")
            print("Note: This might fail if the paper ID doesn't exist on ArXiv")
    
    async def analysis_prompt_demo(self):
        """Demonstrate the analysis prompt."""
        print("\n🧠 Getting analysis prompt template...")
        print("-" * 40)
        
        try:
            result = await self.session.get_prompt(
                "analyze_paper",
                {}
            )
            
            if result.messages:
                template = result.messages[0].content.text
                print("Analysis Workflow Template:")
                print(template[:500] + "..." if len(template) > 500 else template)
                
        except Exception as e:
            print(f"❌ Error getting analysis prompt: {e}")
    
    def pretty_print_json(self, data: Any) -> str:
        """Pretty print JSON data."""
        return json.dumps(data, indent=2, ensure_ascii=False)


async def main():
    """Main entry point for the client demo."""
    print("🎯 ArXiv MCP Server Client Demo")
    print("Make sure the ArXiv server is available!")
    print("=" * 50)
    
    client = ArXivMCPClient()
    
    try:
        await client.connect()
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the server.py is in the current directory")
        print("2. Check that all dependencies are installed: uv sync")
        print("3. Verify the server runs independently: uv run python server.py")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())