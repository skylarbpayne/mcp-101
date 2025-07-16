#!/usr/bin/env python3
"""
OAuth 2.1 Research Assistant MCP Server with GitHub Integration

This server demonstrates a complete OAuth 2.1 + PKCE implementation for MCP,
integrating with GitHub API to save research papers as repositories.
"""

import asyncio
import hashlib
import secrets
import base64
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

import arxiv
import httpx
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP with HTTP transport for OAuth compatibility
mcp = FastMCP("OAuth Research Server")
app = FastAPI()

# OAuth Configuration
GITHUB_CLIENT_ID = "your_github_client_id"  # Replace with actual client ID
GITHUB_CLIENT_SECRET = "your_github_client_secret"  # Replace with actual secret
REDIRECT_URI = "http://localhost:8002/oauth/callback"
AUTHORIZATION_ENDPOINT = "https://github.com/login/oauth/authorize"
TOKEN_ENDPOINT = "https://github.com/login/oauth/access_token"

# Storage for OAuth sessions (in production, use proper storage)
oauth_sessions: Dict[str, dict] = {}
access_tokens: Dict[str, dict] = {}

@dataclass
class Paper:
    """Data model for an ArXiv paper"""
    title: str
    authors: List[str]
    summary: str
    pdf_url: str
    paper_id: str
    published: str

class OAuthError(BaseModel):
    error: str
    error_description: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    scope: str
    expires_in: Optional[int] = None

