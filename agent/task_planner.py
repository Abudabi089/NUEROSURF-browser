"""
Task Planner - Uses Executive model to decompose commands into steps
"""

import logging
import json
from typing import List, Dict, Any, Optional
import ollama

logger = logging.getLogger('NeuroSurf.TaskPlanner')


class TaskPlanner:
    """
    Task planning using the Executive LLM
    Breaks down natural language commands into executable steps
    """
    
    def __init__(self, model: str = "llama3.1:8b"):
        """
        Initialize task planner
        
        Args:
            model: Ollama model for planning
        """
        self.model = model
        
    async def plan(
        self,
        command: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an execution plan from a natural language command
        
        Args:
            command: User's natural language command
            context: Additional context (current URL, page content, etc.)
            
        Returns:
            Plan with summary and steps
        """
        context_str = ""
        if context:
            if context.get('current_url'):
                context_str += f"\nCurrent URL: {context['current_url']}"
            if context.get('page_title'):
                context_str += f"\nPage Title: {context['page_title']}"
        
        prompt = f"""You are a web browsing assistant that breaks down user commands into step-by-step browser actions.

Available actions:
- navigate: Go to a URL
- click: Click on an element (describe what to click)
- type: Type text into a field (specify field and text)
- read: Read and extract page content
- scroll: Scroll the page (up/down/to element)
- wait: Wait for something to appear
- screenshot: Take a screenshot

User Command: {command}
{context_str}

Create a JSON plan with:
1. "summary": Brief description of what will be done
2. "steps": Array of action objects

Each step should have:
- "action": One of the available actions
- "target": What to interact with (URL, element description, etc.)
- "value": Optional value (for typing, etc.)
- "description": Human-readable description of this step

Example response:
{{
  "summary": "Search for information on Google",
  "steps": [
    {{"action": "navigate", "target": "https://google.com", "description": "Go to Google"}},
    {{"action": "type", "target": "search input field", "value": "query text", "description": "Enter search query"}},
    {{"action": "click", "target": "search button", "description": "Submit search"}}
  ]
}}

Respond with valid JSON only:"""

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                format='json'
            )
            
            plan = json.loads(response['response'])
            
            # Validate plan structure
            if 'steps' not in plan:
                plan['steps'] = []
            if 'summary' not in plan:
                plan['summary'] = command
            
            logger.info(f"Created plan with {len(plan['steps'])} steps")
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {e}")
            return self._fallback_plan(command)
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return self._fallback_plan(command)
    
    def _fallback_plan(self, command: str) -> Dict[str, Any]:
        """Create a simple fallback plan"""
        # Try to extract URL if present
        import re
        url_match = re.search(r'https?://\S+', command)
        
        steps = []
        if url_match:
            steps.append({
                "action": "navigate",
                "target": url_match.group(),
                "description": f"Navigate to {url_match.group()}"
            })
        
        steps.append({
            "action": "read",
            "target": "page content",
            "description": "Read page content"
        })
        
        return {
            "summary": f"Attempt: {command}",
            "steps": steps
        }
    
    async def refine_step(
        self,
        step: Dict[str, Any],
        page_context: str
    ) -> Dict[str, Any]:
        """
        Refine a step based on actual page content
        
        Args:
            step: Original step
            page_context: Current page HTML or text
            
        Returns:
            Refined step with more specific selectors
        """
        prompt = f"""Given this browser action step and the current page content, 
provide more specific instructions.

Step: {json.dumps(step)}

Page content (truncated):
{page_context[:2000]}

Provide a refined step with:
- More specific target selector or description
- Any additional context needed

Respond with JSON:"""

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                format='json'
            )
            
            refined = json.loads(response['response'])
            return {**step, **refined}
            
        except Exception as e:
            logger.warning(f"Step refinement failed: {e}")
            return step
    
    async def summarize_task_result(
        self,
        command: str,
        steps_results: List[Dict[str, Any]]
    ) -> str:
        """
        Summarize the results of a completed task
        
        Args:
            command: Original command
            steps_results: Results from each step
            
        Returns:
            Human-readable summary
        """
        results_str = "\n".join([
            f"- {r.get('action', 'unknown')}: {r.get('status', 'unknown')}"
            for r in steps_results
        ])
        
        prompt = f"""Summarize the results of this browsing task for the user.

Original command: {command}

Steps completed:
{results_str}

Provide a brief, friendly summary of what was accomplished or any issues encountered:"""

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt
            )
            return response['response']
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"Task completed with {len(steps_results)} steps."


class YouTubeTaskHandler:
    """
    Specialized handler for YouTube video tasks
    """
    
    def __init__(self, planner: TaskPlanner):
        self.planner = planner
        
    async def handle_video_summary(
        self,
        video_url: str
    ) -> Dict[str, Any]:
        """
        Handle "watch and summarize" type commands
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Plan for video summarization
        """
        return {
            "summary": f"Watch and summarize YouTube video",
            "steps": [
                {
                    "action": "navigate",
                    "target": video_url,
                    "description": "Open YouTube video"
                },
                {
                    "action": "wait",
                    "target": "video player",
                    "value": "3000",
                    "description": "Wait for video to load"
                },
                {
                    "action": "click",
                    "target": "show transcript button or more options",
                    "description": "Try to access transcript"
                },
                {
                    "action": "read",
                    "target": "transcript or video description",
                    "description": "Extract available text content"
                },
                {
                    "action": "summarize",
                    "target": "extracted content",
                    "description": "Generate summary of video content"
                }
            ],
            "special_handler": "youtube_summary"
        }
