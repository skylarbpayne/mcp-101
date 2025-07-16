# ArXiv Research Demo

A comprehensive demo that combines ArXiv paper search, information extraction, and GitHub gist creation with OAuth authentication.

## Features

🔍 **ArXiv Search**: Search for scientific papers using the ArXiv API
📋 **Information Extraction**: Extract key findings, methodology, datasets, and limitations from paper abstracts
🔐 **GitHub OAuth**: Secure authentication with GitHub using device flow
📝 **Gist Creation**: Automatically create GitHub gists with extracted research summaries

## Setup

### Prerequisites

- Python 3.8+
- uv (for dependency management)
- GitHub account with OAuth app configured

### GitHub OAuth App Setup

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Create a new OAuth App with:
   - **Application name**: `ArXiv Research Demo`
   - **Homepage URL**: `http://localhost:8000`
   - **Authorization callback URL**: `http://localhost:8000/callback` (not used in device flow)
3. Note the Client ID and Client Secret

### Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your GitHub OAuth credentials:
   ```
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   ```

### Install Dependencies

```bash
cd demo
uv sync
```

## Usage

### Basic Usage

Search for papers and create a GitHub gist:

```bash
uv run demo.py "quantum computing"
```

### Advanced Usage

```bash
# Search with specific number of papers
uv run demo.py "machine learning" --max-papers 10

# Test without creating gist (dry run)
uv run demo.py "neural networks" --dry-run

# Skip authentication for testing
uv run demo.py "artificial intelligence" --skip-auth
```

### Command Line Options

- `query`: Search query for ArXiv papers (required)
- `--max-papers`: Maximum number of papers to analyze (default: 5)
- `--skip-auth`: Skip GitHub authentication (for testing)
- `--dry-run`: Don't create gist, just show extracted info

## What the Demo Does

1. **🔍 Search ArXiv**: Uses the ArXiv API to find relevant papers based on your query
2. **📋 Extract Information**: Analyzes paper abstracts to extract:
   - Key findings and results
   - Methodology and approach
   - Datasets used
   - Limitations mentioned
   - Future work suggestions
3. **🔐 Authenticate**: Uses GitHub device flow for secure authentication
4. **📝 Create Gist**: Generates a formatted markdown gist with all extracted information

## Example Output

When you run the demo, you'll see:

```
🚀 Starting ArXiv Research Demo
📋 Query: quantum computing
📊 Max papers: 5

🔍 Searching ArXiv for: quantum computing
✅ Found 5 papers

📄 Found Papers:
┌─────────────┬──────────────────────────────────────────────────────────┬─────────────────────────┬──────────────┐
│ ID          │ Title                                                    │ Authors                 │ Published    │
├─────────────┼──────────────────────────────────────────────────────────┼─────────────────────────┼──────────────┤
│ 2401.12345  │ Quantum Computing Advances in Error Correction...       │ Smith, J., Doe, J.      │ 2024-01-15   │
└─────────────┴──────────────────────────────────────────────────────────┴─────────────────────────┴──────────────┘

📋 Extracting info from: Quantum Computing Advances in Error...
...

📝 Creating GitHub gist...
✅ Gist created successfully!
🔗 Gist URL: https://gist.github.com/username/abc123...

🎉 Demo completed successfully!
```

## Architecture

The demo is organized into modular components:

```
demo/
├── __init__.py           # Package initialization
├── models.py             # Pydantic data models
├── arxiv_search.py       # ArXiv search functionality
├── extractor.py          # Information extraction logic
├── github_gist.py        # GitHub OAuth and gist creation
├── demo.py               # Main demo script
├── pyproject.toml        # Project configuration
├── .env.example          # Environment variables template
└── README.md            # This file
```

## Information Extraction

The extractor uses pattern matching to identify:

- **Key Findings**: Sentences containing result indicators ("we show", "we find", "our results demonstrate")
- **Methodology**: Approaches, methods, and techniques used
- **Datasets**: Named datasets, corpora, and benchmarks
- **Limitations**: Explicit limitations and constraints mentioned
- **Future Work**: Planned next steps and future research directions

## Security Features

- **GitHub Device Flow**: Secure authentication for CLI applications
- **Environment Variables**: Sensitive credentials stored securely
- **Token Handling**: Proper access token management
- **Scope Limitation**: Only requests necessary GitHub permissions (gist creation)

## Development

### Testing

Test the demo with different queries:

```bash
# Test with dry run
uv run demo.py "transformer models" --dry-run

# Test without auth
uv run demo.py "deep learning" --skip-auth
```

### Extending the Demo

To add new features:

1. **New Extractors**: Add extraction methods to `extractor.py`
2. **Different Outputs**: Modify `github_gist.py` to support other platforms
3. **Enhanced Search**: Extend `arxiv_search.py` with additional filters
4. **AI Integration**: Add LLM-based extraction for better results

## Troubleshooting

### Common Issues

**Authentication Failed**:
- Check your GitHub OAuth app configuration
- Ensure environment variables are set correctly
- Verify you have internet connectivity
- Try authenticating again if the device code expires

**No Papers Found**:
- Try broader search terms
- Check ArXiv API status
- Verify network connectivity

**Gist Creation Failed**:
- Ensure you have gist creation permissions
- Check GitHub API status
- Verify OAuth token is valid

### Debug Mode

Enable verbose output by setting:
```bash
export PYTHONPATH=.
uv run python -m demo.demo --help
```

## License

This project is part of the MCP 101 presentation materials.