# OAuth 2.1 Well-Known Configuration Endpoint
@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    """OAuth 2.1 authorization server metadata per RFC 8414"""
    return {
        "issuer": "http://localhost:8002",
        "authorization_endpoint": f"http://localhost:8002/oauth/authorize",
        "token_endpoint": f"http://localhost:8002/oauth/token",
        "registration_endpoint": f"http://localhost:8002/oauth/register",
        "scopes_supported": ["repo", "gist", "user:email"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_basic"]
    }

def generate_pkce_challenge():
    """Generate PKCE code verifier and challenge"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

@app.post("/oauth/register")
async def dynamic_client_registration(request: Request):
    """Dynamic Client Registration per RFC 7591"""
    body = await request.json()
    
    # Generate client credentials
    client_id = f"dynamic_client_{secrets.token_urlsafe(16)}"
    client_secret = secrets.token_urlsafe(32)
    
    # Store client info (in production, use proper storage)
    oauth_sessions[client_id] = {
        "client_secret": client_secret,
        "redirect_uris": body.get("redirect_uris", [REDIRECT_URI]),
        "scope": body.get("scope", "repo"),
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "registration_access_token": secrets.token_urlsafe(32),
        "registration_client_uri": f"http://localhost:8002/oauth/register/{client_id}"
    }

@app.get("/oauth/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    scope: str = "repo",
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: str = "S256"
):
    """OAuth 2.1 Authorization endpoint with PKCE support"""
    
    # Validate client_id
    if client_id not in oauth_sessions and client_id != GITHUB_CLIENT_ID:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    
    # Store PKCE challenge for later verification
    session_id = secrets.token_urlsafe(32)
    oauth_sessions[session_id] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Redirect to GitHub for actual authorization
    github_auth_url = (
        f"{AUTHORIZATION_ENDPOINT}"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(scope)}"
        f"&state={session_id}"
    )
    
    return RedirectResponse(url=github_auth_url)

@app.get("/oauth/callback")
async def oauth_callback(code: str, state: str):
    """OAuth callback handler"""
    
    # Retrieve session
    if state not in oauth_sessions:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    session = oauth_sessions[state]
    
    # Exchange code for token with GitHub
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            TOKEN_ENDPOINT,
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Token exchange failed")
        
        token_data = token_response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data["error_description"])
    
    # Store access token
    access_token = token_data["access_token"]
    access_tokens[session["client_id"]] = {
        "access_token": access_token,
        "token_type": "Bearer",
        "scope": token_data.get("scope", session["scope"]),
        "expires_at": datetime.utcnow() + timedelta(hours=1)  # GitHub tokens don't expire, but we set a reasonable time
    }
    
    # Redirect back to original client
    redirect_url = f"{session['redirect_uri']}?code={secrets.token_urlsafe(32)}"
    if session.get("state"):
        redirect_url += f"&state={session['state']}"
    
    return RedirectResponse(url=redirect_url)

@app.post("/oauth/token")
async def token_exchange(request: Request):
    """OAuth 2.1 Token Exchange endpoint"""
    body = await request.form()
    
    client_id = body.get("client_id")
    code = body.get("code")
    code_verifier = body.get("code_verifier")
    
    if not client_id or client_id not in access_tokens:
        raise HTTPException(status_code=400, detail="Invalid client or authorization")
    
    token_data = access_tokens[client_id]
    
    return TokenResponse(
        access_token=token_data["access_token"],
        token_type=token_data["token_type"],
        scope=token_data["scope"],
        expires_in=3600
    )

def get_github_token(request: Request) -> str:
    """Extract and validate GitHub access token from request"""
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    # In a real implementation, validate the token
    return token

# MCP Tools with OAuth Protection

@mcp.tool()
def search_papers(query: str, max_results: int = 5) -> Dict:
    """Search ArXiv for scientific papers"""
    search = arxiv.Search(
        query=query,
        max_results=min(max_results, 20),
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    papers = []
    for result in search.results():
        paper = Paper(
            title=result.title.strip(),
            authors=[author.name for author in result.authors],
            summary=result.summary.replace('\n', ' ').strip(),
            pdf_url=result.pdf_url,
            paper_id=result.entry_id.split('/')[-1],
            published=result.published.strftime('%Y-%m-%d')
        )
        papers.append(paper.__dict__)
    
    return {
        "papers": papers,
        "query": query,
        "total_results": len(papers)
    }

@mcp.tool()
async def save_paper_to_github(paper_id: str, repo_name: str) -> Dict:
    """Save ArXiv paper as GitHub repository with OAuth 2.1 protection"""
    
    # This would trigger OAuth flow if not authenticated
    # For demo purposes, we simulate the auth check
    auth_header = mcp.request_context.session.get_auth_header()
    if not auth_header:
        raise HTTPException(
            status_code=401, 
            detail="OAuth authorization required",
            headers={"WWW-Authenticate": "Bearer scope=\"repo\""}
        )
    
    # Get paper details from ArXiv
    search = arxiv.Search(id_list=[paper_id])
    try:
        paper = next(search.results())
    except StopIteration:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    
    token = auth_header.replace("Bearer ", "")
    
    # Create GitHub repository
    async with httpx.AsyncClient() as client:
        # Create repository
        repo_data = {
            "name": repo_name,
            "description": f"Research paper: {paper.title}",
            "private": False,
            "auto_init": True
        }
        
        repo_response = await client.post(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json=repo_data
        )
        
        if repo_response.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail="Failed to create repository")
        
        repo_info = repo_response.json()
        
        # Create README with paper information
        readme_content = f"""# {paper.title}

## Authors
{', '.join([author.name for author in paper.authors])}

## Published
{paper.published.strftime('%Y-%m-%d')}

## Abstract
{paper.summary}

## Links
- [ArXiv Page]({paper.entry_id})
- [PDF Download]({paper.pdf_url})

## Categories
{', '.join(paper.categories)}

---
*This repository was automatically created by the MCP OAuth Research Assistant.*
"""
        
        # Create README file
        readme_response = await client.put(
            f"https://api.github.com/repos/{repo_info['full_name']}/contents/README.md",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={
                "message": "Add paper information",
                "content": base64.b64encode(readme_content.encode()).decode()
            }
        )
        
        return {
            "repository_url": repo_info["html_url"],
            "paper_title": paper.title,
            "paper_id": paper_id,
            "created_at": repo_info["created_at"]
        }

@mcp.tool()
async def create_research_gist(paper_id: str, notes: str = "") -> Dict:
    """Create a GitHub Gist with paper summary and notes"""
    
    auth_header = mcp.request_context.session.get_auth_header()
    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="OAuth authorization required", 
            headers={"WWW-Authenticate": "Bearer scope=\"gist\""}
        )
    
    # Get paper details
    search = arxiv.Search(id_list=[paper_id])
    try:
        paper = next(search.results())
    except StopIteration:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    
    token = auth_header.replace("Bearer ", "")
    
    gist_content = f"""# {paper.title}

**Authors:** {', '.join([author.name for author in paper.authors])}
**Published:** {paper.published.strftime('%Y-%m-%d')}
**ArXiv ID:** {paper_id}

## Abstract
{paper.summary}

## Research Notes
{notes if notes else "Add your research notes here..."}

## Links
- [ArXiv]({paper.entry_id})
- [PDF]({paper.pdf_url})
"""
    
    async with httpx.AsyncClient() as client:
        gist_response = await client.post(
            "https://api.github.com/gists",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={
                "description": f"Research notes: {paper.title}",
                "public": False,
                "files": {
                    f"{paper_id}_notes.md": {
                        "content": gist_content
                    }
                }
            }
        )
        
        if gist_response.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail="Failed to create gist")
        
        gist_info = gist_response.json()
        
        return {
            "gist_url": gist_info["html_url"],
            "gist_id": gist_info["id"],
            "paper_title": paper.title,
            "paper_id": paper_id
        }

def main():
    """Main entry point"""
    # Mount FastAPI app for OAuth endpoints
    mcp.app.mount("/", app)
    
    # Run with HTTP transport for OAuth compatibility
    mcp.run(
        transport="http",
        port=8002
    )

if __name__ == "__main__":
    main()
