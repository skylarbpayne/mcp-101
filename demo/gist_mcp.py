import httpx
import os
from fastmcp import FastMCP
from dotenv import load_dotenv
import uvicorn

load_dotenv()

GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")

mcp = FastMCP("Gist Creator")

@mcp.tool(
    name="create_gist",
    description="Create a GitHub Gist using the configured personal access token.",
)
async def create_github_gist(title: str, body: str, description: str = "", public: bool = True):
    """
    Create a GitHub Gist.

    Args:
        title: the title of the file
        body: the content of the file
        description (str): Description of the gist.
        public (bool): Whether the gist is public.

    Returns:
        dict: The created gist's JSON response.
    """
    url = "https://api.github.com/gists"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    payload = {
        "description": description,
        "public": public,
        "files": {title: {"content": body}}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    uvicorn.run(mcp.http_app(), host="0.0.0.0", port=8000)