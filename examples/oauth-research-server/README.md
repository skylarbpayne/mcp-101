# MCP OAuth Research Assistant - Simple Demo

A simple demonstration of the **correct** MCP OAuth flow where the MCP server acts as a Resource Server only.

## 🎯 What This Shows

- ✅ **Correct MCP OAuth** - MCP server = Resource Server only
- ✅ **GitHub Authentication** - GitHub = Authorization Server  
- ✅ **Internal Tokens** - MCP tokens bound to GitHub sessions
- ✅ **Simple Flow** - Browser login, no complex client registration

## 🚀 Quick Start

1. **Configure GitHub OAuth App**:
   - Create at https://github.com/settings/applications/new
   - Callback URL: `http://localhost:8002/auth/callback`
   - Update `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in `server.py`

2. **Install dependencies**:
   ```bash
   pip install mcp fastapi uvicorn httpx arxiv PyJWT
   ```

3. **Run the server**:
   ```bash
   python server.py
   ```

4. **Run the demo**:
   ```bash
   python client_demo.py
   ```

## 📋 Demo Flow

1. **Client** needs authenticated action → gets 401 from MCP server
2. **Browser** opens to MCP server's `/login/github` 
3. **MCP server** redirects to GitHub OAuth
4. **User** authenticates with GitHub
5. **GitHub** sends callback to MCP server
6. **MCP server** creates internal JWT token bound to GitHub session
7. **User** copies internal token to client
8. **Client** uses internal token for API calls
9. **MCP server** validates token and uses stored GitHub token for GitHub API

## 🔧 Files

- `server.py` - MCP server with correct OAuth (Resource Server only)
- `client_demo.py` - Simple client demonstrating the flow
- `pyproject.toml` - Dependencies

## 🎯 Key Points

- **No OAuth AS endpoints** - MCP server doesn't implement `/.well-known/oauth-authorization-server`
- **Internal tokens only** - Clients never see GitHub tokens directly
- **Simple user flow** - Just browser login, no complex client registration
- **Follows MCP spec** - As described in Auth0's MCP OAuth blog post

This demonstrates the **actual** MCP OAuth capabilities, not a non-compliant implementation.
