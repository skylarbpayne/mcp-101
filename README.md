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

```bash
# Install dependencies
uv sync

# Start the MCP server
uv run python demo/server.py

# In another terminal, run the client
uv run python demo/client.py
```

## What You'll Learn

- Bridge the gap between LLMs and real-world data
- Build MCP servers with tools, resources, and prompts
- Implement authentication and progress tracking
- Navigate the growing MCP ecosystem

## Demo Features

The demo shows ArXiv paper search integrated with GitHub gist creation through MCP.
