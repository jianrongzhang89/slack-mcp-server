#!/usr/bin/env python3
"""
A simple MCP server implementation using fastMCP.
This server provides basic tools for file operations, system information, calculations, and Slack integration.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastmcp import FastMCP
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from ai_search import search_engine

# Debug logging (disabled for production)
# import logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the MCP server
mcp = FastMCP("Simple MCP Server")

# Global Slack client - initialized when needed
_slack_client = None

def get_slack_client() -> Optional[WebClient]:
    """Get initialized Slack client."""
    global _slack_client
    if _slack_client is None:
        token = os.getenv('SLACK_BOT_TOKEN')
        if not token:
            return None
        _slack_client = WebClient(token=token)
    return _slack_client







@mcp.tool()
def slack_list_channels() -> str:
    """List all Slack channels the bot has access to."""
    client = get_slack_client()
    if not client:
        return "Error: Slack client not initialized. Please set SLACK_BOT_TOKEN environment variable."
    
    try:
        # Get public channels
        result = client.conversations_list(types="public_channel,private_channel")
        channels = result["channels"]
        
        if not channels:
            return "No channels found or bot doesn't have access to any channels."
        
        output = "Available Slack channels:\n"
        for channel in channels:
            channel_type = "🔒" if channel["is_private"] else "📢"
            member_count = channel.get("num_members", "?")
            output += f"{channel_type} #{channel['name']} (ID: {channel['id']}, Members: {member_count})\n"
        
        return output
    except SlackApiError as e:
        return f"Slack API error: {e.response['error']}"
    except Exception as e:
        return f"Error listing channels: {str(e)}"

@mcp.tool()
def slack_get_channel_messages(channel_id: str, limit: int = 10) -> str:
    """Get recent messages from a Slack channel."""
    client = get_slack_client()
    if not client:
        return "Error: Slack client not initialized. Please set SLACK_BOT_TOKEN environment variable."
    
    try:
        # Limit to reasonable number of messages
        limit = min(limit, 50)
        
        # Get channel info first
        channel_info = client.conversations_info(channel=channel_id)
        channel_name = channel_info["channel"]["name"]
        
        # Get messages
        result = client.conversations_history(channel=channel_id, limit=limit)
        messages = result["messages"]
        
        if not messages:
            return f"No messages found in #{channel_name}."
        
        output = f"Recent messages from #{channel_name} (showing {len(messages)} messages):\n\n"
        
        for msg in reversed(messages):  # Show oldest first
            timestamp = datetime.fromtimestamp(float(msg["ts"])).strftime("%Y-%m-%d %H:%M:%S")
            user_id = msg.get("user", "Unknown")
            text = msg.get("text", "")
            
            # Get user info if possible
            try:
                user_info = client.users_info(user=user_id)
                username = user_info["user"]["real_name"] or user_info["user"]["name"]
            except:
                username = user_id
            
            # Handle different message types
            if msg.get("subtype") == "bot_message":
                username = msg.get("bot_id", "Bot")
            
            output += f"[{timestamp}] {username}: {text}\n"
            
            # Add thread info if it's a thread
            if msg.get("thread_ts"):
                output += "  └─ (part of thread)\n"
        
        return output
    except SlackApiError as e:
        return f"Slack API error: {e.response['error']}"
    except Exception as e:
        return f"Error getting messages: {str(e)}"

@mcp.tool()
def slack_search_messages(query: str, channel_id: Optional[str] = None, limit: int = 10) -> str:
    """Search for messages in Slack channels (fallback implementation without search:read scope)."""
    client = get_slack_client()
    if not client:
        return "Error: Slack client not initialized. Please set SLACK_BOT_TOKEN environment variable."
    
    try:
        # Limit to reasonable number of results
        limit = min(limit, 20)
        
        # If no specific channel, search across accessible channels
        if channel_id:
            channels_to_search = [channel_id]
        else:
            # Get list of channels the bot has access to
            try:
                channels_result = client.conversations_list(types="public_channel,private_channel", limit=20)
                channels_to_search = [ch["id"] for ch in channels_result["channels"]]
            except:
                return "Error: Unable to access channels. Bot needs to be invited to channels."
        
        matches = []
        query_lower = query.lower()
        
        # Search through channel histories
        for ch_id in channels_to_search:
            try:
                # Get channel name
                channel_info = client.conversations_info(channel=ch_id)
                channel_name = channel_info["channel"]["name"]
                
                # Get recent messages from this channel
                result = client.conversations_history(channel=ch_id, limit=50)
                messages = result["messages"]
                
                # Search for query in messages
                for msg in messages:
                    text = msg.get("text", "").lower()
                    if query_lower in text:
                        # Get user info
                        user_id = msg.get("user", "Unknown")
                        try:
                            user_info = client.users_info(user=user_id)
                            username = user_info["user"]["real_name"] or user_info["user"]["name"]
                        except:
                            username = user_id
                        
                        matches.append({
                            "timestamp": msg["ts"],
                            "channel": channel_name,
                            "username": username,
                            "text": msg.get("text", "")
                        })
                        
                        if len(matches) >= limit:
                            break
                            
            except SlackApiError as api_error:
                # Skip channels we don't have access to
                continue
            except Exception:
                # Skip any other errors for individual channels
                continue
            
            if len(matches) >= limit:
                break
        
        if not matches:
            return f"No messages found matching '{query}'. Note: Bot can only search channels it has been invited to."
        
        output = f"Search results for '{query}' (showing {len(matches)} results):\n\n"
        
        # Sort by timestamp (newest first)
        matches.sort(key=lambda x: float(x["timestamp"]), reverse=True)
        
        for match in matches:
            timestamp = datetime.fromtimestamp(float(match["timestamp"])).strftime("%Y-%m-%d %H:%M:%S")
            output += f"[{timestamp}] #{match['channel']} - {match['username']}: {match['text']}\n\n"
        
        return output
    except SlackApiError as e:
        if e.response['error'] == 'missing_scope':
            return f"Error: Missing required scope. Bot needs 'search:read' scope for advanced search, using fallback method."
        return f"Slack API error: {e.response['error']}"
    except Exception as e:
        return f"Error searching messages: {str(e)}"

@mcp.tool()
def slack_get_user_info(user_id: str) -> str:
    """Get information about a Slack user."""
    client = get_slack_client()
    if not client:
        return "Error: Slack client not initialized. Please set SLACK_BOT_TOKEN environment variable."
    
    try:
        result = client.users_info(user=user_id)
        user = result["user"]
        
        output = f"User Information for {user['name']}:\n"
        output += f"Real Name: {user.get('real_name', 'N/A')}\n"
        output += f"Display Name: {user.get('profile', {}).get('display_name', 'N/A')}\n"
        output += f"Email: {user.get('profile', {}).get('email', 'N/A')}\n"
        output += f"Title: {user.get('profile', {}).get('title', 'N/A')}\n"
        output += f"Status: {user.get('profile', {}).get('status_text', 'N/A')}\n"
        output += f"Is Bot: {user.get('is_bot', False)}\n"
        output += f"Is Admin: {user.get('is_admin', False)}\n"
        output += f"Timezone: {user.get('tz', 'N/A')}\n"
        
        return output
    except SlackApiError as e:
        return f"Slack API error: {e.response['error']}"
    except Exception as e:
        return f"Error getting user info: {str(e)}"

@mcp.tool()
def slack_send_message(channel_id: str, text: str) -> str:
    """Send a message to a Slack channel."""
    client = get_slack_client()
    if not client:
        return "Error: Slack client not initialized. Please set SLACK_BOT_TOKEN environment variable."
    
    try:
        result = client.chat_postMessage(channel=channel_id, text=text)
        return f"Message sent successfully to channel {channel_id}. Message timestamp: {result['ts']}"
    except SlackApiError as e:
        return f"Slack API error: {e.response['error']}"
    except Exception as e:
        return f"Error sending message: {str(e)}"

@mcp.tool()
def slack_smart_search(query: str, channel_id: Optional[str] = None, max_results: int = 10, include_summary: bool = True) -> str:
    """
    Search Slack messages using natural language queries with AI-powered understanding.
    
    Examples:
    - "Show me discussions about deployment from last week"
    - "What did John say about the API changes?"
    - "Find decisions made about the mobile app"
    - "Show me concerns people raised about performance"
    """
    client = get_slack_client()
    if not client:
        return "Error: Slack client not initialized. Please set SLACK_BOT_TOKEN environment variable."
    
    try:
        # Parse natural language query
        search_params = search_engine.parse_natural_query(query)
        
        # Determine channels to search
        if channel_id:
            channels_to_search = [channel_id]
        else:
            # Get accessible channels
            try:
                channels_result = client.conversations_list(types="public_channel,private_channel", limit=20)
                channels_to_search = [ch["id"] for ch in channels_result["channels"]][:10]  # Limit for performance
            except:
                return "Error: Unable to access channels. Bot needs to be invited to channels."
        
        # Collect messages from channels
        all_messages = []
        channel_names = {}
        
        for ch_id in channels_to_search:
            try:
                # Get channel info
                channel_info = client.conversations_info(channel=ch_id)
                channel_name = channel_info["channel"]["name"]
                channel_names[ch_id] = channel_name
                
                # Get messages (more for better search results)
                result = client.conversations_history(channel=ch_id, limit=100)
                messages = result["messages"]
                
                # Add channel context to messages
                for msg in messages:
                    msg['channel_id'] = ch_id
                    msg['channel_name'] = channel_name
                
                all_messages.extend(messages)
                
            except SlackApiError:
                # Skip channels we don't have access to
                continue
            except Exception:
                # Skip any other errors for individual channels
                continue
        
        if not all_messages:
            return f"No messages found. Bot may need to be invited to channels first."
        
        # Apply time filtering
        if search_params.time_filter:
            all_messages = search_engine.filter_by_time(all_messages, search_params.time_filter)
        
        # Apply user filtering
        if search_params.user_filter:
            all_messages = search_engine.filter_by_user(all_messages, search_params.user_filter, client)
        
        # Perform semantic search
        search_query = ' '.join(search_params.keywords) if search_params.keywords else query
        results = search_engine.semantic_search(search_query, all_messages, max_results)
        
        if not results:
            return f"No messages found matching '{query}'. Try different keywords or check if bot has access to relevant channels."
        
        # Format results intelligently
        output = f"🔍 **Smart Search Results for**: '{query}'\n"
        output += f"📊 Found {len(results)} relevant messages"
        
        if search_params.time_filter:
            output += f" from {search_params.time_filter}"
        if search_params.user_filter:
            output += f" by {search_params.user_filter}"
        
        output += f"\n\n"
        
        # Add AI summary if requested
        if include_summary and len(results) > 1:
            summary = search_engine.generate_summary(results, query)
            output += f"💡 **Summary**: {summary}\n\n"
        
        # Show search parameters if extracted
        if any([search_params.time_filter, search_params.user_filter, search_params.content_type]):
            output += "🎯 **Detected filters**: "
            filters = []
            if search_params.time_filter:
                filters.append(f"Time: {search_params.time_filter}")
            if search_params.user_filter:
                filters.append(f"User: {search_params.user_filter}")
            if search_params.content_type:
                filters.append(f"Type: {search_params.content_type}")
            output += ", ".join(filters) + "\n\n"
        
        # Show results
        output += "📝 **Messages**:\n"
        for i, result in enumerate(results[:max_results], 1):
            msg = result['message']
            score = result.get('score', 0)
            match_reason = result.get('match_reason', '')
            
            timestamp = datetime.fromtimestamp(float(msg["ts"])).strftime("%Y-%m-%d %H:%M")
            channel = msg.get('channel_name', 'Unknown')
            user_id = msg.get("user", "Unknown")
            text = msg.get("text", "")[:300] + ("..." if len(msg.get("text", "")) > 300 else "")
            
            # Get user info
            try:
                user_info = client.users_info(user=user_id)
                username = user_info["user"]["real_name"] or user_info["user"]["name"]
            except:
                username = user_id
            
            output += f"\n**{i}.** [{timestamp}] **#{channel}** - {username}\n"
            output += f"    {text}\n"
            if match_reason:
                output += f"    🎯 *{match_reason}*\n"
        
        if len(results) > max_results:
            output += f"\n📎 *{len(results) - max_results} more results available*"
        
        return output
        
    except Exception as e:
        return f"Error in smart search: {str(e)}"





@mcp.resource("slack://{resource_type}")
def get_slack_resource(resource_type: str) -> str:
    """Get Slack information as a resource."""
    if resource_type == "channels":
        return slack_list_channels()
    elif resource_type == "status":
        client = get_slack_client()
        if client:
            return "Slack client initialized and ready"
        else:
            return "Slack client not initialized - set SLACK_BOT_TOKEN"
    else:
        return f"Unknown Slack resource type: {resource_type}"

def main():
    """Run the MCP server."""
    print("Starting Simple MCP Server with Slack integration...")
    print(f"Server name: {mcp.name}")
    print("Available tools:")
    print("  - slack_list_channels")
    print("  - slack_get_channel_messages")
    print("  - slack_search_messages")
    print("  - slack_smart_search (🧠 AI-powered natural language search)")
    print("  - slack_get_user_info")
    print("  - slack_send_message")
    
    # Check Slack configuration
    if os.getenv('SLACK_BOT_TOKEN'):
        print("✅ Slack integration enabled")
    else:
        print("⚠️  Slack integration disabled - set SLACK_BOT_TOKEN environment variable")
    
    print("\nServer is running. Connect using MCP client.")
    
    try:
        # Run the server
        mcp.run()
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
    except KeyboardInterrupt:
        print("Server stopped by user")

if __name__ == "__main__":
    main()
