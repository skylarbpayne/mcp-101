#!/usr/bin/env python3
"""
MCP Research Assistant Server - Simple Correct OAuth Demo

This demonstrates the CORRECT MCP OAuth flow:
- MCP server = Resource Server ONLY
- GitHub = Authorization Server  
- Internal tokens bound to GitHub sessions
"""

import secrets
import jwt
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional

import arxiv
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("MCP Research Server")
app = FastAPI()

# Configuration - Replace with your GitHub OAuth app credentials
GITHUB_CLIENT_ID = "your_github_client_id"
GITHUB_CLIENT_SECRET = "your_github_client_secret" 
MCP_SIGNING_KEY = "your-secret-signing-key"

# Storage for GitHub sessions (use proper database in production)
github_sessions: Dict[str, dict] = {}

# ============================================================================
# GitHub OAuth Delegation (MCP acts as Resource Server only)
# ============================================================================

@app.get("/login/github")
async def login_with_github():
    """Redirect user to GitHub for authentication"""
    state = secrets.token_urlsafe(32)
    github_sessions[state] = {"created_at": datetime.utcnow(), "status": "pending"}
    
    github_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri=http://localhost:8002/auth/callback"
        f"&scope=repo user:email"
        f"&state={state}"
    )
    return RedirectResponse(url=github_url)

@app.get("/auth/callback")
async def github_callback(code: str, state: str):
    """Handle GitHub OAuth callback and create internal MCP token"""
    if state not in github_sessions:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # Exchange code for GitHub token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
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
        github_access_token = token_data["access_token"]
    
    # Get GitHub user info
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_access_token}"}
        )
        github_user = user_response.json()
    
    # Create internal MCP session
    session_id = secrets.token_urlsafe(32)
    github_sessions[session_id] = {
        "github_token": github_access_token,
        "github_user": github_user,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    
    # Create internal MCP JWT token
    mcp_token = jwt.encode(
        {
            "sub": str(github_user["id"]),
            "username": github_user["login"],
            "session_id": session_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iss": "mcp-research-server"
        },
        MCP_SIGNING_KEY,
        algorithm="HS256"
    )
    
    # Clean up pending state
    del github_sessions[state]
    
    # Return success page with token
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>MCP Authentication Success</title></head>
    <body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
        <div style="background: #d4edda; color: #155724; padding: 15px; border-radius: 5px;">
            <h2>✅ Authentication Successful!</h2>
            <p>Welcome <strong>{github_user['login']}</strong>!</p>
            
            <h3>Your MCP Access Token:</h3>
            <div style="background: #f8f9fa; padding: 10px; font-family: monospace; word-break: break-all;">
                {mcp_token}
            </div>
            
            <p><strong>Copy this token</strong> and use it in your MCP client.</p>
        </div>
    </body>
    </html>
    """)

# ============================================================================
# Token Validation
# ============================================================================

def validate_mcp_token(request: Request) -> dict:
    """Validate internal MCP token and return session info"""
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing MCP token")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, MCP_SIGNING_KEY, algorithms=["HS256"])
        session_id = payload.get("session_id")
        
        if session_id not in github_sessions:
            raise HTTPException(status_code=401, detail="Session expired")
        
        session = github_sessions[session_id]
        expires_at = session["expires_at"]
        if datetime.utcnow() > expires_at:
            del github_sessions[session_id]
            raise HTTPException(status_code=401, detail="Session expired")
        
        return {
            "username": payload["username"],
            "github_token": session["github_token"],
            "github_user": session["github_user"]
        }
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
def search_papers(query: str, max_results: int = 5) -> Dict:
    """Search ArXiv for scientific papers"""
    search = arxiv.Search(query=query, max_results=min(max_results, 20))
    
    papers = []
    for result in search.results():
        papers.append({
            "title": result.title.strip(),
            "authors": [author.name for author in result.authors],
            "summary": result.summary.replace('\n', ' ').strip(),
            "pdf_url": result.pdf_url,
            "paper_id": result.entry_id.split('/')[-1],
            "published": result.published.strftime('%Y-%m-%d')
        })
    
    return {"papers": papers, "query": query, "total_results": len(papers)}

@mcp.tool()
async def save_paper_to_github(paper_id: str, repo_name: str) -> Dict:
    """Save ArXiv paper as GitHub repository (requires authentication)"""
    session_info = validate_mcp_token(mcp.request_context.request)
    github_token = session_info["github_token"]
    
    # Get paper details
    search = arxiv.Search(id_list=[paper_id])
    try:
        paper = next(search.results())
    except StopIteration:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    
    # Create GitHub repository
    async with httpx.AsyncClient() as client:
        repo_response = await client.post(
            "https://api.github.com/user/repos",
            headers={"Authorization": f"Bearer {github_token}"},
            json={
                "name": repo_name,
                "description": f"Research paper: {paper.title}",
                "private": False,
                "auto_init": True
            }
        )
        
        if repo_response.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail="Failed to create repository")
        
        repo_info = repo_response.json()
        
        # Create README
        readme_content = f"""# {paper.title}

## Authors
{chr(10).join([f"- {author.name}" for author in paper.authors])}

## Published
{paper.published.strftime('%Y-%m-%d')}

## Abstract
{paper.summary}

## Links
- [ArXiv]({paper.entry_id})
- [PDF]({paper.pdf_url})

---
*Created by: {session_info['username']}*
"""
        
        await client.put(
            f"https://api.github.com/repos/{repo_info['full_name']}/contents/README.md",
            headers={"Authorization": f"Bearer {github_token}"},
            json={
                "message": "Add paper information",
                "content": base64.b64encode(readme_content.encode()).decode()
            }
        )
        
        return {
            "repository_url": repo_info["html_url"],
            "paper_title": paper.title,
            "created_by": session_info["username"]
        }

@app.get("/")
async def root():
    """Server info"""
    return {
        "server": "MCP Research Assistant",
        "oauth_flow": "Correct MCP OAuth (Resource Server Only)",
        "endpoints": {
            "login": "/login/github",
            "callback": "/auth/callback"
        },
        "tools": ["search_papers", "save_paper_to_github"]
    }

def main():
    """Start the server"""
    mcp.app.mount("/", app)
    mcp.run(transport="http", port=8002)

if __name__ == "__main__":
    main()
