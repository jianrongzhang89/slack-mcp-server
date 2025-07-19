"""
AI-powered natural language search for Slack messages.
Implements semantic search, query parsing, and intelligent result formatting.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from dateutil.parser import parse as parse_date
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# AI/ML imports
try:
    import openai
    from sentence_transformers import SentenceTransformer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

@dataclass
class SearchParams:
    """Structured search parameters extracted from natural language."""
    keywords: List[str]
    time_filter: Optional[str] = None
    user_filter: Optional[str] = None
    content_type: Optional[str] = None
    sentiment: Optional[str] = None
    channel_hints: List[str] = None
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SearchParams':
        """Create SearchParams from JSON string."""
        try:
            data = json.loads(json_str)
            return cls(**data)
        except:
            # Fallback if JSON parsing fails
            return cls(keywords=[json_str])

class NaturalLanguageSearchEngine:
    """AI-powered search engine for Slack messages."""
    
    def __init__(self):
        self.openai_client = None
        self.embedding_model = None
        self.embeddings_cache = {}
        
        # Initialize AI components if available
        if AI_AVAILABLE:
            self._init_ai_components()
    
    def _init_ai_components(self):
        """Initialize AI components (OpenAI, embeddings)."""
        try:
            # Initialize OpenAI client
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
            
            # Initialize local embedding model as fallback
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"Warning: Could not load embedding model: {e}")
                
        except Exception as e:
            print(f"Warning: AI initialization failed: {e}")
    
    def parse_natural_query(self, query: str) -> SearchParams:
        """Parse natural language query into structured search parameters."""
        
        if self.openai_client:
            return self._parse_with_llm(query)
        else:
            return self._parse_with_rules(query)
    
    def _parse_with_llm(self, query: str) -> SearchParams:
        """Use LLM to parse natural language query."""
        
        prompt = f"""
        Parse this Slack search query and extract structured search parameters:
        Query: "{query}"
        
        Extract and return ONLY a valid JSON object with these fields:
        {{
            "keywords": ["main", "search", "terms"],
            "time_filter": "last week" or "yesterday" or null,
            "user_filter": "John" or "team lead" or null,
            "content_type": "decisions" or "questions" or "issues" or null,
            "sentiment": "concerned" or "excited" or null,
            "channel_hints": ["channel-name"] or []
        }}
        
        Return ONLY the JSON, no other text.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            json_str = response.choices[0].message.content.strip()
            # Clean up the response to ensure it's valid JSON
            json_str = re.sub(r'^```json\s*', '', json_str)
            json_str = re.sub(r'\s*```$', '', json_str)
            
            return SearchParams.from_json(json_str)
            
        except Exception as e:
            print(f"LLM parsing failed: {e}")
            return self._parse_with_rules(query)
    
    def _parse_with_rules(self, query: str) -> SearchParams:
        """Parse query using rule-based approach as fallback."""
        
        keywords = []
        time_filter = None
        user_filter = None
        content_type = None
        sentiment = None
        channel_hints = []
        
        # Extract time references
        time_patterns = {
            r'(last week|past week)': 'last week',
            r'(yesterday|last day)': 'yesterday', 
            r'(today|this day)': 'today',
            r'(this week|current week)': 'this week',
            r'(last month|past month)': 'last month'
        }
        
        for pattern, filter_val in time_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                time_filter = filter_val
                query = re.sub(pattern, '', query, flags=re.IGNORECASE)
                break
        
        # Extract user references  
        user_match = re.search(r'(what|from|by)\s+(\w+)\s+said', query, re.IGNORECASE)
        if user_match:
            user_filter = user_match.group(2)
            query = re.sub(r'(what|from|by)\s+\w+\s+said', '', query, flags=re.IGNORECASE)
        
        # Extract content types
        content_patterns = {
            r'(decision|decide|decided)': 'decisions',
            r'(question|asked|asking)': 'questions',
            r'(issue|problem|bug)': 'issues',
            r'(concern|worried|problem)': 'concerns'
        }
        
        for pattern, content_val in content_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                content_type = content_val
                break
        
        # Extract sentiment
        sentiment_patterns = {
            r'(confused|unclear|lost)': 'confused',
            r'(excited|happy|great)': 'excited', 
            r'(concerned|worried|anxious)': 'concerned'
        }
        
        for pattern, sentiment_val in sentiment_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                sentiment = sentiment_val
                break
        
        # Extract channel hints
        channel_matches = re.findall(r'#(\w+)', query)
        channel_hints = channel_matches
        
        # Clean query and extract remaining keywords
        query = re.sub(r'[#@]', '', query)
        query = re.sub(r'\b(show|find|get|me|discussions?|about|the)\b', '', query, flags=re.IGNORECASE)
        keywords = [word.strip() for word in query.split() if len(word.strip()) > 2]
        
        return SearchParams(
            keywords=keywords,
            time_filter=time_filter,
            user_filter=user_filter,
            content_type=content_type,
            sentiment=sentiment,
            channel_hints=channel_hints
        )
    
    def semantic_search(self, query: str, messages: List[Dict], limit: int = 10) -> List[Dict]:
        """Perform semantic search on messages."""
        
        if not messages:
            return []
        
        if self.embedding_model:
            return self._semantic_search_with_embeddings(query, messages, limit)
        else:
            return self._semantic_search_with_keywords(query, messages, limit)
    
    def _semantic_search_with_embeddings(self, query: str, messages: List[Dict], limit: int) -> List[Dict]:
        """Use embeddings for semantic similarity search."""
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            scored_messages = []
            for message in messages:
                text = message.get('text', '')
                if not text:
                    continue
                
                # Get or generate message embedding
                msg_id = message.get('ts', str(hash(text)))
                if msg_id not in self.embeddings_cache:
                    self.embeddings_cache[msg_id] = self.embedding_model.encode([text])
                
                msg_embedding = self.embeddings_cache[msg_id]
                
                # Calculate similarity
                similarity = cosine_similarity(query_embedding, msg_embedding)[0][0]
                
                if similarity > 0.2:  # Lower threshold for short terms and acronyms
                    scored_messages.append({
                        'message': message,
                        'score': float(similarity),
                        'match_reason': f'Semantic similarity: {similarity:.2f}'
                    })
            
            # Sort by score and return top results
            scored_messages.sort(key=lambda x: x['score'], reverse=True)
            return scored_messages[:limit]
            
        except Exception as e:
            print(f"Embedding search failed: {e}")
            return self._semantic_search_with_keywords(query, messages, limit)
    
    def _semantic_search_with_keywords(self, query: str, messages: List[Dict], limit: int) -> List[Dict]:
        """Fallback keyword-based search."""
        
        query_words = set(query.lower().split())
        scored_messages = []
        
        for message in messages:
            text = message.get('text', '').lower()
            if not text:
                continue
            
            # Calculate simple keyword score
            text_words = set(text.split())
            matches = query_words.intersection(text_words)
            score = len(matches) / len(query_words) if query_words else 0
            
            if score > 0:
                scored_messages.append({
                    'message': message,
                    'score': score,
                    'match_reason': f'Keywords: {", ".join(matches)}'
                })
        
        scored_messages.sort(key=lambda x: x['score'], reverse=True)
        return scored_messages[:limit]
    
    def filter_by_time(self, messages: List[Dict], time_filter: str) -> List[Dict]:
        """Filter messages by time range."""
        
        if not time_filter:
            return messages
        
        now = datetime.now()
        cutoff = None
        
        if 'yesterday' in time_filter.lower():
            cutoff = now - timedelta(days=1)
        elif 'last week' in time_filter.lower() or 'past week' in time_filter.lower():
            cutoff = now - timedelta(weeks=1)
        elif 'today' in time_filter.lower():
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif 'this week' in time_filter.lower():
            days_since_monday = now.weekday()
            cutoff = now - timedelta(days=days_since_monday)
        elif 'last month' in time_filter.lower():
            cutoff = now - timedelta(days=30)
        
        if cutoff:
            filtered = []
            for msg in messages:
                try:
                    msg_time = datetime.fromtimestamp(float(msg.get('ts', 0)))
                    if msg_time >= cutoff:
                        filtered.append(msg)
                except:
                    continue
            return filtered
        
        return messages
    
    def filter_by_user(self, messages: List[Dict], user_filter: str, slack_client) -> List[Dict]:
        """Filter messages by user."""
        
        if not user_filter:
            return messages
        
        # Try to resolve username to user ID
        user_id = None
        try:
            # Search for user by name
            users = slack_client.users_list()['members']
            for user in users:
                if (user.get('real_name', '').lower() == user_filter.lower() or 
                    user.get('name', '').lower() == user_filter.lower()):
                    user_id = user['id']
                    break
        except:
            pass
        
        # Filter messages
        filtered = []
        for msg in messages:
            msg_user = msg.get('user', '')
            if (msg_user == user_id or 
                user_filter.lower() in msg.get('text', '').lower()):
                filtered.append(msg)
        
        return filtered
    
    def generate_summary(self, results: List[Dict], query: str) -> str:
        """Generate AI summary of search results."""
        
        if not results:
            return "No relevant messages found."
        
        if self.openai_client:
            return self._generate_llm_summary(results, query)
        else:
            return self._generate_simple_summary(results, query)
    
    def _generate_llm_summary(self, results: List[Dict], query: str) -> str:
        """Generate summary using LLM."""
        
        try:
            # Extract key messages for summary
            key_messages = []
            for result in results[:5]:  # Top 5 results
                msg = result['message']
                text = msg.get('text', '')[:200]  # Limit length
                user = msg.get('user', 'Unknown')
                key_messages.append(f"{user}: {text}")
            
            prompt = f"""
            User searched for: "{query}"
            
            Here are the most relevant messages found:
            {chr(10).join(key_messages)}
            
            Provide a 1-2 sentence summary of what these results show about the topic.
            Focus on key insights, decisions, or important information.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"LLM summary failed: {e}")
            return self._generate_simple_summary(results, query)
    
    def _generate_simple_summary(self, results: List[Dict], query: str) -> str:
        """Generate simple rule-based summary."""
        
        total_messages = len(results)
        if total_messages == 0:
            return "No relevant messages found."
        elif total_messages == 1:
            return "Found 1 relevant message matching your search."
        else:
            return f"Found {total_messages} relevant messages discussing the topic."

# Global search engine instance
search_engine = NaturalLanguageSearchEngine() 