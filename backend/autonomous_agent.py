"""
Autonomous Agent - Main agent orchestrator for NeuroSurf
Powered by Nemotron with full tool access and agentic reasoning loop
"""

import asyncio
import logging
import json
import re
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import os
import ollama

from agent_tools import AgentTools
from context_memory import get_context_memory

logger = logging.getLogger('NeuroSurf.AutonomousAgent')

# Fast model for CPU-bound systems (Intel Iris Xe / i5-13th gen)
MODEL = 'qwen2.5:3b'

# Singleton Ollama async client - reused across all calls
_ollama_client: Optional[ollama.AsyncClient] = None

def get_ollama_client() -> ollama.AsyncClient:
    """Get or create the singleton Ollama async client"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = ollama.AsyncClient()
    return _ollama_client

# Compressed system prompt (~200 tokens instead of ~400)
CURRENT_DIR = os.getcwd()

AGENT_SYSTEM_PROMPT = """You are Neuro, a helpful AI assistant. Be concise.
Rules: Use double newlines between points. For research tasks use web_search then write_research_document to save findings as a formatted document. For math use calculate tool. For vision use webcam_analyze.
Tools are called via JSON: {"tool": "name", "parameters": {...}}
Wait for tool results before concluding."""


class AutonomousAgent:
    """
    Autonomous agent with agentic loop for complex task execution
    Uses tool calling, planning, and iterative reasoning
    """
    
    def __init__(
        self, 
        memory_store=None, 
        vision_helper=None,
        max_iterations: int = 15
    ):
        """
        Initialize the autonomous agent
        
        Args:
            memory_store: Optional MemoryStore for persistence
            vision_helper: Optional VisionHelper for screenshot analysis
            max_iterations: Maximum tool-calling iterations per task
        """
        self.model = MODEL
        self.tools = AgentTools(memory_store=memory_store, vision_helper=vision_helper)
        self.memory_store = memory_store
        self.max_iterations = max_iterations
        self.conversation_history: List[Dict[str, str]] = []
        self._halt_flag = False
        self._current_task = None
        # Keep history minimal for fast context processing on CPU
        self._max_history = 6
        
    async def process_task(
        self, 
        task: str, 
        callback: Optional[Callable] = None,
        on_chunk: Optional[Callable] = None,
        session_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Main entry point - process a user task through the agentic loop
        
        Args:
            task: Natural language task/command from user
            callback: Async callback for streaming updates to frontend
            session_id: Session identifier for memory
            
        Returns:
            Task result with summary and actions taken
        """
        self._halt_flag = False
        self._current_task = task
        
        logger.info(f"🤖 Starting task: {task}")
        
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": task
        })
        
        # Store in memory (non-blocking - don't wait for this)
        if self.memory_store:
            try:
                asyncio.create_task(self._save_memory("user", task, session_id))
            except Exception as e:
                logger.error(f"Memory store error: {e}")
        
        # Run the agentic loop
        actions_taken = []
        final_response = ""
        
        for iteration in range(self.max_iterations):
            if self._halt_flag:
                final_response = "Task halted by user."
                break
            
            # Build messages for Chat API
            messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}]
            recent_context = self.conversation_history[-self._max_history:]
            messages.extend(recent_context)
            
            try:
                # Call the LLM with messages list
                response = await self._call_llm(messages, on_chunk=on_chunk)
                
                if not response:
                    final_response = "I apologize, I couldn't generate a response."
                    break
                
                # Parse response for tool calls
                tool_calls = self._extract_tool_calls(response)
                
                if tool_calls:
                    for tool_call in tool_calls:
                        tool_name = tool_call.get("tool")
                        parameters = tool_call.get("parameters", {})
                        
                        logger.info(f"🔧 Tool call: {tool_name}({parameters})")
                        
                        # Execute the tool
                        result = await self.tools.execute_tool(tool_name, parameters)
                        
                        actions_taken.append({
                            "tool": tool_name,
                            "parameters": parameters,
                            "result": result
                        })
                        
                        # Add truncated tool result to history (keeps context small)
                        result_str = json.dumps(result, default=str)
                        if len(result_str) > 500:
                            result_str = result_str[:500] + '...TRUNCATED'
                        self.conversation_history.append({
                            "role": "user",
                            "content": f"TOOL_RESULT({tool_name}): {result_str}"
                        })
                    
                    # Continue loop to let agent respond to tool results
                    continue
                else:
                    # No tool calls - this is the final response
                    final_response = self._clean_response(response)
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    if callback:
                        await callback(final_response, "assistant")
                    break
            except Exception as e:
                logger.error(f"Agent iteration error: {e}")
                final_response = f"I encountered an error: {str(e)}"
                break
        
        # Store final response in memory (non-blocking)
        if self.memory_store and final_response:
            try:
                asyncio.create_task(self._save_memory("agent", final_response, session_id))
            except Exception as e:
                logger.error(f"Memory store error: {e}")
        
        if callback:
            await callback(f"✨ Task complete", "system")
        
        return {
            "response": final_response,
            "actions": actions_taken
        }
    
    def _build_prompt(self) -> str:
        """Build the full prompt with system message and conversation history"""
        messages = [AGENT_SYSTEM_PROMPT, ""]
        
        # Add recent conversation history (keep short for speed)
        recent_history = self.conversation_history[-self._max_history:]
        for msg in recent_history:
            role = msg["role"].upper()
            content = msg["content"]
            messages.append(f"{role}: {content}")
        
        messages.append("\nNEURO:")
        return "\n\n".join(messages)
    
    async def _save_memory(self, role: str, content: str, session_id: str):
        """Non-blocking memory save helper"""
        try:
            self.memory_store.add_conversation(
                role, content, session_id,
                {"timestamp": datetime.now().isoformat()}
            )
        except Exception as e:
            logger.error(f"Memory save error: {e}")

    async def _call_llm(self, messages: List[Dict[str, str]], on_chunk: Optional[Callable] = None) -> str:
        """Call the LLM with optimized streaming using Chat API"""
        try:
            client = get_ollama_client()
            full_response = ""
            
            # Optimized for CPU (Intel i5-13th gen + Iris Xe)
            chat_call = await client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                keep_alive='5m',
                options={
                    'temperature': 0.5,
                    'num_predict': 384,
                    'top_p': 0.85,
                    'num_ctx': 2048,
                    'repeat_penalty': 1.1,
                    'num_batch': 256,
                    'num_thread': 8,
                }
            )
            
            async for chunk in chat_call:
                text_chunk = chunk.get('message', {}).get('content', '')
                full_response += text_chunk
                if on_chunk and text_chunk:
                    try:
                        await on_chunk(text_chunk)
                    except:
                        pass
            
            return full_response.strip()
            
        except asyncio.TimeoutError:
            logger.error("LLM call timed out")
            return "Error: I timed out while thinking. Please try again."
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            if "connection" in str(e).lower():
                return "Error: Could not connect to Ollama. Please make sure the Ollama service is running."
            raise
    
    def _extract_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Extract all JSON tool calls from LLM response"""
        tool_calls = []
        try:
            # Method 1: Look for JSON blocks in code tags
            json_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            for block in json_blocks:
                try:
                    tool_calls.append(json.loads(block))
                except: continue
            
            if tool_calls: return tool_calls

            # Method 2: Look for raw JSON objects starting with {"tool":
            start = 0
            while True:
                start_idx = response.find('{"tool":', start)
                if start_idx == -1: break
                
                open_braces = 0
                for i in range(start_idx, len(response)):
                    char = response[i]
                    if char == '{': open_braces += 1
                    elif char == '}': open_braces -= 1
                        
                    if open_braces == 0:
                        json_str = response[start_idx:i+1]
                        try:
                            tool_calls.append(json.loads(json_str))
                            start = i + 1
                            break
                        except:
                            start = i + 1
                            break
                else: break # No closing brace
                        
            return tool_calls
            
        except Exception as e:
            logger.error(f"Error extracting tool calls: {e}")
            return []
    
    def _clean_response(self, response: str) -> str:
        """Clean up response for display to user"""
        if not response:
            return "Task completed."
        # Remove any lingering tool JSON blocks
        response = re.sub(r'```json\s*\{.*?\}\s*```', '', response, flags=re.DOTALL)
        response = re.sub(r'\{"tool":\s*".*?"\s*,\s*"parameters":\s*\{.*?\}\}', '', response, flags=re.DOTALL)
        # Final fallback for any remaining tool strings
        response = re.sub(r'\{"tool":\s*".*?"\s*\}', '', response, flags=re.DOTALL)
        return response.strip() or "Task completed."
    
    def halt(self):
        """Halt current task processing"""
        self._halt_flag = True
        self._current_task = None
        logger.warning("🛑 Agent halted")
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "model": self.model,
            "current_task": self._current_task,
            "history_length": len(self.conversation_history),
            "tools_available": list(self.tools.get_tool_definitions())
        }


# Singleton instance for the backend
_agent_instance: Optional[AutonomousAgent] = None


def get_agent(memory_store=None, vision_helper=None) -> AutonomousAgent:
    """Get or create the singleton agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AutonomousAgent(
            memory_store=memory_store,
            vision_helper=vision_helper
        )
    return _agent_instance
