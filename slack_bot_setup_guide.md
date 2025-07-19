# Complete Slack Bot Setup Guide

## Why Some Scopes Are Missing

### `users:read` - Should be available
- This scope **is available** for most apps
- Look carefully in the Bot Token Scopes list - it's usually there
- If you can't find it, try scrolling down or typing "users" in the search

### `search:read` - Often restricted 
- This scope requires **special approval** from Slack
- Not available for most standard apps
- **Good news**: Our MCP server now includes a fallback that works without it!

## Step-by-Step Setup Instructions

### 1. Create Your Slack App
1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** 
3. Select **"From scratch"**
4. Name: `MCP Server Bot`
5. Select your workspace
6. Click **"Create App"**

### 2. Add Bot Token Scopes (Essential)

Go to **"OAuth & Permissions"** → **"Scopes"** → **"Bot Token Scopes"**

**Click "Add an OAuth Scope" and add these one by one:**

✅ **Required Scopes (must have):**
```
channels:read          - List public channels
channels:history       - Read public channel messages  
groups:read           - List private channels
groups:history        - Read private channel messages
chat:write            - Send messages
users:read            - Get user information
app_mentions:read     - Receive mentions
im:history            - Read direct messages
mpim:history          - Read group direct messages
```

⚠️ **Optional (if available):**
```
search:read           - Advanced search (often not available)
```

### 3. Enable Socket Mode
1. Go to **"Socket Mode"** in left sidebar
2. Toggle **"Enable Socket Mode"** to **ON**
3. This allows real-time events

### 4. Create App-Level Token
1. Go to **"Basic Information"** 
2. Scroll to **"App-Level Tokens"**
3. Click **"Generate Token and Scopes"**
4. Name: `socket-token`
5. Add scope: `connections:write`
6. Click **"Generate"**
7. **Copy the token** (starts with `xapp-`)

### 5. Enable Event Subscriptions
1. Go to **"Event Subscriptions"**
2. Toggle **"Enable Events"** to **ON**
3. Under **"Subscribe to bot events"**, add:
   - `app_mention` - when someone mentions your bot
   - `message.im` - for direct messages

### 6. Install the App
1. Go to **"OAuth & Permissions"**
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. **Copy the Bot User OAuth Token** (starts with `xoxb-`)

## Set Environment Variables

```bash
# Replace with your actual tokens
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
export SLACK_APP_TOKEN="xapp-your-app-token-here"
```

## Test Your Setup

```bash
# Test the enhanced MCP server
uv run python main_dev.py
```

You should see:
```
Running MCP Development Server with Slack integration...
✅ Slack integration enabled
```

## Invite Your Bot to Channels

In any Slack channel, type:
```
/invite @MCP Server Bot
```

## Test Commands

Once your bot is set up:

1. **List channels**: Mention your bot and ask it to list channels
2. **Get messages**: Ask for recent messages from a channel  
3. **Search**: Search will work using the fallback method (no `search:read` scope needed!)

## Troubleshooting

### "users:read not found"
- Scroll through the entire scopes list
- Try typing "users" in the search box
- This scope should be available for standard apps

### "search:read not available"
- This is normal! Many apps don't get this scope
- Our server now works fine without it
- The fallback search method searches through channel history instead

### "Bot doesn't respond"
- Make sure Socket Mode is enabled
- Check that Event Subscriptions are configured
- Verify your environment variables are set correctly
- Invite the bot to the channel where you're testing

## What Each Scope Does

| Scope | Purpose | Required? |
|-------|---------|-----------|
| `channels:read` | List public channels | ✅ Yes |
| `channels:history` | Read public channel messages | ✅ Yes |
| `groups:read` | List private channels | ✅ Yes |  
| `groups:history` | Read private channel messages | ✅ Yes |
| `chat:write` | Send messages | ✅ Yes |
| `users:read` | Get user information | ✅ Yes |
| `app_mentions:read` | Receive @mentions | ✅ Yes |
| `im:history` | Read direct messages | ✅ Yes |
| `mpim:history` | Read group DMs | ✅ Yes |
| `search:read` | Advanced search API | ⚠️ Optional |

Your MCP server will work perfectly with just the required scopes! 