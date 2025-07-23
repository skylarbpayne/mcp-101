# MCP 101: Building Context-Aware AI Agents

A Quarto presentation teaching engineers how to build applications using LLMs with the Model Context Protocol (MCP).

## Quick Start

### Prerequisites
- [Quarto](https://quarto.org/docs/get-started/) installed
- Python 3.10+ with [uv](https://docs.astral.sh/uv/) package manager

### View the Presentation

```bash
quarto preview
```

### Run the Demo

1. **Set up environment variables:**
   ```bash
   # Copy the example environment file
   cp demo/.env.example demo/.env
   ```

2. **Configure API keys in `demo/.env`:**
   - `OPENAI_API_KEY`: Your OpenAI API key (get from [OpenAI Dashboard](https://platform.openai.com/api-keys))
   - `GITHUB_PERSONAL_ACCESS_TOKEN`: GitHub token with gist creation permissions (see setup below)

3. **Install dependencies and run:**
   ```bash
   # Install dependencies
   uv sync

   # Start the MCP server
   uv run demo/server.py

   # In another terminal, run the client
   uv run demo/client.py
   ```

### GitHub Personal Access Token Setup

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a descriptive name (e.g., "MCP 101 Demo")
4. Select the **`gist`** scope (required for creating gists)
5. Click "Generate token"
6. Copy the token and add it to your `demo/.env` file

## What You'll Learn

- Bridge the gap between LLMs and real-world data
- Build MCP servers with tools, resources, and prompts
- Implement authentication and progress tracking
- Navigate the growing MCP ecosystem

## Demo Features

The demo shows ArXiv paper search integrated with GitHub gist creation through MCP.
