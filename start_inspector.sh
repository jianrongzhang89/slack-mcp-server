#!/bin/bash

# Quick Start Script for MCP Inspector
# This script starts the MCP Inspector with proper environment setup

set -e

echo "🚀 Starting MCP Inspector for Slack MCP Server..."
echo ""

# Check if required environment variables are set
if [[ -z "$SLACK_BOT_TOKEN" ]]; then
    echo "⚠️  Warning: SLACK_BOT_TOKEN not set"
    echo "   Set it with: export SLACK_BOT_TOKEN=xoxb-your-token"
fi

if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "💡 Info: OPENAI_API_KEY not set (optional for enhanced AI features)"
    echo "   Set it with: export OPENAI_API_KEY=your-key"
fi

echo ""
echo "🔧 Make sure the wrapper script exists at ~/bin/mcp-server-everything"
echo "   If not, run: ./setup_inspector.sh"
echo ""

# Ensure ~/bin is in PATH
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo "📍 Adding ~/bin to PATH for this session..."
    export PATH="$HOME/bin:$PATH"
fi

echo "🎯 Starting MCP Inspector..."
echo "   Use the complete URL with session token!"
echo ""

# Start the MCP Inspector
exec npx @modelcontextprotocol/inspector 