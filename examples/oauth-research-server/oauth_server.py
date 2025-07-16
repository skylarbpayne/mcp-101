#!/usr/bin/env python3
"""
OAuth Research Server - MCP server demonstrating OAuth 2.1 + PKCE with GitHub integration.

This server implements proper MCP OAuth flow:
1. HTTP transport for OAuth compatibility
2. OAuth 2.1 with PKCE support
3. GitHub API integration requiring OAuth credentials
4. Dynamic client registration
5. Proper OAuth metadata discovery

Run: python oauth_server.py
"""

import asyncio
import base64
import hashlib
import json
import os
import secrets
import time
from typing import Dict, List, Optional
from urllib.parse import urlencode, parse_qs
import uuid
import webbrowser

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

# GitHub OAuth configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com"

# Server configuration
SERVER_PORT = 8002
SERVER_HOST = "localhost"
REDIRECT_URI = f"http://{SERVER_HOST}:{SERVER_PORT}/oauth/callback"

# Initialize FastMCP with HTTP transport
mcp = FastMCP("OAuth Research Server")

# OAuth state storage (in production, use proper database)
oauth_sessions: Dict[str, Dict] = {}
registered_clients: Dict[str, Dict] = {}
access_tokens: Dict[str, Dict] = {}

class OAuthMetadata(BaseModel):
    """OAuth 2.1 server metadata"""
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str
    scopes_supported: List[str]
    response_types_supported: List[str]
    code_challenge_methods_supported: List[str]

class ClientRegistration(BaseModel):
    """Dynamic client registration request"""
    client_name: str
    redirect_uris: List[str]
    scope: str = "repo"

class ClientRegistrationResponse(BaseModel):
    """Dynamic client registration response"""
    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: List[str]

class TokenRequest(BaseModel):
    """OAuth token request"""
    grant_type: str
    code: str
    redirect_uri: str
    client_id: str
    client_secret: Optional[str] = None
    code_verifier: Optional[str] = None

