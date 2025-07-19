#!/bin/bash

# MCP Inspector Setup Script
# This script sets up the wrapper script and starts the MCP Inspector

set -e

echo "🔧 Setting up MCP Inspector for custom server..."

# Get the current directory (project root)
PROJECT_DIR="$(pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
MAIN_DEV="$PROJECT_DIR/main_dev.py"

# Check if we're in the right directory
if [[ ! -f "$MAIN_DEV" ]]; then
    echo "❌ Error: main_dev.py not found in current directory"
    echo "   Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -f "$VENV_PYTHON" ]]; then
    echo "❌ Error: Virtual environment not found at $VENV_PYTHON"
    echo "   Please run 'uv sync' first to create the virtual environment"
    exit 1
fi

# Create ~/bin directory if it doesn't exist
mkdir -p "$HOME/bin"

# Create the wrapper script
WRAPPER_SCRIPT="$HOME/bin/mcp-server-everything"
echo "📝 Creating wrapper script at $WRAPPER_SCRIPT"

cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
# Wrapper script to run custom MCP server
# Note: Set SLACK_BOT_TOKEN and SLACK_APP_TOKEN environment variables before running
cd "$PROJECT_DIR"
exec "$VENV_PYTHON" "$MAIN_DEV" "\$@"
EOF

# Make it executable
chmod +x "$WRAPPER_SCRIPT"

# Check if ~/bin is in PATH
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo "⚠️  Warning: $HOME/bin is not in your PATH"
    echo "   Adding it temporarily for this session..."
    export PATH="$HOME/bin:$PATH"
fi

echo "✅ Wrapper script created successfully!"
echo "📍 Project directory: $PROJECT_DIR"
echo "🐍 Python executable: $VENV_PYTHON"
echo "📄 Main dev script: $MAIN_DEV"
echo ""
echo "⚠️  Important: Make sure to set your environment variables:"
echo "   export SLACK_BOT_TOKEN=your_slack_bot_token"
echo "   export SLACK_APP_TOKEN=your_slack_app_token"
echo "   export OPENAI_API_KEY=your_openai_key  # Optional for enhanced AI features"
echo ""

# Skip wrapper script test (MCP servers don't exit immediately)
echo "✅ Wrapper script created and ready!"
echo ""
echo "🚀 Starting MCP Inspector..."
echo "   The inspector will generate a unique session token"
echo "   Make sure to use the complete URL with the token!"
echo ""

# Start the MCP Inspector
exec npx @modelcontextprotocol/inspector 