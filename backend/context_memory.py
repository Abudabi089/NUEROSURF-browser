"""
Context Memory - Extended context using Supermemory.ai
Provides semantic memory storage and RAG-based retrieval for the autonomous agent
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('NeuroSurf.ContextMemory')

# NeuroSurf data directory
DATA_DIR = Path(__file__).parent.parent / "data"
MEMORY_FILE = DATA_DIR / "context_memory.json"


class ContextMemory:
    """
    Extended context memory using Supermemory.ai
    Falls back to local ChromaDB/JSON if Supermemory is unavailable
    
    Features:
    - Store conversation context and page summaries
    - Semantic search for relevant past context
    - Automatic chunking of large content
    - Free tier: 1M tokens, 10K searches
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize context memory
        
        Args:
            api_key: Supermemory API key (optional, uses env var if not provided)
        """
        self.api_key = api_key or os.getenv("SUPERMEMORY_API_KEY")
        self.supermemory_client = None
        self.local_memory: List[Dict] = []
        self._initialized = False
        
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize the memory service"""
        if self._initialized:
            return
        
        # Try to initialize Supermemory
        if self.api_key:
            try:
                from supermemory import Supermemory
                self.supermemory_client = Supermemory(api_key=self.api_key)
                logger.info("✨ Supermemory initialized (extended context enabled)")
                self._initialized = True
                return
            except ImportError:
                logger.warning("Supermemory SDK not installed, using local fallback")
            except Exception as e:
                logger.warning(f"Supermemory init failed: {e}, using local fallback")
        
        # Fallback: Load local memory
        await self._load_local_memory()
        self._initialized = True
        logger.info("💾 Using local context memory (set SUPERMEMORY_API_KEY for extended context)")
    
    async def _load_local_memory(self):
        """Load local memory from JSON file"""
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    self.local_memory = json.load(f)
                logger.info(f"Loaded {len(self.local_memory)} memory entries")
            except Exception as e:
                logger.error(f"Failed to load local memory: {e}")
                self.local_memory = []
    
    async def _save_local_memory(self):
        """Save local memory to JSON file"""
        try:
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.local_memory, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save local memory: {e}")
    
    async def add_memory(
        self,
        content: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Add content to memory
        
        Args:
            content: Text content to store
            memory_type: Type of memory (conversation, page_summary, task_result, etc.)
            metadata: Additional metadata
            
        Returns:
            Storage result
        """
        await self.initialize()
        
        # Chunk large content
        chunks = self._chunk_content(content)
        
        if self.supermemory_client:
            try:
                # Use Supermemory API
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.supermemory_client.add(
                        content=content,
                        metadata={
                            "type": memory_type,
                            "timestamp": datetime.now().isoformat(),
                            **(metadata or {})
                        }
                    )
                )
                return {"success": True, "id": result.get("id"), "provider": "supermemory"}
            except Exception as e:
                logger.error(f"Supermemory add failed: {e}")
                # Fallback to local
        
        # Local storage
        memory_entry = {
            "id": f"local_{datetime.now().timestamp()}",
            "content": content[:5000],  # Limit size for local storage
            "type": memory_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.local_memory.append(memory_entry)
        
        # Keep only last 1000 entries
        if len(self.local_memory) > 1000:
            self.local_memory = self.local_memory[-1000:]
        
        await self._save_local_memory()
        
        return {"success": True, "id": memory_entry["id"], "provider": "local"}
    
    async def search_memory(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memory for relevant context
        
        Args:
            query: Search query
            limit: Maximum results to return
            memory_type: Filter by memory type
            
        Returns:
            List of relevant memory entries
        """
        await self.initialize()
        
        if self.supermemory_client:
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.supermemory_client.search(
                        query=query,
                        limit=limit,
                        filters={"type": memory_type} if memory_type else None
                    )
                )
                return result.get("results", [])
            except Exception as e:
                logger.error(f"Supermemory search failed: {e}")
        
        # Local search (simple keyword matching)
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_results = []
        for entry in self.local_memory:
            if memory_type and entry.get("type") != memory_type:
                continue
            
            content_lower = entry.get("content", "").lower()
            
            # Simple relevance scoring
            score = 0
            for word in query_words:
                if word in content_lower:
                    score += content_lower.count(word)
            
            if score > 0:
                scored_results.append((score, entry))
        
        # Sort by score and return top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_results[:limit]]
    
    async def get_context_for_task(
        self,
        task: str,
        max_tokens: int = 2000
    ) -> str:
        """
        Get relevant context for a task
        
        Args:
            task: Task description
            max_tokens: Approximate max tokens for context
            
        Returns:
            Formatted context string
        """
        results = await self.search_memory(task, limit=5)
        
        if not results:
            return ""
        
        context_parts = ["## Relevant Past Context:"]
        total_chars = 0
        char_limit = max_tokens * 4  # Rough token to char ratio
        
        for entry in results:
            content = entry.get("content", "")[:1000]
            memory_type = entry.get("type", "unknown")
            timestamp = entry.get("timestamp", "")[:10]
            
            part = f"\n### [{memory_type}] ({timestamp})\n{content}"
            
            if total_chars + len(part) > char_limit:
                break
            
            context_parts.append(part)
            total_chars += len(part)
        
        return "\n".join(context_parts)
    
    async def store_conversation(
        self,
        user_message: str,
        agent_response: str,
        session_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Store a conversation exchange
        
        Args:
            user_message: User's message
            agent_response: Agent's response
            session_id: Session identifier
            
        Returns:
            Storage result
        """
        content = f"User: {user_message}\n\nAgent: {agent_response}"
        return await self.add_memory(
            content=content,
            memory_type="conversation",
            metadata={"session_id": session_id}
        )
    
    async def store_page_summary(
        self,
        url: str,
        title: str,
        summary: str
    ) -> Dict[str, Any]:
        """
        Store a page summary
        
        Args:
            url: Page URL
            title: Page title
            summary: AI-generated summary
            
        Returns:
            Storage result
        """
        content = f"URL: {url}\nTitle: {title}\n\nSummary: {summary}"
        return await self.add_memory(
            content=content,
            memory_type="page_summary",
            metadata={"url": url, "title": title}
        )
    
    async def store_task_result(
        self,
        task: str,
        result: str,
        actions: List[str]
    ) -> Dict[str, Any]:
        """
        Store a task result
        
        Args:
            task: Original task description
            result: Task result/output
            actions: List of actions taken
            
        Returns:
            Storage result
        """
        content = f"Task: {task}\n\nResult: {result}\n\nActions: {', '.join(actions)}"
        return await self.add_memory(
            content=content,
            memory_type="task_result",
            metadata={"task": task}
        )
    
    def _chunk_content(self, content: str, chunk_size: int = 1000) -> List[str]:
        """Split content into chunks for storage"""
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        words = content.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks


# Singleton instance
_context_memory: Optional[ContextMemory] = None


def get_context_memory() -> ContextMemory:
    """Get or create singleton context memory instance"""
    global _context_memory
    if _context_memory is None:
        _context_memory = ContextMemory()
    return _context_memory