class TokenResponse(BaseModel):
    """OAuth token response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str

class GitHubRepository(BaseModel):
    """GitHub repository model"""
    name: str
    full_name: str
    description: Optional[str]
    html_url: str
    created_at: str
    language: Optional[str]
    stargazers_count: int

class PaperRepository(BaseModel):
    """Research paper repository model"""
    title: str
    description: str
    content: str
    filename: str

# Helper functions
def generate_code_challenge(code_verifier: str) -> str:
    """Generate PKCE code challenge from verifier"""
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")

def get_auth_context() -> Dict:
    """Get authentication context from MCP request"""
    # In a real implementation, this would extract auth from request context
    return getattr(mcp.request_context, 'auth', {}) if hasattr(mcp, 'request_context') else {}

# OAuth 2.1 Server Endpoints
@mcp.get("/.well-known/oauth-authorization-server")
async def oauth_metadata() -> OAuthMetadata:
    """OAuth 2.1 metadata discovery endpoint"""
    return OAuthMetadata(
        issuer=f"http://{SERVER_HOST}:{SERVER_PORT}",
        authorization_endpoint=f"http://{SERVER_HOST}:{SERVER_PORT}/oauth/authorize",
        token_endpoint=f"http://{SERVER_HOST}:{SERVER_PORT}/oauth/token",
        registration_endpoint=f"http://{SERVER_HOST}:{SERVER_PORT}/oauth/register",
        scopes_supported=["repo", "user"],
        response_types_supported=["code"],
        code_challenge_methods_supported=["S256"]
    )

@mcp.post("/oauth/register")
async def register_client(registration: ClientRegistration) -> ClientRegistrationResponse:
    """Dynamic client registration endpoint"""
    client_id = str(uuid.uuid4())
    client_secret = secrets.token_urlsafe(32)
    
    registered_clients[client_id] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": registration.client_name,
        "redirect_uris": registration.redirect_uris,
        "scope": registration.scope
    }
    
    return ClientRegistrationResponse(
        client_id=client_id,
        client_secret=client_secret,
        client_name=registration.client_name,
        redirect_uris=registration.redirect_uris
    )

@mcp.get("/oauth/authorize")
async def oauth_authorize(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(default="repo"),
    state: str = Query(None),
    code_challenge: str = Query(None),
    code_challenge_method: str = Query("S256")
):
    """OAuth 2.1 authorization endpoint with PKCE"""
    # Validate client
    if client_id not in registered_clients:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    
    client = registered_clients[client_id]
    if redirect_uri not in client["redirect_uris"]:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    
    # Generate session state
    session_state = secrets.token_urlsafe(32)
    oauth_sessions[session_state] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "timestamp": time.time()
    }
    
    # Redirect to GitHub OAuth
    github_params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "repo user",
        "state": session_state
    }
    
    github_auth_url = f"{GITHUB_AUTHORIZATION_URL}?{urlencode(github_params)}"
    return RedirectResponse(github_auth_url)

@mcp.get("/oauth/callback")
async def oauth_callback(code: str = Query(...), state: str = Query(...)):
    """OAuth callback from GitHub"""
    if state not in oauth_sessions:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    session = oauth_sessions[state]
    
    # Exchange code for GitHub access token
    token_data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            data=token_data,
            headers={"Accept": "application/json"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Token exchange failed")
        
        github_token = response.json()["access_token"]
    
    # Generate MCP server access token
    mcp_token = secrets.token_urlsafe(32)
    access_tokens[mcp_token] = {
        "github_token": github_token,
        "client_id": session["client_id"],
        "scope": session["scope"],
        "expires_at": time.time() + 3600
    }
    
    # Generate authorization code for client
    auth_code = secrets.token_urlsafe(32)
    oauth_sessions[auth_code] = {
        **session,
        "mcp_token": mcp_token,
        "type": "authorization_code"
    }
    
    # Redirect back to client
    params = {"code": auth_code}
    if session["state"]:
        params["state"] = session["state"]
    
    callback_url = f"{session['redirect_uri']}?{urlencode(params)}"
    return RedirectResponse(callback_url)

@mcp.post("/oauth/token")
async def oauth_token(request: TokenRequest) -> TokenResponse:
    """OAuth token endpoint"""
    if request.grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant type")
    
    if request.code not in oauth_sessions:
        raise HTTPException(status_code=400, detail="Invalid authorization code")
    
    session = oauth_sessions[request.code]
    
    # Validate client
    if session["client_id"] != request.client_id:
        raise HTTPException(status_code=400, detail="Client mismatch")
    
    # Validate PKCE
    if session.get("code_challenge") and request.code_verifier:
        expected_challenge = generate_code_challenge(request.code_verifier)
        if session["code_challenge"] != expected_challenge:
            raise HTTPException(status_code=400, detail="Invalid code verifier")
    
    # Return access token
    return TokenResponse(
        access_token=session["mcp_token"],
        scope=session["scope"]
    )

# GitHub-integrated MCP tools (OAuth protected)
@mcp.tool()
async def save_paper_to_github(paper_title: str, paper_content: str, repo_name: str) -> Dict:
    """
    Save a research paper to GitHub as a new repository.
    
    Requires OAuth authentication with 'repo' scope.
    
    Args:
        paper_title: Title of the research paper
        paper_content: Full content/abstract of the paper
        repo_name: Name for the GitHub repository
        
    Returns:
        Dictionary with repository information
    """
    # Get authentication context
    auth_context = get_auth_context()
    if not auth_context.get("bearer"):
        raise HTTPException(status_code=401, detail="OAuth authentication required")
    
    # Validate token
    bearer_token = auth_context["bearer"]
    if bearer_token not in access_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    token_info = access_tokens[bearer_token]
    github_token = token_info["github_token"]
    
    # Create repository on GitHub
    repo_data = {
        "name": repo_name,
        "description": f"Research paper: {paper_title}",
        "private": False,
        "auto_init": True
    }
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        # Create repository
        repo_response = await client.post(
            f"{GITHUB_API_BASE}/user/repos",
            json=repo_data,
            headers=headers
        )
        
        if repo_response.status_code != 201:
            raise HTTPException(status_code=400, detail="Failed to create repository")
        
        repo_info = repo_response.json()
        
        # Create README with paper content
        readme_content = f"""# {paper_title}

