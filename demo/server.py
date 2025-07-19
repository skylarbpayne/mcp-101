from fastmcp import FastMCP
from gist_mcp import mcp as gist_mcp
import uvicorn

arxiv_mcp = FastMCP.as_proxy({
    "mcpServers": {
        # We can use off the shelf MCP servers
        "arxiv-mcp-server": {
            "command": "uv",
            "args": [
                "tool",
                "run",
                "arxiv-mcp-server",
                "--storage-path", ".tmp/arxiv-mcp-server"
            ]
        }
    }
})

mcp = FastMCP("My MCP Server")

# You can mount multiple servers together for composition
mcp.mount(arxiv_mcp)
# this is an example of a custom MCP server -- see gist_mcp.py
mcp.mount(gist_mcp)

if __name__ == "__main__":
    # NOTE: sse is deprecated. However, Mirascope has not updated to support the new HTTP transport yet.
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=8000)