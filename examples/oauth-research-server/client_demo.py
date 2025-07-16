#!/usr/bin/env python3
"""
Simple MCP OAuth Client Demo

Demonstrates the correct MCP OAuth flow:
1. User authenticates with GitHub via MCP server
2. MCP server creates internal token
3. Client uses internal token for API calls
"""

import asyncio
import webbrowser
import httpx

class MCPClient:
    """Simple MCP client with correct OAuth flow"""
    
    def __init__(self, server_url: str = "http://localhost:8002"):
        self.server_url = server_url
        self.mcp_token = None
    
    async def authenticate(self):
        """Authenticate with MCP server via GitHub"""
        print("🔐 Starting MCP OAuth authentication...")
        print("📋 Flow: MCP server delegates to GitHub, returns internal token")
        print()
        
        # Open browser to MCP server's GitHub login
        login_url = f"{self.server_url}/login/github"
        print(f"🌐 Opening browser to: {login_url}")
        webbrowser.open(login_url)
        
        print("\n📝 Instructions:")
        print("1. Authorize with GitHub")
        print("2. Copy the MCP token from the success page")
        print("3. Paste it here")
        
        self.mcp_token = input("\n🔑 Enter your MCP token: ").strip()
        
        if not self.mcp_token:
            raise ValueError("No token provided")
        
        print("✅ Token received!")
    
    async def search_papers(self, query: str, max_results: int = 3):
        """Search papers (no auth required)"""
        print(f"\n📚 Searching for: '{query}'")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.server_url}/mcp/tools/search_papers",
                    params={"query": query, "max_results": max_results}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    papers = data.get("papers", [])
                    
                    for i, paper in enumerate(papers, 1):
                        print(f"\n{i}. {paper['title']}")
                        print(f"   Authors: {', '.join(paper['authors'])}")
                        print(f"   ArXiv ID: {paper['paper_id']}")
                    
                    return papers
                else:
                    print(f"❌ Search failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"❌ Search error: {e}")
            # Return demo data
            return [{
                "title": "Attention Is All You Need",
                "authors": ["Vaswani et al."],
                "paper_id": "1706.03762"
            }]
    
    async def save_paper_to_github(self, paper_id: str, repo_name: str):
        """Save paper to GitHub (requires auth)"""
        print(f"\n💾 Saving paper {paper_id} to GitHub repo '{repo_name}'")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/mcp/tools/save_paper_to_github",
                    json={"paper_id": paper_id, "repo_name": repo_name},
                    headers={"Authorization": f"Bearer {self.mcp_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Repository created!")
                    print(f"   URL: {data.get('repository_url')}")
                    print(f"   Created by: {data.get('created_by')}")
                    return data
                else:
                    print(f"❌ Save failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Save error: {e}")
            return None

async def demo():
    """Run the demo"""
    print("🚀 MCP OAuth Research Assistant Demo")
    print("=" * 50)
    print("✅ This shows the CORRECT MCP OAuth flow")
    print("✅ MCP server = Resource Server only")
    print("✅ GitHub = Authorization Server")
    print("✅ Internal tokens bound to GitHub sessions")
    print()
    
    client = MCPClient()
    
    # Step 1: Authenticate
    try:
        await client.authenticate()
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Step 2: Search papers
    papers = await client.search_papers("transformer models", 2)
    
    if papers:
        # Step 3: Save first paper to GitHub
        first_paper = papers[0]
        paper_id = first_paper['paper_id']
        repo_name = f"research-{paper_id.replace('.', '-')}"
        
        await client.save_paper_to_github(paper_id, repo_name)
    
    print("\n✅ Demo completed!")
    print("🎉 This demonstrates the correct MCP OAuth specification")

if __name__ == "__main__":
    asyncio.run(demo())
