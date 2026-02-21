"""
Memory Store - ChromaDB integration for agent memory
Provides episodic memory and context retrieval
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings

logger = logging.getLogger('NeuroSurf.Memory')


class MemoryStore:
    """
    ChromaDB-based memory store for the agent
    Stores conversation history, browsing context, and task results
    """
    
    def __init__(self, persist_directory: str = "./data/memory"):
        """
        Initialize memory store
        
        Args:
            persist_directory: Directory for ChromaDB persistence
        """
        self.persist_directory = persist_directory
        self.client: Optional[chromadb.Client] = None
        self.conversations: Optional[chromadb.Collection] = None
        self.browsing_history: Optional[chromadb.Collection] = None
        self.task_results: Optional[chromadb.Collection] = None
        
    async def initialize(self):
        """Initialize ChromaDB collections"""
        logger.info("💾 Initializing Memory Store...")
        
        try:
            # Create persistent client
            self.client = chromadb.Client(Settings(
                anonymized_telemetry=False,
                persist_directory=self.persist_directory
            ))
            
            # Create collections
            self.conversations = self.client.get_or_create_collection(
                name="conversations",
                metadata={"description": "User-agent conversation history"}
            )
            
            self.browsing_history = self.client.get_or_create_collection(
                name="browsing_history",
                metadata={"description": "Visited pages and content"}
            )
            
            self.task_results = self.client.get_or_create_collection(
                name="task_results",
                metadata={"description": "Completed task results and summaries"}
            )
            
            logger.info("  ✅ Conversations collection ready")
            logger.info("  ✅ Browsing history collection ready")
            logger.info("  ✅ Task results collection ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory store: {e}")
            raise
            
    async def shutdown(self):
        """Cleanup memory store"""
        logger.info("💾 Memory Store shutdown")
        
    # ==================== Conversation Memory ====================
    
    async def add_conversation(
        self,
        role: str,
        content: str,
        session_id: str,
        metadata: Optional[Dict] = None
    ):
        """
        Add a conversation entry
        
        Args:
            role: "user" or "agent"
            content: Message content
            session_id: Current session identifier
            metadata: Additional metadata
        """
        if not self.conversations:
            return
        
        doc_id = f"{session_id}_{datetime.now().timestamp()}"
        meta = {
            "role": role,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        self.conversations.add(
            documents=[content],
            metadatas=[meta],
            ids=[doc_id]
        )
        
    async def get_conversation_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant conversation history
        
        Args:
            query: Query to find relevant context
            session_id: Limit to specific session
            n_results: Number of results to return
            
        Returns:
            List of relevant conversation entries
        """
        if not self.conversations:
            return []
        
        where = {"session_id": session_id} if session_id else None
        
        results = self.conversations.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        entries = []
        for i, doc in enumerate(results['documents'][0]):
            entries.append({
                "content": doc,
                "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                "distance": results['distances'][0][i] if results['distances'] else None
            })
            
        return entries
    
    # ==================== Browsing History ====================
    
    async def add_page(
        self,
        url: str,
        title: str,
        content: str,
        session_id: str,
        metadata: Optional[Dict] = None
    ):
        """
        Add a visited page to browsing history
        
        Args:
            url: Page URL
            title: Page title
            content: Page text content
            session_id: Current session
            metadata: Additional metadata
        """
        if not self.browsing_history:
            return
        
        doc_id = f"page_{hash(url)}_{datetime.now().timestamp()}"
        meta = {
            "url": url,
            "title": title,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        # Truncate content if too long
        max_content_length = 10000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        self.browsing_history.add(
            documents=[content],
            metadatas=[meta],
            ids=[doc_id]
        )
        
    async def search_pages(
        self,
        query: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search browsing history for relevant pages
        
        Args:
            query: Search query
            n_results: Number of results
            
        Returns:
            List of relevant pages
        """
        if not self.browsing_history:
            return []
        
        results = self.browsing_history.query(
            query_texts=[query],
            n_results=n_results
        )
        
        pages = []
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i] if results['metadatas'] else {}
            pages.append({
                "url": meta.get('url'),
                "title": meta.get('title'),
                "content_snippet": doc[:500] + "..." if len(doc) > 500 else doc,
                "timestamp": meta.get('timestamp')
            })
            
        return pages
    
    # ==================== Task Results ====================
    
    async def save_task_result(
        self,
        task_description: str,
        result: str,
        session_id: str,
        metadata: Optional[Dict] = None
    ):
        """
        Save a completed task result
        
        Args:
            task_description: What was the task
            result: Task result/summary
            session_id: Current session
            metadata: Additional metadata
        """
        if not self.task_results:
            return
        
        doc_id = f"task_{datetime.now().timestamp()}"
        meta = {
            "task": task_description,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        self.task_results.add(
            documents=[result],
            metadatas=[meta],
            ids=[doc_id]
        )
        
    async def get_similar_tasks(
        self,
        query: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find similar past tasks
        
        Args:
            query: Current task description
            n_results: Number of results
            
        Returns:
            List of similar past tasks
        """
        if not self.task_results:
            return []
        
        results = self.task_results.query(
            query_texts=[query],
            n_results=n_results
        )
        
        tasks = []
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i] if results['metadatas'] else {}
            tasks.append({
                "task": meta.get('task'),
                "result": doc,
                "timestamp": meta.get('timestamp')
            })
            
        return tasks
