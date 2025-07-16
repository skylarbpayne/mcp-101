#!/usr/bin/env python3
"""
MCP Research Assistant Server - Correct OAuth Implementation

This server demonstrates the CORRECT MCP OAuth flow where:
1. MCP server acts as RESOURCE SERVER only (not authorization server)
2. Delegates user authentication to GitHub (third-party authorization server)
3. Creates internal MCP tokens bound to GitHub sessions
4. Never exposes OAuth AS endpoints to clients
"""

import asyncio
import secrets
import jwt
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

import arxiv
import httpx
from fastapi import FastAPI, Request, HTTPException, Depends, Cookie
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("MCP Research Server")
app = FastAPI()

# Configuration
GITHUB_CLIENT_ID = "your_github_client_id"  # Replace with actual
GITHUB_CLIENT_SECRET = "your_github_client_secret"  # Replace with actual
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com"

# Internal MCP token signing (use proper secret in production)
MCP_SIGNING_KEY = "your-mcp-server-secret-key"  # Replace with actual secret
FRONTEND_URL = "http://localhost:3000"  # Where your MCP client UI runs

# Storage for GitHub sessions (use proper database in production)
github_sessions: Dict[str, dict] = {}  # session_id -> {github_token, user_info, expires}

@dataclass
class Paper:
    """Data model for an ArXiv paper"""
    title: str
    authors: List[str]
    summary: str
    pdf_url: str
    paper_id: str
    published: str

# ============================================================================
# GitHub OAuth Delegation (NOT OAuth Authorization Server endpoints)
# ============================================================================

@app.get("/login/github")
async def login_with_github(request: Request):
    """
    Redirect user to GitHub for authentication.
    This is NOT an OAuth AS endpoint - it's a login helper for our app.
    """
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state temporarily (in production, use proper session storage)
    github_sessions[state] = {
        "state": state,
        "created_at": datetime.utcnow().isoformat(),
        "status": "pending"
    }
    
    # Build GitHub authorization URL
    github_auth_params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": "http://localhost:8002/auth/callback",
        "scope": "repo user:email",
        "state": state,
        "response_type": "code"
    }
    
    github_url = GITHUB_AUTH_URL + "?" + "&".join([
        f"{k}={v}" for k, v in github_auth_params.items()
    ])
    
    return RedirectResponse(url=github_url)

