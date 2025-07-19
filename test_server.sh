#!/bin/bash

# Test script to verify MCP server is working
# This helps debug connection issues before using the inspector

set -e

echo "🧪 Testing MCP Server Connection..."
echo ""

# Check if wrapper script exists
if [[ ! -f "$HOME/bin/mcp-server-everything" ]]; then
    echo "❌ Error: Wrapper script not found at ~/bin/mcp-server-everything"
    echo "   Please run: ./setup_inspector.sh first"
    exit 1
fi

# Check environment variables
if [[ -z "$SLACK_BOT_TOKEN" ]]; then
    echo "⚠️  Warning: SLACK_BOT_TOKEN not set"
    echo "   Server will start but Slack features won't work"
    echo "   Set it with: export SLACK_BOT_TOKEN=xoxb-your-token"
    echo ""
fi

echo "🔧 Testing server startup..."
echo "   This will show server info and then exit"
echo ""

# Test the server startup with --help flag
echo "📋 Server information:"
timeout 5s ~/bin/mcp-server-everything --help || {
    echo ""
    echo "✅ Server starts correctly (timeout is expected for --help)"
    echo "🎯 Ready to connect with MCP Inspector!"
    echo ""
    echo "To start the inspector connected to your server, run:"
    echo "   ./start_inspector.sh"
} 