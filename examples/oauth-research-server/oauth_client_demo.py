#!/usr/bin/env python3
"""
OAuth Client Demo for MCP Research Assistant

This client demonstrates the complete OAuth 2.1 + PKCE flow with the 
MCP OAuth Research Server, showing how to authenticate and use protected tools.
"""

import asyncio
import secrets
import hashlib
import base64
import urllib.parse
import webbrowser
from typing import Optional

import httpx
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters
from mcp.client.sse import SseServerParameters

class OAuth2Client:
    """OAuth 2.1 client with PKCE support for MCP"""
    
    def __init__(self, server_base_url: str = "http://localhost:8002"):
        self.server_base_url = server_base_url
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.code_verifier: Optional[str] = None
        self.code_challenge: Optional[str] = None
    
    def _generate_pkce_challenge(self):
        """Generate PKCE code verifier and challenge"""
        self.code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        self.code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
    
    async def register_client(self) -> dict:
        """Perform dynamic client registration"""
        registration_data = {
            "redirect_uris": ["http://localhost:3000/callback"],
            "scope": "repo gist user:email",
            "client_name": "MCP OAuth Demo Client",
            "client_uri": "http://localhost:3000"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_base_url}/oauth/register",
                json=registration_data
            )
            response.raise_for_status()
            data = response.json()
            
            self.client_id = data["client_id"]
            self.client_secret = data["client_secret"]
            
            print(f"✅ Client registered successfully!")
            print(f"   Client ID: {self.client_id}")
            print(f"   Client Secret: {self.client_secret[:10]}...")
            
            return data
    
    async def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate OAuth authorization URL with PKCE"""
        if not self.client_id:
            await self.register_client()
        
        self._generate_pkce_challenge()
        
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": "http://localhost:3000/callback",
            "scope": "repo gist",
            "state": state,
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
            "response_type": "code"
        }
        
        auth_url = f"{self.server_base_url}/oauth/authorize?" + urllib.parse.urlencode(params)
        return auth_url
    
    async def exchange_code_for_token(self, authorization_code: str) -> dict:
        """Exchange authorization code for access token"""
        token_data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "code": authorization_code,
            "redirect_uri": "http://localhost:3000/callback",
            "code_verifier": self.code_verifier
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_base_url}/oauth/token",
                data=token_data
            )
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data["access_token"]
            
            print(f"✅ Access token obtained!")
            print(f"   Token: {self.access_token[:20]}...")
            print(f"   Scope: {data.get('scope', 'N/A')}")
            
            return data

class MCPResearchClient:
    """MCP client for the OAuth Research Assistant"""
    
    def __init__(self):
        self.oauth_client = OAuth2Client()
        self.session: Optional[ClientSession] = None
    
    async def authenticate(self):
        """Perform OAuth authentication flow"""
        print("🔐 Starting OAuth 2.1 authentication flow...")
        
        # Get authorization URL
        auth_url = await self.oauth_client.get_authorization_url()
        
        print(f"\n📱 Opening browser for authorization...")
        print(f"   URL: {auth_url}")
        
        # Open browser for user authorization
        webbrowser.open(auth_url)
        
        # In a real application, you would set up a local server to receive the callback
        # For this demo, we'll simulate the callback
        print("\n⏳ Please complete the authorization in your browser...")
        print("   After authorization, you'll be redirected to GitHub and then back.")
        
        # Simulate getting the authorization code
        # In practice, this would come from the callback handler
        auth_code = input("\n🔑 Enter the authorization code from the callback URL: ")
        
        # Exchange code for token
        await self.oauth_client.exchange_code_for_token(auth_code)
        
        print("✅ OAuth authentication complete!")
    
    async def connect_to_server(self):
        """Connect to the MCP server"""
        try:
            # Connect using SSE (Server-Sent Events) transport for HTTP
            server_params = SseServerParameters(
                url=f"http://localhost:8002/sse",
                headers={"Authorization": f"Bearer {self.oauth_client.access_token}"}
            )
            
            self.session = ClientSession(server_params)
            await self.session.initialize()
            
            print("🔗 Connected to MCP OAuth Research Server")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to server: {e}")
            return False
    
    async def list_available_tools(self):
        """List available tools from the server"""
        if not self.session:
            print("❌ Not connected to server")
            return
        
        try:
            tools = await self.session.list_tools()
            print("\n🛠️  Available Tools:")
            for tool in tools.tools:
                print(f"   • {tool.name}: {tool.description}")
        except Exception as e:
            print(f"❌ Error listing tools: {e}")
    
    async def search_papers(self, query: str, max_results: int = 5):
        """Search for papers using the MCP server"""
        if not self.session:
            print("❌ Not connected to server")
            return None
        
        try:
            result = await self.session.call_tool(
                "search_papers",
                {"query": query, "max_results": max_results}
            )
            
            print(f"\n📚 Search Results for '{query}':")
            papers = result.content[0].text  # Assuming JSON response
            
            import json
            data = json.loads(papers)
            
            for i, paper in enumerate(data["papers"], 1):
                print(f"\n   {i}. {paper['title']}")
                print(f"      Authors: {', '.join(paper['authors'])}")
                print(f"      Published: {paper['published']}")
                print(f"      ArXiv ID: {paper['paper_id']}")
            
            return data["papers"]
            
        except Exception as e:
            print(f"❌ Error searching papers: {e}")
            return None
    
    async def save_paper_to_github(self, paper_id: str, repo_name: str):
        """Save a paper to GitHub using OAuth-protected tool"""
        if not self.session:
            print("❌ Not connected to server")
            return
        
        try:
            print(f"\n💾 Saving paper {paper_id} to GitHub repository '{repo_name}'...")
            
            result = await self.session.call_tool(
                "save_paper_to_github",
                {"paper_id": paper_id, "repo_name": repo_name}
            )
            
            import json
            data = json.loads(result.content[0].text)
            
            print(f"✅ Paper saved successfully!")
            print(f"   Repository: {data['repository_url']}")
            print(f"   Paper: {data['paper_title']}")
            print(f"   Created: {data['created_at']}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error saving paper: {e}")
            return None
    
    async def create_research_gist(self, paper_id: str, notes: str = ""):
        """Create a research gist with paper information"""
        if not self.session:
            print("❌ Not connected to server")
            return
        
        try:
            print(f"\n📝 Creating research gist for paper {paper_id}...")
            
            result = await self.session.call_tool(
                "create_research_gist",
                {"paper_id": paper_id, "notes": notes}
            )
            
            import json
            data = json.loads(result.content[0].text)
            
            print(f"✅ Research gist created!")
            print(f"   Gist URL: {data['gist_url']}")
            print(f"   Paper: {data['paper_title']}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error creating gist: {e}")
            return None

async def demo_workflow():
    """Demonstrate the complete OAuth workflow"""
    print("🚀 MCP OAuth Research Assistant Demo")
    print("=" * 50)
    
    client = MCPResearchClient()
    
    # Step 1: OAuth Authentication
    await client.authenticate()
    
    # Step 2: Connect to MCP Server
    if not await client.connect_to_server():
        return
    
    # Step 3: List available tools
    await client.list_available_tools()
    
    # Step 4: Search for papers
    papers = await client.search_papers("transformer attention mechanisms", 3)
    
    if papers:
        # Step 5: Save first paper to GitHub
        first_paper = papers[0]
        repo_name = f"research-{first_paper['paper_id'].replace('.', '-')}"
        
        await client.save_paper_to_github(first_paper['paper_id'], repo_name)
        
        # Step 6: Create a research gist
        research_notes = """
## Initial Analysis

This paper presents interesting work on transformer attention mechanisms.

### Key Points:
- Novel attention approach
- Improved efficiency
- Strong experimental results

### Questions:
- How does this compare to recent work?
- What are the computational requirements?
        """.strip()
        
        await client.create_research_gist(first_paper['paper_id'], research_notes)
    
    print("\n✅ Demo completed successfully!")
    print("🎉 You now have a complete OAuth-protected MCP research assistant!")

def simple_demo():
    """Simple demo without OAuth for testing basic functionality"""
    print("🧪 Running simple demo (no OAuth)...")
    # This would connect to the server without OAuth for basic testing

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        simple_demo()
    else:
        asyncio.run(demo_workflow())
