# OAuth Research Server

A complete MCP OAuth 2.1 demonstration with GitHub integration, showing how to properly implement OAuth authentication for MCP servers.

## Features

- ✅ **OAuth 2.1 + PKCE**: Full OAuth implementation with security best practices
- ✅ **GitHub Integration**: Real OAuth with GitHub API for repository management
- ✅ **Dynamic Client Registration**: Automatic client registration per MCP spec
- ✅ **Metadata Discovery**: OAuth server metadata endpoint
- ✅ **Protected Tools**: MCP tools that require OAuth authentication
- ✅ **Token Management**: Proper token storage and validation

## Architecture

```
MCP Client → OAuth Server → GitHub OAuth → GitHub API
     ↓            ↓              ↓            ↓
  1. Register   2. Get Auth   3. User      4. Access
     Client        Code         Login       Protected
                                           Resources
```

## Setup

### 1. GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Create a new OAuth App with:
   - **Application name**: `MCP OAuth Demo`
   - **Homepage URL**: `http://localhost:8002`
   - **Authorization callback URL**: `http://localhost:8002/oauth/callback`
3. Note the Client ID and Client Secret

### 2. Environment Variables

```bash
export GITHUB_CLIENT_ID="your_github_client_id"
export GITHUB_CLIENT_SECRET="your_github_client_secret"
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Start the OAuth Server

```bash
python oauth_server.py
```

The server will run on `http://localhost:8002` and provide:

- **OAuth Metadata**: `/.well-known/oauth-authorization-server`
- **Client Registration**: `/oauth/register`
- **Authorization**: `/oauth/authorize`
- **Token Exchange**: `/oauth/token`
- **Protected MCP Tools**: Require Bearer token

### Run the OAuth Demo

```bash
python oauth_client_demo.py
```

This demonstrates the complete OAuth flow:

1. **Metadata Discovery**: Client discovers OAuth endpoints
2. **Client Registration**: Dynamic registration with MCP server
3. **Authorization**: PKCE flow with GitHub OAuth
4. **Token Exchange**: Get MCP access token
5. **Protected API Calls**: Use GitHub API via MCP tools

## OAuth Flow Details

### 1. Dynamic Client Registration

```python
POST /oauth/register
{
    "client_name": "MCP OAuth Demo Client",
    "redirect_uris": ["http://localhost:8003/callback"],
    "scope": "repo"
}
```

### 2. Authorization with PKCE

```python
GET /oauth/authorize?
    response_type=code&
    client_id=CLIENT_ID&
    redirect_uri=REDIRECT_URI&
    scope=repo&
    code_challenge=CODE_CHALLENGE&
    code_challenge_method=S256
```

### 3. Token Exchange

```python
POST /oauth/token
{
    "grant_type": "authorization_code",
    "code": "AUTH_CODE",
    "redirect_uri": "REDIRECT_URI",
    "client_id": "CLIENT_ID",
    "code_verifier": "CODE_VERIFIER"
}
```

### 4. Protected MCP Tool Call

```python
POST /mcp/tools/save_paper_to_github
Authorization: Bearer ACCESS_TOKEN
{
    "paper_title": "Research Paper",
    "paper_content": "Abstract...",
    "repo_name": "research-repo"
}
```

## MCP Tools

### `search_papers_mock(query, max_results=5)`
- **Auth**: None required
- **Description**: Mock paper search for demonstration
- **Returns**: List of papers matching query

### `save_paper_to_github(paper_title, paper_content, repo_name)`
- **Auth**: OAuth required (scope: repo)
- **Description**: Save research paper as GitHub repository
- **Returns**: Repository information and creation status

### `list_research_repositories()`
- **Auth**: OAuth required (scope: repo)
- **Description**: List all user's GitHub repositories
- **Returns**: List of repositories with metadata

## Security Features

- **PKCE**: Prevents authorization code interception
- **State Parameter**: Prevents CSRF attacks
- **Token Expiration**: Access tokens expire after 1 hour
- **Scope Validation**: Tools check required OAuth scopes
- **Bearer Token**: Proper authorization header handling

## Development

### Testing OAuth Flow

1. Start server: `python oauth_server.py`
2. Test metadata: `curl http://localhost:8002/.well-known/oauth-authorization-server`
3. Run client demo: `python oauth_client_demo.py`

### Debugging

- Enable verbose logging in FastAPI
- Check GitHub OAuth app settings
- Verify environment variables are set
- Test GitHub API access manually

## Production Considerations

- Use proper database for token storage
- Implement token refresh
- Add rate limiting
- Use HTTPS in production
- Store client secrets securely
- Add proper logging and monitoring
