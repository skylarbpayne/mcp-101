# MCP 101: Building Context-Aware AI Agents

A comprehensive Quarto presentation teaching engineers how to build applications using Large Language Models (LLMs) with the Model Context Protocol (MCP).

## 🎯 Overview

This presentation demonstrates how to bridge the gap between powerful LLMs and real-world data and tools through MCP, moving from isolated AI systems to context-aware agents that can take meaningful action.

## 📚 Contents

- **Presentation**: Interactive reveal.js slides covering MCP fundamentals
- **Demo Project**: Complete ArXiv research assistant implementation
- **Code Examples**: Practical MCP server development patterns

## 🚀 Quick Start

### Prerequisites
- [Quarto](https://quarto.org/docs/get-started/) installed
- Python 3.8+ (for demo code)

### Running the Presentation

```bash
# Clone/navigate to repository
cd mcp-101

# Preview with live reload
quarto preview

# Or render static version
quarto render
```

### Running the Demo

```bash
cd examples/arxiv-server
uv sync
uv run arxiv-server

# In another terminal, run the example client:
uv sync --extra client
uv run python client_example.py
```

## 📖 Presentation Outline

### Part 1: The Dawn of Agentic AI
- Evolution from text generation to real-world action
- The context gap problem
- Why isolated LLMs aren't enough

### Part 2: MCP as the Universal Standard  
- "USB-C for AI" concept
- Architecture: Hosts, Clients, and Servers
- Solving the N×M integration problem

### Part 3: Building the AI Research Assistant
- Scaffolding an ArXiv MCP server
- Tools vs Resources vs Prompts
- Progressive enhancement patterns

### Part 4: Advanced Capabilities
- Progress notifications and logging
- OAuth 2.1 authentication
- Elicitation, Roots, and Sampling

### Part 5: The Growing Ecosystem
- Available MCP servers and tools
- Developer resources and community
- Next steps for builders

## 🛠️ Demo Project Features

The included ArXiv research assistant demonstrates:

- **Paper Search**: Query ArXiv database with structured results
- **Bulk Downloads**: Progress-tracked PDF collection downloads  
- **Resource Access**: Abstract and detail retrieval
- **Workflow Templates**: Reusable analysis prompts
- **Best Practices**: Error handling, logging, security

## 🏗️ Architecture

```
MCP 101 Project
├── index.qmd              # Main presentation
├── _quarto.yml           # Quarto configuration  
├── custom.css           # Presentation styling
├── examples/
│   └── arxiv-server/    # Demo MCP server
│       ├── server.py    # Complete implementation
│       ├── requirements.txt
│       └── README.md
└── README.md           # This file
```

## 🎓 Learning Objectives

After this presentation, participants will:

1. **Understand** the context gap in current AI systems
2. **Grasp** MCP's role as a universal integration standard
3. **Build** a functional MCP server from scratch
4. **Implement** advanced features like authentication and progress tracking
5. **Navigate** the growing MCP ecosystem and resources

## 🌐 Resources

- **MCP Official Docs**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Protocol Specification**: Complete technical reference
- **Community Servers**: [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
- **Developer Tools**: MCP Inspector for debugging
- **Learning**: DeepLearning.AI MCP course

## 🤝 Contributing

This is an educational resource. Contributions welcome:

- Presentation improvements
- Additional code examples  
- Bug fixes and clarifications
- Translation to other languages

## 📄 License

MIT License - Feel free to adapt for your own workshops and presentations.

---

*Built with ❤️ for the MCP community*
