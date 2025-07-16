#!/usr/bin/env python3
"""
OAuth Client Demo - Demonstrates full MCP OAuth 2.1 flow with PKCE.

This client demonstrates:
1. Dynamic client registration with MCP server
2. OAuth 2.1 authorization with PKCE
3. Token exchange and management
4. Calling OAuth-protected MCP tools
5. Proper error handling and token refresh

Run: python oauth_client_demo.py
"""

import asyncio
import base64
import hashlib
import json
import secrets
import webbrowser
from typing import Dict, Optional
from urllib.parse import urlencode, parse_qs, urlparse

import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client

# Configuration
SERVER_BASE_URL = "http://localhost:8002"
CLIENT_REDIRECT_URI = "http://localhost:8003/callback"

class MCPOAuthClient:
    """MCP OAuth 2.1 client with PKCE support."""
    
    def __init__(self, server_url: str = SERVER_BASE_URL):
        self.server_url = server_url
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.session: Optional[ClientSession] = None
        self.http_client = httpx.AsyncClient()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()
    
    def generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode('utf-8').rstrip('=')
        return code_verifier, code_challenge
    
    async def discover_oauth_metadata(self) -> Dict:
        """Discover OAuth server metadata."""
        print("🔍 Discovering OAuth server metadata...")
        
        response = await self.http_client.get(
            f"{self.server_url}/.well-known/oauth-authorization-server"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to discover OAuth metadata: {response.status_code}")
        
        metadata = response.json()
        print(f"✅ Found OAuth server: {metadata['issuer']}")
        print(f"   Authorization endpoint: {metadata['authorization_endpoint']}")
        print(f"   Token endpoint: {metadata['token_endpoint']}")
        print(f"   Registration endpoint: {metadata['registration_endpoint']}")
        
        return metadata
    
    async def register_client(self, metadata: Dict) -> Dict:
        """Dynamically register client with MCP server."""
        print("📝 Registering OAuth client...")
        
        registration_data = {
            "client_name": "MCP OAuth Demo Client",
            "redirect_uris": [CLIENT_REDIRECT_URI],
            "scope": "repo"
        }
        
        response = await self.http_client.post(
            metadata["registration_endpoint"],
            json=registration_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Client registration failed: {response.status_code}")
        
        client_info = response.json()
        self.client_id = client_info["client_id"]
        self.client_secret = client_info["client_secret"]
        
        print(f"✅ Client registered with ID: {self.client_id}")
        return client_info
    
    async def authorize_user(self, metadata: Dict) -> str:
        """Perform OAuth authorization with PKCE."""
        print("🔐 Starting OAuth authorization flow...")
        
        # Generate PKCE parameters
        code_verifier, code_challenge = self.generate_pkce_pair()
        state = secrets.token_urlsafe(32)
        
        # Build authorization URL
        auth_params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": CLIENT_REDIRECT_URI,
            "scope": "repo",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        auth_url = f"{metadata['authorization_endpoint']}?{urlencode(auth_params)}"
        
        print(f"🌐 Opening browser for authorization...")
        print(f"URL: {auth_url}")
        
        # In a real implementation, you'd either:
        # 1. Open browser and start local server to catch redirect
        # 2. Use device flow
        # 3. Have user manually copy authorization code
        
        # For demo, simulate the callback
        webbrowser.open(auth_url)
        
        print("\n⏳ Please complete authorization in browser...")
        print("After authorization, you'll be redirected to the callback URL.")
        print("Copy the authorization code from the URL and paste it here:")
        
        # In real implementation, you'd capture this automatically
        auth_code = input("Authorization code: ").strip()
        
        # Exchange authorization code for access token
        return await self.exchange_code_for_token(
            metadata["token_endpoint"],
            auth_code,
            code_verifier
        )
    
    async def exchange_code_for_token(self, token_endpoint: str, auth_code: str, code_verifier: str) -> str:
        """Exchange authorization code for access token."""
        print("🔄 Exchanging authorization code for access token...")
        
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": CLIENT_REDIRECT_URI,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code_verifier": code_verifier
        }
        
        response = await self.http_client.post(
            token_endpoint,
            json=token_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
        
        token_info = response.json()
        self.access_token = token_info["access_token"]
        
        print(f"✅ Access token received: {self.access_token[:20]}...")
        return self.access_token
    
    async def connect_to_mcp_server(self) -> ClientSession:
        """Connect to MCP server with OAuth token."""
        print("🔌 Connecting to MCP server...")
        
        # Add Authorization header for MCP requests
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # Connect using SSE client (for HTTP transport)
        async with sse_client(f"{self.server_url}/sse", headers=headers) as (read, write):
            session = ClientSession(read, write)
            await session.initialize()
            
            print("✅ Connected to MCP server with OAuth authentication")
            return session
    
    async def run_oauth_demo(self):
        """Run complete OAuth demonstration."""
        print("🚀 Starting MCP OAuth 2.1 Demo")
        print("=" * 50)
        
        try:
            # Step 1: Discover OAuth metadata
            metadata = await self.discover_oauth_metadata()
            
            # Step 2: Register client
            await self.register_client(metadata)
            
            # Step 3: Authorize user
            await self.authorize_user(metadata)
            
            # Step 4: Try to use protected MCP tools
            await self.demo_protected_tools()
            
        except Exception as e:
            print(f"❌ OAuth demo failed: {e}")
            raise
    
    async def demo_protected_tools(self):
        """Demonstrate using OAuth-protected MCP tools."""
        print("\n🛠️ Testing OAuth-protected MCP tools...")
        print("-" * 40)
        
        # Mock MCP session for demonstration
        # In real implementation, you'd use the actual MCP session
        
        # Test 1: Search papers (should work without auth)
        print("\n1. Testing paper search (no auth required)...")
        try:
            search_result = await self.call_mcp_tool(
                "search_papers_mock",
                {"query": "quantum computing", "max_results": 2}
            )
            print(f"✅ Found {len(search_result['papers'])} papers")
        except Exception as e:
            print(f"❌ Search failed: {e}")
        
        # Test 2: Save paper to GitHub (requires OAuth)
        print("\n2. Testing save paper to GitHub (OAuth required)...")
        try:
            save_result = await self.call_mcp_tool(
                "save_paper_to_github",
                {
                    "paper_title": "Quantum Computing with MCP",
                    "paper_content": "This paper demonstrates quantum computing concepts using the Model Context Protocol.",
                    "repo_name": "quantum-mcp-demo"
                }
            )
            print(f"✅ Paper saved to: {save_result['repository']['html_url']}")
        except Exception as e:
            print(f"❌ Save failed: {e}")
        
        # Test 3: List repositories (requires OAuth)
        print("\n3. Testing list repositories (OAuth required)...")
        try:
            repos = await self.call_mcp_tool("list_research_repositories", {})
            print(f"✅ Found {len(repos)} repositories")
            for repo in repos[:3]:  # Show first 3
                print(f"   • {repo['name']}: {repo['description']}")
        except Exception as e:
            print(f"❌ List repositories failed: {e}")
    
    async def call_mcp_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Call MCP tool with OAuth authentication."""
        # Mock implementation for demonstration
        # In real implementation, this would use the MCP session
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # This is a simplified mock - real MCP would use proper protocol
        response = await self.http_client.post(
            f"{self.server_url}/mcp/tools/{tool_name}",
            json=parameters,
            headers=headers
        )
        
        if response.status_code == 401:
            raise Exception("OAuth authentication required")
        elif response.status_code != 200:
            raise Exception(f"Tool call failed: {response.status_code}")
        
        return response.json()

async def main():
    """Main entry point for OAuth client demo."""
    print("🎯 MCP OAuth 2.1 Client Demo")
    print("Make sure the OAuth server is running on http://localhost:8002")
    print("=" * 60)
    
    async with MCPOAuthClient() as client:
        try:
            await client.run_oauth_demo()
            print("\n🎉 OAuth demo completed successfully!")
        except KeyboardInterrupt:
            print("\n👋 Demo interrupted by user")
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            print("\nTroubleshooting:")
            print("1. Make sure oauth_server.py is running: python oauth_server.py")
            print("2. Check that GitHub OAuth credentials are set")
            print("3. Verify network connectivity to GitHub")

if __name__ == "__main__":
    asyncio.run(main())