@app.get("/auth/callback")
async def github_callback(code: str, state: str):
    """
    Handle GitHub OAuth callback.
    Creates internal MCP token bound to GitHub session.
    """
    # Validate state
    if state not in github_sessions:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    session = github_sessions[state]
    
    # Exchange code for GitHub access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": "http://localhost:8002/auth/callback"
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="GitHub token exchange failed")
        
        token_data = token_response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data.get("error_description", "GitHub authorization failed"))
        
        github_access_token = token_data["access_token"]
    
    # Get GitHub user info
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            f"{GITHUB_API_BASE}/user",
            headers={"Authorization": f"Bearer {github_access_token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get GitHub user info")
        
        github_user = user_response.json()
    
    # Create internal MCP session
    session_id = secrets.token_urlsafe(32)
    github_sessions[session_id] = {
        "github_token": github_access_token,
        "github_user": github_user,
        "scopes": token_data.get("scope", "repo user:email").split(","),
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        "status": "active"
    }
    
    # Create internal MCP JWT token
    mcp_token_payload = {
        "sub": str(github_user["id"]),  # GitHub user ID
        "username": github_user["login"],
        "session_id": session_id,
        "scopes": ["github:repo", "github:user"],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "provider": "github",
        "iss": "mcp-research-server"
    }
    
    internal_token = jwt.encode(
        mcp_token_payload,
        MCP_SIGNING_KEY,
        algorithm="HS256"
    )
    
    # Clean up the pending state
    if state in github_sessions:
        del github_sessions[state]
    
    # Create success page with token (in production, use better method)
    success_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Authentication Success</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
            .success {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; }}
            .token {{ background: #f8f9fa; padding: 10px; font-family: monospace; word-break: break-all; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="success">
            <h2>✅ Authentication Successful!</h2>
            <p>Welcome <strong>{github_user['login']}</strong>! You have successfully authenticated with GitHub.</p>
            
            <h3>Your MCP Access Token:</h3>
            <div class="token">{internal_token}</div>
            
            <p><strong>Important:</strong> Use this token in your MCP client as the Bearer token for API requests.</p>
            
            <h3>Next Steps:</h3>
            <ol>
                <li>Copy the token above</li>
                <li>Configure your MCP client with: <code>Authorization: Bearer [token]</code></li>
                <li>Start using the research assistant tools!</li>
            </ol>
        </div>
        
        <script>
            // Auto-copy token for convenience
            const token = "{internal_token}";
            if (navigator.clipboard) {{
                navigator.clipboard.writeText(token);
                console.log("Token copied to clipboard");
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=success_html)

@app.get("/logout")
async def logout(mcp_token: Optional[str] = Cookie(None)):
    """Logout user and revoke internal session"""
    if mcp_token:
        try:
            payload = jwt.decode(mcp_token, MCP_SIGNING_KEY, algorithms=["HS256"])
            session_id = payload.get("session_id")
            if session_id in github_sessions:
                # Optionally revoke GitHub token here
                del github_sessions[session_id]
        except jwt.InvalidTokenError:
            pass
    
    return {"message": "Logged out successfully"}

# ============================================================================
# Internal Token Validation
# ============================================================================

def validate_mcp_token(request: Request) -> dict:
    """
    Validate internal MCP token and return session info.
    This replaces the old get_github_token function.
    """
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Missing or invalid MCP token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization.split(" ")[1]
    
    try:
        # Decode and validate internal MCP token
        payload = jwt.decode(token, MCP_SIGNING_KEY, algorithms=["HS256"])
        session_id = payload.get("session_id")
        
        # Check if session still exists
        if session_id not in github_sessions:
            raise HTTPException(status_code=401, detail="Session expired or invalid")
        
        session = github_sessions[session_id]
        
        # Check if session is still active
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.utcnow() > expires_at:
            del github_sessions[session_id]
            raise HTTPException(status_code=401, detail="Session expired")
        
        return {
            "user_id": payload["sub"],
            "username": payload["username"],
            "session_id": session_id,
            "scopes": payload["scopes"],
            "github_token": session["github_token"],
            "github_user": session["github_user"]
        }
        
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def get_github_token_for_session(session_info: dict) -> str:
    """Get GitHub access token for the validated MCP session"""
    return session_info["github_token"]

# ============================================================================
# MCP Tools (Protected by internal tokens)
# ============================================================================

@mcp.tool()
def search_papers(query: str, max_results: int = 5) -> Dict:
    """Search ArXiv for scientific papers (no auth required)"""
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
    """
    Save ArXiv paper as GitHub repository (requires MCP authentication).
    Uses internal MCP token to access bound GitHub session.
    """
    # Validate internal MCP token (not GitHub token directly)
    session_info = validate_mcp_token(mcp.request_context.request)
    github_token = get_github_token_for_session(session_info)
    
    # Get paper details from ArXiv
    search = arxiv.Search(id_list=[paper_id])
    try:
        paper = next(search.results())
    except StopIteration:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    
    # Create GitHub repository using the session's GitHub token
    async with httpx.AsyncClient() as client:
        repo_data = {
            "name": repo_name,
            "description": f"Research paper: {paper.title}",
            "private": False,
            "auto_init": True
        }
        
        repo_response = await client.post(
            f"{GITHUB_API_BASE}/user/repos",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json=repo_data
        )
        
        if repo_response.status_code not in [200, 201]:
            error_detail = repo_response.json().get("message", "Failed to create repository")
            raise HTTPException(status_code=400, detail=f"GitHub API error: {error_detail}")
        
        repo_info = repo_response.json()
        
        # Create comprehensive README
        readme_content = f"""# {paper.title}

[![ArXiv](https://img.shields.io/badge/arXiv-{paper_id}-b31b1b.svg)](https://arxiv.org/abs/{paper_id})

## Authors
{chr(10).join([f"- {author.name}" for author in paper.authors])}

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
*Repository created by MCP Research Assistant*  
*User: {session_info['username']}*  
*Created: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""
        
        # Add README to repository
        import base64
        readme_response = await client.put(
            f"{GITHUB_API_BASE}/repos/{repo_info['full_name']}/contents/README.md",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={
                "message": "Add comprehensive paper information",
                "content": base64.b64encode(readme_content.encode()).decode()
            }
        )
        
        return {
            "repository_url": repo_info["html_url"],
            "repository_name": repo_info["full_name"],
            "paper_title": paper.title,
            "paper_id": paper_id,
            "created_by": session_info["username"],
            "created_at": repo_info["created_at"]
        }

@mcp.tool()
async def create_research_gist(paper_id: str, notes: str = "") -> Dict:
    """Create a GitHub Gist with paper summary and research notes"""
    session_info = validate_mcp_token(mcp.request_context.request)
    github_token = get_github_token_for_session(session_info)
    
    # Get paper details
    search = arxiv.Search(id_list=[paper_id])
    try:
        paper = next(search.results())
    except StopIteration:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    
    gist_content = f"""# Research Notes: {paper.title}

**ArXiv ID:** {paper_id}  
**Authors:** {', '.join([author.name for author in paper.authors])}  
**Published:** {paper.published.strftime('%Y-%m-%d')}

## Abstract
{paper.summary}

## Research Notes
{notes if notes else "Add your research notes here..."}

## Citation
```bibtex
@article{{{paper_id.replace('.', '')},
  title={{{paper.title}}},
  author={{{' and '.join([author.name for author in paper.authors])}}},
  journal={{arXiv preprint arXiv:{paper_id}}},
  year={{{paper.published.strftime('%Y')}}},
  url={{{paper.entry_id}}}
}}
```

## Links
- [ArXiv]({paper.entry_id})
- [PDF]({paper.pdf_url})

---
*Created by: {session_info['username']}*
*Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""
    
    async with httpx.AsyncClient() as client:
        gist_response = await client.post(
            f"{GITHUB_API_BASE}/gists",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={
                "description": f"Research notes: {paper.title}",
                "public": False,
                "files": {
                    f"{paper_id}_research_notes.md": {
                        "content": gist_content
                    }
                }
            }
        )
        
        if gist_response.status_code not in [200, 201]:
            error_detail = gist_response.json().get("message", "Failed to create gist")
            raise HTTPException(status_code=400, detail=f"GitHub API error: {error_detail}")
        
        gist_info = gist_response.json()
        
        return {
            "gist_url": gist_info["html_url"],
            "gist_id": gist_info["id"],
            "paper_title": paper.title,
            "paper_id": paper_id,
            "created_by": session_info["username"]
        }

@mcp.tool()
async def get_user_info() -> Dict:
    """Get authenticated user information"""
    session_info = validate_mcp_token(mcp.request_context.request)
    
    return {
        "username": session_info["username"],
        "github_user": session_info["github_user"]["login"],
        "user_id": session_info["user_id"],
        "scopes": session_info["scopes"],
        "session_active": True
    }

# ============================================================================
# API Info Endpoints (for debugging)
# ============================================================================

@app.get("/")
async def root():
    """Server info and available endpoints"""
    return {
        "server": "MCP Research Assistant",
        "oauth_flow": "Correct MCP OAuth (Resource Server Only)",
        "auth_provider": "GitHub",
        "endpoints": {
            "login": "/login/github",
            "callback": "/auth/callback",
            "logout": "/logout"
        },
        "mcp_tools": ["search_papers", "save_paper_to_github", "create_research_gist", "get_user_info"],
        "note": "This server acts as a resource server only. It delegates authentication to GitHub."
    }

def main():
    """Main entry point"""
    # Mount FastAPI app for OAuth endpoints
    mcp.app.mount("/", app)
    
    # Run with HTTP transport (required for OAuth flows)
    mcp.run(
        transport="http",
        port=8002
    )

if __name__ == "__main__":
    main()
