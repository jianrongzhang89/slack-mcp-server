# Slack MCP Server

A specialized Model Context Protocol (MCP) server built with fastMCP that provides intelligent Slack integration with AI-powered natural language search capabilities.

## Features

### Slack Integration Tools
- **slack_list_channels**: List all accessible Slack channels
- **slack_get_channel_messages**: Get recent messages from a specific channel
- **slack_search_messages**: Search for messages across channels (with fallback implementation)
- **slack_smart_search**: 🧠 AI-powered natural language search with intelligent query understanding
- **slack_get_user_info**: Get information about a Slack user
- **slack_send_message**: Send a message to a Slack channel

### Development Tools
- **ping_test**: Connection test tool (development server only)

### Resources
- **slack://channels**: List all accessible Slack channels as a resource
- **slack://status**: Check Slack connection status as a resource

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd slack-mcp-server
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Install MCP CLI tools (for development):
   ```bash
   uv add "mcp[cli]"
   ```

4. Install MCP Inspector (for testing):
   ```bash
   npm install -g @modelcontextprotocol/inspector
   ```

5. Set up environment variables:
   ```bash
   # Required for Slack integration
   export SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
   export SLACK_APP_TOKEN=xapp-your-slack-app-token-here
   
   # Optional for enhanced AI features
   export OPENAI_API_KEY=your-openai-api-key-here
   ```

## Usage

### Production Server

Run the production server with fastMCP:

```bash
uv run python main.py
```

### Development Server with MCP Inspector

For development and testing, use the development server (`main_dev.py`) with the MCP Inspector:

#### Quick Setup (Recommended)

Use the provided setup script for automatic configuration:

```bash
# Run the setup script (creates wrapper and starts inspector)
./setup_inspector.sh
```

This script will:
- Create a wrapper script in `~/bin/mcp-server-everything`
- Automatically start the MCP Inspector
- Provide the inspector URL for connecting

#### Manual Setup

If you prefer manual setup:

1. **Set environment variables**:
   ```bash
   export SLACK_BOT_TOKEN=xoxb-your-token-here
   export SLACK_APP_TOKEN=xapp-your-app-token-here
   export OPENAI_API_KEY=your-openai-key-here  # Optional
   ```

2. **Start the development server**:
   ```bash
   uv run python main_dev.py
   ```

3. **In a separate terminal, start the MCP Inspector**:
   ```bash
   npx @modelcontextprotocol/inspector
   ```

4. **Connect to the server**:
   - Use the URL provided by the inspector (includes session token)
   - For local development, typically: `http://localhost:3000`

## Connecting to the Server

The server implements the MCP protocol and can be connected to by any MCP-compatible client. The server will handle:
- Tool discovery and execution
- Resource access
- Proper error handling and responses

### Examples

Once connected through an MCP client, you can use the Slack tools:

- **Basic Slack Operations** (requires SLACK_BOT_TOKEN):
  - List channels: `slack_list_channels()`
  - Get messages: `slack_get_channel_messages("C1234567890", limit=20)`
  - Search messages: `slack_search_messages("deployment", channel_id="C1234567890")`
  - Get user info: `slack_get_user_info("U1234567890")`
  - Send message: `slack_send_message("C1234567890", "Hello from MCP!")`

- **🧠 AI-Powered Smart Search** (enhanced with OPENAI_API_KEY):
  - Natural language search: `slack_smart_search("Show me discussions about deployment from last week")`
  - User-focused search: `slack_smart_search("What did John say about the API changes?")`
  - Topic analysis: `slack_smart_search("Find decisions made about the mobile app")`
  - Sentiment search: `slack_smart_search("Show me concerns people raised about performance")`

### Resources

- **slack://channels**: List all accessible Slack channels as a resource
- **slack://status**: Check Slack connection status as a resource

## Slack Integration Setup

### Step 1: Create a Slack Bot

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Give your app a name and select your workspace
4. Go to "OAuth & Permissions" in the sidebar
5. Add the following **Bot Token Scopes**:
   - `channels:read` (to list channels)
   - `channels:history` (to read channel messages)
   - `groups:read` (to list private channels)
   - `groups:history` (to read private channel messages)
   - `chat:write` (to send messages)
   - `users:read` (to get user information)
   - `app_mentions:read` (to receive mentions)
   - `im:history` (to read direct messages)
   - `mpim:history` (to read group direct messages)
   
   **Note**: `search:read` scope may not be available for all apps. The server includes a fallback search implementation that works without this scope.

### Step 2: Install the Bot

1. Click "Install to Workspace" and authorize the app
2. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
3. Set the environment variable:
   ```bash
   export SLACK_BOT_TOKEN=xoxb-your-token-here
   ```

### Step 3: Invite Bot to Channels

Invite your bot to the channels you want it to access:
```
/invite @your-bot-name
```

### Step 4: Test Integration

Start the server and the Slack tools will be available. The server will show whether Slack integration is enabled on startup.

## AI Features

The smart search functionality has two modes:

### Enhanced Mode (with OpenAI API Key)
- Advanced natural language query understanding
- Intelligent result summarization
- Better handling of synonyms and context
- Smart extraction of time, user, and content filters

### Fallback Mode (without OpenAI API Key)  
- Basic keyword-based search with semantic similarity
- Rule-based query parsing for time/user filters
- Simple result counting

To enable enhanced mode, set your OpenAI API key:
```bash
export OPENAI_API_KEY=your-openai-api-key-here
```

## Security

- All Slack tools validate inputs and handle exceptions gracefully
- Slack integration requires proper OAuth token setup with appropriate scopes
- Slack API calls are rate-limited and include comprehensive error handling
- AI search functionality respects Slack permissions and channel access
- Bot tokens are securely managed through environment variables
- No sensitive data is stored or logged

## Development

To extend this Slack-focused server:

1. Add new Slack tools using the `@mcp.tool()` decorator
2. Add new Slack resources using the `@mcp.resource()` decorator
3. Enhance AI search capabilities in `ai_search.py`
4. Ensure proper error handling and type hints
5. Test with an MCP client or the MCP Inspector

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with real Slack data
5. Submit a pull request

## License

MIT License
