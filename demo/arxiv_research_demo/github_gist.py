"""GitHub gist creation with OAuth authentication."""

import os
import webbrowser
import asyncio
from typing import Optional, List
from datetime import datetime

import httpx
from rich.console import Console
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
from arxiv_research_demo.models import ExtractedInfo, GistInfo

console = Console()

# GitHub OAuth configuration
GITHUB_AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com"


class GitHubGistCreator:
    """Handles GitHub OAuth and gist creation."""

    def __init__(self):
        self.access_token: Optional[str] = None
        self._client_id: Optional[str] = None
        self._client_secret: Optional[str] = None

    def _load_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """Lazily load GitHub OAuth credentials from environment variables."""
        if self._client_id is None:
            self._client_id = os.getenv("GITHUB_CLIENT_ID")
        if self._client_secret is None:
            self._client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        return self._client_id, self._client_secret

    async def authenticate(self) -> bool:
        """Perform OAuth authentication with GitHub using authorization code flow."""
        client_id, client_secret = self._load_credentials()
        if not client_id or not client_secret:
            console.print("❌ GitHub OAuth credentials not configured")
            console.print(
                "Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env file"
            )
            return False

        console.print("🔐 Starting GitHub OAuth authentication...")

        # Generate state for security
        import secrets

        state = secrets.token_urlsafe(32)

        # Build authorization URL
        auth_url = (
            f"{GITHUB_AUTHORIZATION_URL}?client_id={client_id}&scope=gist&state={state}"
        )

        console.print(f"🌐 Opening browser for GitHub authorization...")
        console.print(
            f"If the browser doesn't open automatically, please visit: {auth_url}"
        )
        webbrowser.open(auth_url)

        # Set up FastAPI app for OAuth callback
        app = FastAPI()
        callback_event = asyncio.Event()
        authorization_code = None
        received_state = None

        @app.get("/callback")
        async def oauth_callback(request: Request):
            nonlocal authorization_code, received_state
            
            # Debug logging
            console.print(f"🔍 Callback received: {request.url}")
            
            # Get query parameters
            query_params = dict(request.query_params)
            console.print(f"🔍 Query params: {query_params}")

            if "code" in query_params and "state" in query_params:
                authorization_code = query_params["code"]
                received_state = query_params["state"]
                
                console.print(f"🔍 Got authorization code: {authorization_code[:10]}...")
                console.print(f"🔍 Got state: {received_state[:10]}...")

                # Signal that we got the callback
                callback_event.set()
                
                return HTMLResponse(
                    "<html><body><h1>Authorization successful!</h1><p>You can close this window.</p></body></html>"
                )
            else:
                console.print(f"🔍 Missing required parameters in callback")
                return HTMLResponse(
                    "<html><body><h1>Authorization failed!</h1><p>Please try again.</p></body></html>",
                    status_code=400
                )

        # Start FastAPI server in background task
        config = uvicorn.Config(app, host="localhost", port=8000, log_level="error")
        server = uvicorn.Server(config)
        
        # Start server in background
        server_task = asyncio.create_task(server.serve())
        
        console.print("⏳ Waiting for authorization callback...")

        try:
            # Wait for callback with timeout
            await asyncio.wait_for(callback_event.wait(), timeout=300)  # 5 minutes
        except asyncio.TimeoutError:
            console.print("❌ Authorization timed out. Please try again.")
            return False
        finally:
            # Clean shutdown
            server.should_exit = True
            await server_task

        if received_state != state:
            console.print("❌ Invalid state parameter. Possible security issue.")
            return False

        # Exchange authorization code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GITHUB_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": authorization_code,
                    "state": state,
                },
                headers={"Accept": "application/json"},
            )

            if token_response.status_code == 200:
                token_data = token_response.json()

                if "access_token" in token_data:
                    self.access_token = token_data["access_token"]
                    console.print("✅ Authentication successful!")
                    return True
                else:
                    console.print(f"❌ Token exchange failed: {token_data}")
                    return False
            else:
                console.print(f"❌ Token exchange failed: {token_response.status_code}")
                console.print(f"Error: {token_response.text}")
                return False

    async def create_gist(
        self, extracted_info: List[ExtractedInfo], query: str
    ) -> Optional[GistInfo]:
        """Create a GitHub gist with extracted research information."""
        if not self.access_token:
            console.print("❌ Not authenticated. Please authenticate first.")
            return None

        console.print("📝 Creating GitHub gist...")

        # Generate gist content
        gist_content = self._generate_gist_content(extracted_info, query)
        filename = f"arxiv_research_{query.replace(' ', '_')}.md"

        # Create gist payload
        gist_data = {
            "description": f"ArXiv Research Summary: {query}",
            "public": True,
            "files": {filename: {"content": gist_content}},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/gists",
                json=gist_data,
                headers={
                    "Authorization": f"token {self.access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

            if response.status_code == 201:
                gist_response = response.json()

                gist_info = GistInfo(
                    gist_id=gist_response["id"],
                    gist_url=gist_response["html_url"],
                    filename=filename,
                    title=f"ArXiv Research: {query}",
                    created_at=datetime.now(),
                )

                console.print(f"✅ Gist created successfully!")
                console.print(f"🔗 Gist URL: {gist_info.gist_url}")

                return gist_info
            else:
                console.print(f"❌ Gist creation failed: {response.status_code}")
                console.print(f"Error: {response.text}")
                return None

    def _generate_gist_content(
        self, extracted_info: List[ExtractedInfo], query: str
    ) -> str:
        """Generate markdown content for the gist."""
        content = f"""# ArXiv Research Summary: {query}

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Search Query
`{query}`

## Papers Analyzed
Found {len(extracted_info)} relevant papers:

"""

        for i, info in enumerate(extracted_info, 1):
            content += f"""---

## {i}. {info.title}

**Authors:** {", ".join(info.authors)}
**ArXiv ID:** {info.paper_id}
**URL:** {info.arxiv_url}

### Key Findings
"""

            if info.key_findings:
                for finding in info.key_findings:
                    content += f"- {finding}\n"
            else:
                content += "- No key findings extracted\n"

            content += f"""
### Methodology
{info.methodology}

"""

            if info.datasets_used:
                content += "### Datasets Used\n"
                for dataset in info.datasets_used:
                    content += f"- {dataset}\n"
                content += "\n"

            if info.limitations:
                content += "### Limitations\n"
                for limitation in info.limitations:
                    content += f"- {limitation}\n"
                content += "\n"

            if info.future_work:
                content += "### Future Work\n"
                for future in info.future_work:
                    content += f"- {future}\n"
                content += "\n"

        content += """---

## Summary

This research summary was automatically generated using ArXiv search and information extraction.
Each paper's abstract was analyzed to extract key findings, methodology, datasets, limitations, and future work.

For more detailed information, please refer to the original papers using the ArXiv URLs provided above.
"""

        return content
