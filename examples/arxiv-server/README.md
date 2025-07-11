# ArXiv MCP Server

A demonstration Model Context Protocol (MCP) server that provides access to the ArXiv scientific paper database. Built for the MCP 101 presentation.

## Features

- **Search Papers**: Find scientific papers by query with customizable result limits
- **Download Collections**: Bulk download papers with real-time progress tracking
- **Paper Details**: Get comprehensive information about specific papers
- **Abstract Access**: Quick access to paper abstracts
- **Analysis Workflow**: Built-in prompt for structured paper analysis

## Setup

### Prerequisites
- Python 3.8+ 
- uv (recommended) or pip

### Installation

```bash
# Clone or navigate to this directory
cd examples/arxiv-server

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv add -r requirements.txt
```

### Running the Server

```bash
# For local development (stdio transport)
uv run python server.py

# For remote access (HTTP transport)
# Uncomment the HTTP transport lines in server.py, then:
uv run python server.py
```

### Testing with MCP Inspector

```bash
# In another terminal
uv run mcp dev server.py
```

## Available Capabilities

### Tools

1. **search_papers(query, max_results=5)**
   - Search ArXiv for papers matching the query
   - Returns structured paper data with titles, authors, abstracts, URLs

2. **download_paper_collection(query, max_papers=10)**
   - Download multiple papers based on search query
   - Demonstrates progress notifications for long-running operations
   - Creates local PDF files in `./downloads/` directory

### Resources

1. **arxiv/{paper_id}**
   - Get detailed information about a specific paper
   - Includes title, authors, abstract, categories, URLs

2. **arxiv/{paper_id}/abstract**
   - Get just the abstract of a specific paper
   - Useful for quick content preview

### Prompts

1. **analyze_paper**
   - Structured workflow for comprehensive paper analysis
   - Guides users through systematic paper evaluation

## Example Usage

### Search for Papers
```python
# Find papers on transformer models
result = search_papers("transformer neural networks", max_results=10)
```

### Get Paper Details
```python
# Get details for a specific paper
details = get_paper_details("2301.07041")
```

### Download Paper Collection
```python
# Download papers with progress tracking
result = download_paper_collection("quantum computing", max_papers=5)
```

## Integration with MCP Clients

This server can be used with any MCP-compatible client:

- **Claude Desktop**: Add to MCP configuration
- **Cursor IDE**: Configure as MCP server
- **Custom Applications**: Connect via JSON-RPC 2.0

### Configuration Example

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "arxiv": {
      "command": "python",
      "args": ["path/to/server.py"],
      "transport": "stdio"
    }
  }
}
```

## Architecture Notes

- Built with FastMCP for rapid development
- Uses ArXiv's official Python library
- Implements MCP best practices:
  - Proper error handling
  - Progress notifications for long operations
  - Structured logging
  - Resource URI schemes
  - Tool/Resource separation

## Security Considerations

- No authentication required (ArXiv is public)
- Rate limiting recommended for production use
- File downloads are restricted to `./downloads/` directory
- Input validation on all parameters