## Abstract

{paper_content}

## Paper Details

- **Title**: {paper_title}
- **Repository**: {repo_info['html_url']}
- **Created**: {repo_info['created_at']}

This repository was created via MCP OAuth integration.
"""
        
        # Commit README file
        file_data = {
            "message": f"Add paper: {paper_title}",
            "content": base64.b64encode(readme_content.encode()).decode(),
            "path": "README.md"
        }
        
        await client.put(
            f"{GITHUB_API_BASE}/repos/{repo_info['full_name']}/contents/README.md",
            json=file_data,
            headers=headers
        )
    
    return {
        "repository": {
            "name": repo_info["name"],
            "full_name": repo_info["full_name"],
            "html_url": repo_info["html_url"],
            "description": repo_info["description"],
            "created_at": repo_info["created_at"]
        },
        "paper_title": paper_title,
        "status": "saved"
    }

@mcp.tool()
async def list_research_repositories() -> List[GitHubRepository]:
    """
    List all GitHub repositories for research papers.
    
    Requires OAuth authentication with 'repo' scope.
    
    Returns:
        List of GitHubRepository objects
    """
    # Get authentication context
    auth_context = get_auth_context()
    if not auth_context.get("bearer"):
        raise HTTPException(status_code=401, detail="OAuth authentication required")
    
    # Validate token
    bearer_token = auth_context["bearer"]
    if bearer_token not in access_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    token_info = access_tokens[bearer_token]
    github_token = token_info["github_token"]
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/user/repos",
            headers=headers,
            params={"type": "owner", "sort": "created", "direction": "desc"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to list repositories")
        
        repos_data = response.json()
        
        repositories = []
        for repo in repos_data:
            repositories.append(GitHubRepository(
                name=repo["name"],
                full_name=repo["full_name"],
                description=repo.get("description", ""),
                html_url=repo["html_url"],
                created_at=repo["created_at"],
                language=repo.get("language"),
                stargazers_count=repo["stargazers_count"]
            ))
        
        return repositories

@mcp.tool()
async def search_papers_mock(query: str, max_results: int = 5) -> Dict:
    """
    Mock paper search function for demonstration.
    
    In a real implementation, this would search ArXiv or other paper databases.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        Mock search results
    """
    # Mock data for demonstration
    mock_papers = [
        {
            "title": f"Advanced {query.title()} Methods in Machine Learning",
            "authors": ["Dr. Alice Smith", "Prof. Bob Johnson"],
            "abstract": f"This paper presents novel approaches to {query} using deep learning techniques. Our method achieves state-of-the-art results on benchmark datasets.",
            "paper_id": "2024.001",
            "published": "2024-01-15"
        },
        {
            "title": f"A Survey of {query.title()} Applications",
            "authors": ["Dr. Carol Davis", "Dr. David Wilson"],
            "abstract": f"We provide a comprehensive survey of {query} applications in various domains, highlighting key challenges and future directions.",
            "paper_id": "2024.002",
            "published": "2024-02-20"
        }
    ]
    
    return {
        "papers": mock_papers[:max_results],
        "query": query,
        "total_results": len(mock_papers[:max_results])
    }

def main():
    """Main entry point for the OAuth research server."""
    print("🔐 Starting OAuth Research Server...")
    print(f"Server will run on http://{SERVER_HOST}:{SERVER_PORT}")
    print("\nRequired environment variables:")
    print(f"  GITHUB_CLIENT_ID: {'✅ Set' if GITHUB_CLIENT_ID else '❌ Missing'}")
    print(f"  GITHUB_CLIENT_SECRET: {'✅ Set' if GITHUB_CLIENT_SECRET else '❌ Missing'}")
    
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        print("\n⚠️  Please set GitHub OAuth credentials:")
        print("  1. Create a GitHub OAuth app at: https://github.com/settings/developers")
        print(f"  2. Set Authorization callback URL to: {REDIRECT_URI}")
        print("  3. Export GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET")
        return
    
    # Run with HTTP transport for OAuth
    mcp.run(transport="http", port=SERVER_PORT)

if __name__ == "__main__":
    main()
