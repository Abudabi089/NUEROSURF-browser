"""
Agent Tools - Tool implementations for the Autonomous Agent
Provides terminal, file system, screenshot, and memory capabilities
"""

import asyncio
import logging
import subprocess
import os
import json
import shutil
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger('NeuroSurf.AgentTools')

# NeuroSurf workspace root for self-modification
NEUROSURF_ROOT = Path(__file__).parent.parent.resolve()


class AgentTools:
    """
    Collection of tools available to the Autonomous Agent
    Each tool is a callable that returns a structured result
    """
    
    def __init__(self, memory_store=None, vision_helper=None):
        """
        Initialize agent tools
        
        Args:
            memory_store: Optional MemoryStore instance for memory operations
            vision_helper: Optional VisionHelper for screenshot analysis
        """
        self.memory_store = memory_store
        self.vision_helper = vision_helper
        self.screenshot_callback = None  # Set by backend to capture from Electron
        self._screenshot_dir = NEUROSURF_ROOT / "data" / "screenshots"
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for LLM function calling
        Returns structured tool descriptions
        """
        return [
            {
                "name": "terminal_execute",
                "description": "Execute a shell command and return the output. Use for running programs, scripts, or system commands.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute"
                        },
                        "working_dir": {
                            "type": "string",
                            "description": "Optional working directory for the command"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "fs_list",
                "description": "List contents of a directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "fs_read",
                "description": "Read the contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string", 
                            "description": "File path to read"
                        },
                        "max_lines": {
                            "type": "integer",
                            "description": "Maximum lines to read (default: 500)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "fs_write",
                "description": "Write content to a file. Creates the file if it doesn't exist.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "fs_delete",
                "description": "Delete a file or directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to delete"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "modify_neurosurf",
                "description": "Modify NeuroSurf's own source code. Use this to fix bugs, add features, or debug issues in NeuroSurf itself.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Relative path within NeuroSurf (e.g., 'backend/main.py', 'src/App.jsx')"
                        },
                        "content": {
                            "type": "string",
                            "description": "New file content to write"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the change being made"
                        }
                    },
                    "required": ["file_path", "content", "description"]
                }
            },
            {
                "name": "screenshot_capture",
                "description": "Capture a screenshot of the current screen/browser view",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "screenshot_analyze",
                "description": "Analyze a screenshot using vision AI",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "screenshot_path": {
                            "type": "string",
                            "description": "Path to screenshot image"
                        },
                        "query": {
                            "type": "string",
                            "description": "Question or analysis request about the screenshot"
                        }
                    },
                    "required": ["screenshot_path", "query"]
                }
            },
            {
                "name": "memory_store",
                "description": "Store information in persistent memory for later retrieval",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Memory key/identifier"
                        },
                        "value": {
                            "type": "string",
                            "description": "Information to store"
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Optional metadata"
                        }
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "memory_search",
                "description": "Search memory for relevant past information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results (default: 5)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "web_scrape",
                "description": "Scrape a web page to extract text, links, or specific data using CSS selectors",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to scrape"
                        },
                        "selectors": {
                            "type": "object",
                            "description": "Optional CSS selectors as {name: selector} to extract specific elements"
                        },
                        "extract_links": {
                            "type": "boolean",
                            "description": "Whether to extract all links from the page"
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "browser_open_tab",
                "description": "Open a new tab in the NeuroSurf browser with a specific URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to open in the new tab"
                        },
                        "title": {
                            "type": "string",
                            "description": "Optional title for the new tab"
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for information using DuckDuckGo. Returns titles, URLs and snippets.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Optional number of results (default 5)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "write_research_document",
                "description": "Write all research findings into a formatted document and open it. Use this ONCE at the end of research to present ALL findings together.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Document title (the research topic)"
                        },
                        "sections": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of section contents. Each string is a section with heading and body, e.g. '## Overview\nContent here...'"
                        },
                        "sources": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of source URLs used"
                        }
                    },
                    "required": ["title", "sections"]
                }
            },
            {
                "name": "calculate",
                "description": "Evaluate a mathematical expression. Use this for simple or complex math instead of manual reasoning.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The math expression to evaluate (e.g., '2 + 2', 'sqrt(16) * sin(45)')"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "webcam_analyze",
                "description": "Analyze the current frame from the user's webcam. Use this when the user asks you to 'look at this' or 'check what I am showing you'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The question or task related to the webcam image"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "spawn_task_agent",
                "description": "Spawn a sub-agent to perform a specific task asynchronously (web research, data collection, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Description of the task for the sub-agent"
                        },
                        "urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of URLs for the agent to process"
                        }
                    },
                    "required": ["task"]
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name with given parameters
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        tool_methods = {
            "terminal_execute": self.terminal_execute,
            "fs_list": self.fs_list,
            "fs_read": self.fs_read,
            "fs_write": self.fs_write,
            "fs_delete": self.fs_delete,
            "modify_neurosurf": self.modify_neurosurf,
            "screenshot_capture": self.screenshot_capture,
            "screenshot_analyze": self.screenshot_analyze,
            "memory_store": self.memory_store_tool,
            "memory_search": self.memory_search_tool,
            "web_scrape": self.web_scrape,
            "web_search": self.web_search,
            "write_research_document": self.write_research_document,
            "write_research_pdf": self.write_research_pdf,
            "browser_open_tab": self.browser_open_tab,
            "spawn_task_agent": self.spawn_task_agent,
            "calculate": self.calculate,
            "webcam_analyze": self.webcam_analyze
        }
        
        method = tool_methods.get(tool_name)
        if not method:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            result = await method(**parameters)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== Terminal ====================
    
    async def terminal_execute(
        self, 
        command: str, 
        working_dir: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a shell command
        
        Args:
            command: Shell command to execute
            working_dir: Optional working directory
            timeout: Command timeout in seconds
            
        Returns:
            Command output and status
        """
        import re
        def strip_ansi(text):
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            return ansi_escape.sub('', text)
            
        logger.info(f"🐚 Executing: {command}")
        
        cwd = working_dir or str(NEUROSURF_ROOT)
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "stdout": strip_ansi(stdout.decode('utf-8', errors='replace')),
                "stderr": strip_ansi(stderr.decode('utf-8', errors='replace')),
                "return_code": process.returncode,
                "command": command
            }
            
        except asyncio.TimeoutError:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "return_code": -1,
                "command": command
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "command": command
            }
    
    # ==================== File System ====================
    
    async def fs_list(self, path: str = ".") -> Dict[str, Any]:
        """List directory contents"""
        try:
            target_path = path if path else "."
            abs_path = Path(target_path).resolve()
            # Safety check: ensure we don't list outside typical bounds if needed, 
            # but for now we trust the agent in the workspace.
            
            if not abs_path.exists():
                return {"error": f"Path does not exist: {abs_path}", "items": []}

            items = []
            
            for item in abs_path.iterdir():
                items.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
            
            return {
                "path": str(abs_path),
                "items": items,
                "count": len(items)
            }
        except Exception as e:
            logger.error(f"fs_list error: {e}")
            raise Exception(f"Failed to list directory: {e}")
    
    async def fs_read(self, path: str, max_lines: int = 500) -> Dict[str, Any]:
        """Read file contents"""
        try:
            if not path:
                raise Exception("File path is required")
                
            file_path = Path(path).resolve()
            
            if not file_path.exists():
                raise Exception(f"File not found: {path}")
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            content = ''.join(lines[:max_lines])
            truncated = len(lines) > max_lines
            
            return {
                "path": str(file_path),
                "content": content,
                "lines": min(len(lines), max_lines),
                "total_lines": len(lines),
                "truncated": truncated
            }
        except Exception as e:
            raise Exception(f"Failed to read file: {e}")
    
    async def fs_write(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to file"""
        try:
            file_path = Path(path).resolve()
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "path": str(file_path),
                "bytes_written": len(content.encode('utf-8')),
                "status": "success"
            }
        except Exception as e:
            raise Exception(f"Failed to write file: {e}")
    
    async def fs_delete(self, path: str) -> Dict[str, Any]:
        """Delete file or directory"""
        try:
            target = Path(path).resolve()
            
            # Safety: Don't allow deleting outside workspace or critical files
            if not str(target).startswith(str(NEUROSURF_ROOT)):
                raise Exception("Cannot delete files outside NeuroSurf workspace")
            
            if target.name in ['.git', 'node_modules', '.env']:
                raise Exception(f"Cannot delete protected path: {target.name}")
            
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            
            return {
                "path": str(target),
                "status": "deleted"
            }
        except Exception as e:
            raise Exception(f"Failed to delete: {e}")
    
    # ==================== NeuroSurf Self-Modification ====================
    
    async def modify_neurosurf(
        self, 
        file_path: str, 
        content: str, 
        description: str
    ) -> Dict[str, Any]:
        """
        Modify NeuroSurf's own source code
        
        Args:
            file_path: Relative path within NeuroSurf
            content: New file content
            description: Description of the change
            
        Returns:
            Modification result
        """
        try:
            target = NEUROSURF_ROOT / file_path
            
            # Validate file is within NeuroSurf
            if not str(target.resolve()).startswith(str(NEUROSURF_ROOT)):
                raise Exception("Cannot modify files outside NeuroSurf")
            
            # Read original for backup/diff
            original = ""
            if target.exists():
                with open(target, 'r', encoding='utf-8') as f:
                    original = f.read()
            
            # Create backup
            backup_dir = NEUROSURF_ROOT / "data" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{target.stem}_{timestamp}{target.suffix}"
            backup_path = backup_dir / backup_name
            
            if original:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original)
            
            # Write new content
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✏️ Modified NeuroSurf: {file_path} - {description}")
            
            # Store change in memory if available
            if self.memory_store:
                await self._store_code_change(file_path, description, original, content)
            
            return {
                "file": str(target),
                "backup": str(backup_path) if original else None,
                "description": description,
                "status": "modified"
            }
            
        except Exception as e:
            raise Exception(f"Failed to modify NeuroSurf: {e}")
    
    async def _store_code_change(
        self, 
        file_path: str, 
        description: str, 
        original: str, 
        new_content: str
    ):
        """Store code change in memory for tracking"""
        if self.memory_store and hasattr(self.memory_store, 'save_task_result'):
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.memory_store.save_task_result,
                    f"Modified {file_path}",
                    description,
                    "agent_modification",
                    {"lines_before": len(original.split('\n')), 
                     "lines_after": len(new_content.split('\n'))}
                )
            except Exception as e:
                logger.error(f"Failed to store code change: {e}")
    
    # ==================== Screenshots ====================
    
    async def screenshot_capture(self) -> Dict[str, Any]:
        """Capture a screenshot"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = self._screenshot_dir / f"screenshot_{timestamp}.png"
            
            # If we have an Electron callback, use it
            if self.screenshot_callback:
                image_data = await self.screenshot_callback()
                if image_data:
                    # Decode base64 and save
                    with open(screenshot_path, 'wb') as f:
                        f.write(base64.b64decode(image_data))
                    
                    return {
                        "path": str(screenshot_path),
                        "status": "captured"
                    }
            
            # Fallback: Use system screenshot (Windows)
            import platform
            if platform.system() == 'Windows':
                try:
                    # Use PowerShell to capture screen
                    ps_script = f'''
                    Add-Type -AssemblyName System.Windows.Forms
                    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
                    $bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
                    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                    $graphics.CopyFromScreen(0, 0, 0, 0, $bitmap.Size)
                    $bitmap.Save("{str(screenshot_path).replace(chr(92), '/')}")
                    $graphics.Dispose()
                    $bitmap.Dispose()
                    '''
                    result = await self.terminal_execute(
                        f'powershell -Command "{ps_script}"',
                        timeout=10
                    )
                    
                    if screenshot_path.exists():
                        return {
                            "path": str(screenshot_path),
                            "status": "captured"
                        }
                except Exception as e:
                    logger.error(f"Screenshot fallback failed: {e}")
            
            return {
                "path": None,
                "status": "failed",
                "error": "Screenshot capture not available"
            }
            
        except Exception as e:
            raise Exception(f"Screenshot capture failed: {e}")
    
    async def screenshot_analyze(
        self, 
        screenshot_path: str, 
        query: str
    ) -> Dict[str, Any]:
        """Analyze a screenshot using vision AI"""
        try:
            if not Path(screenshot_path).exists():
                raise Exception(f"Screenshot not found: {screenshot_path}")
            
            if self.vision_helper:
                analysis = await self.vision_helper.analyze_page(screenshot_path, query)
                return {
                    "analysis": analysis,
                    "screenshot": screenshot_path
                }
            else:
                # Direct Ollama call as fallback
                import ollama
                response = ollama.generate(
                    model="llava:latest",
                    prompt=query,
                    images=[screenshot_path]
                )
                return {
                    "analysis": response.get('response', ''),
                    "screenshot": screenshot_path
                }
                
        except Exception as e:
            raise Exception(f"Screenshot analysis failed: {e}")

    async def calculate(self, expression: str) -> Dict[str, Any]:
        """Evaluate a math expression safely"""
        import math
        logger.info(f"🔢 Calculating: {expression}")
        try:
            # Safe namespace for eval
            safe_dict = {
                "abs": abs, "round": round, "pow": pow,
                "sum": sum, "min": min, "max": max,
                "math": math,
                "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
                "tan": math.tan, "pi": math.pi, "e": math.e
            }
            # Remove any potentially dangerous characters
            clean_expr = expression.replace('__', '').replace('import', '')
            result = eval(clean_expr, {"__builtins__": {}}, safe_dict)
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"error": str(e), "expression": expression}

    async def webcam_analyze(self, query: str) -> Dict[str, Any]:
        """Analyze the latest webcam frame"""
        try:
            webcam_path = NEUROSURF_ROOT / "data" / "webcam" / "current_frame.jpg"
            if not webcam_path.exists():
                return {"error": "Webcam frame not found. Make sure webcam is active."}

            vision_prompt = f"""You are Neuro's vision system. Analyze this webcam image objectively.
User query: {query}

Instructions:
1. Describe only what is definitively visible.
2. If an object is blurry or partially out of frame, state that clearly.
3. Prioritize identifying shapes, colors, and text on objects.
4. Avoid guessing if you are not certain.

Your analysis:"""

            if self.vision_helper:
                analysis = await self.vision_helper.analyze_page(str(webcam_path), vision_prompt)
                return {
                    "analysis": analysis,
                    "frame": str(webcam_path)
                }
            else:
                import ollama
                response = ollama.generate(
                    model="llava:latest",
                    prompt=vision_prompt,
                    images=[str(webcam_path)]
                )
                return {
                    "analysis": response.get('response', ''),
                    "frame": str(webcam_path)
                }
        except Exception as e:
            return {"error": str(e)}
    
    # ==================== Memory ====================
    
    async def memory_store_tool(
        self, 
        key: str, 
        value: str, 
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Store information in memory"""
        try:
            if self.memory_store:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.memory_store.add_conversation,
                    "agent",
                    f"{key}: {value}",
                    "agent_memory",
                    metadata
                )
                return {"key": key, "status": "stored"}
            else:
                # Fallback: Store in local JSON
                memory_file = NEUROSURF_ROOT / "data" / "agent_memory.json"
                memory_file.parent.mkdir(parents=True, exist_ok=True)
                
                memories = {}
                if memory_file.exists():
                    with open(memory_file, 'r') as f:
                        memories = json.load(f)
                
                memories[key] = {
                    "value": value,
                    "metadata": metadata,
                    "timestamp": datetime.now().isoformat()
                }
                
                with open(memory_file, 'w') as f:
                    json.dump(memories, f, indent=2)
                
                return {"key": key, "status": "stored"}
                
        except Exception as e:
            raise Exception(f"Memory store failed: {e}")
    
    async def memory_search_tool(
        self, 
        query: str, 
        limit: int = 5
    ) -> Dict[str, Any]:
        """Search memory for relevant information"""
        try:
            if self.memory_store:
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    self.memory_store.get_conversation_context,
                    query,
                    None,
                    limit
                )
                return {"query": query, "results": results}
            else:
                # Fallback: Search local JSON
                memory_file = NEUROSURF_ROOT / "data" / "agent_memory.json"
                
                if not memory_file.exists():
                    return {"query": query, "results": []}
                
                with open(memory_file, 'r') as f:
                    memories = json.load(f)
                
                # Simple keyword search
                query_lower = query.lower()
                results = [
                    {"key": k, **v}
                    for k, v in memories.items()
                    if query_lower in k.lower() or query_lower in v.get('value', '').lower()
                ][:limit]
                
                return {"query": query, "results": results}
                
        except Exception as e:
            raise Exception(f"Memory search failed: {e}")
    
    # ==================== Web Scraping ====================
    
    async def web_scrape(
        self,
        url: str,
        selectors: Optional[Dict[str, str]] = None,
        extract_links: bool = False
    ) -> Dict[str, Any]:
        """
        Scrape a web page
        
        Args:
            url: URL to scrape
            selectors: Optional CSS selectors for specific data
            extract_links: Whether to extract links
            
        Returns:
            Scraped content
        """
        try:
            from scraping_agent import get_scraping_agent
            
            agent = get_scraping_agent()
            result = await agent.scrape(
                url=url,
                selectors=selectors,
                extract_links=extract_links,
                extract_text=True
            )
            
            logger.info(f"🌐 Scraped: {url}")
            return result
            
        except Exception as e:
            logger.error(f"Web scrape failed: {e}")
            raise Exception(f"Web scrape failed: {e}")

    async def web_search(
        self,
        query: str,
        num_results: int = 5
    ) -> Dict[str, Any]:
        """Perform a web search"""
        try:
            from scraping_agent import get_scraping_agent
            
            scraper = get_scraping_agent()
            results = await scraper.search(query, num_results)
            
            return {
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            raise Exception(f"Web search failed: {e}")

    async def write_research_document(
        self,
        title: str,
        sections: List[str],
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate a formatted HTML research document and open it"""
        import time as _time
        import webbrowser
        
        sections_html = ""
        for section in sections:
            lines = section.strip().split('\n')
            section_html = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('## '):
                    section_html += f'<h2 style="color:#00d4ff;font-family:Orbitron,monospace;font-size:18px;margin:24px 0 8px;letter-spacing:1px;">{line[3:]}</h2>'
                elif line.startswith('# '):
                    section_html += f'<h2 style="color:#00d4ff;font-family:Orbitron,monospace;font-size:20px;margin:24px 0 10px;">{line[2:]}</h2>'
                elif line.startswith('- ') or line.startswith('* '):
                    section_html += f'<li style="margin:4px 0;color:#ccc;">{line[2:]}</li>'
                else:
                    section_html += f'<p style="font-size:14px;line-height:1.8;color:#d0d0d0;margin:8px 0;">{line}</p>'
            sections_html += f'<div style="margin-bottom:24px;">{section_html}</div>'
        
        sources_html = ""
        if sources:
            sources_html = '<h2 style="color:#ffd700;font-family:Orbitron,monospace;font-size:16px;margin:32px 0 12px;letter-spacing:1px;">Sources</h2><ul style="padding-left:20px;">'
            for src in sources:
                sources_html += f'<li style="margin:6px 0;"><a href="{src}" style="color:#00d4ff;text-decoration:none;">{src}</a></li>'
            sources_html += '</ul>'
        
        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{title} — NeuroSurf Research</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Orbitron:wght@500;700&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Inter',sans-serif; background:#0a0a1a; color:#e0e0e0; max-width:820px; margin:0 auto; padding:48px 36px; line-height:1.8; }}
h1 {{ font-family:'Orbitron',monospace; color:#00d4ff; font-size:28px; margin-bottom:6px; text-shadow:0 0 20px rgba(0,212,255,0.3); }}
.meta {{ color:rgba(255,255,255,0.35); font-size:12px; margin-bottom:36px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:16px; }}
ul {{ padding-left:20px; }}
a {{ color:#00d4ff; }}
a:hover {{ text-decoration:underline; }}
.footer {{ margin-top:48px; padding-top:16px; border-top:1px solid rgba(255,255,255,0.08); color:rgba(255,255,255,0.25); font-size:11px; text-align:center; }}
@media print {{ body {{ background:#fff; color:#222; }} h1,h2 {{ color:#1a1a2e; }} .meta {{ color:#888; }} a {{ color:#0066cc; }} }}
</style></head><body>
<h1>{title}</h1>
<p class="meta">NeuroSurf AI Research Report</p>
{sections_html}
{sources_html}
<div class="footer">Generated by NeuroSurf — Open in Google Docs or Ctrl+P to save as PDF</div>
</body></html>"""
        
        export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        safe_title = ''.join(c if c.isalnum() or c in ' _-' else '' for c in title)[:50].strip().replace(' ', '_')
        filename = f"{safe_title}_{int(_time.time())}.html"
        filepath = os.path.join(export_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"📄 Research document saved: {filepath}")
        
        try:
            webbrowser.open(f'file:///{filepath.replace(os.sep, "/")}')
        except Exception as e:
            logger.warning(f"Could not auto-open: {e}")
        
        return {
            "action": "research_document_created",
            "path": filepath,
            "title": title,
            "sections_count": len(sections)
        }

    async def write_research_pdf(
        self,
        title: str,
        sections: List[str],
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate a professionally formatted PDF research document and open it"""
        import time as _time
        from fpdf import FPDF
        import os
        
        class PDF(FPDF):
            def header(self):
                self.set_fill_color(10, 10, 30)
                self.rect(0, 0, 210, 40, 'F')
                self.set_font("helvetica", "B", 24)
                self.set_text_color(0, 212, 255)
                self.cell(0, 15, title[:40].upper(), border=0, ln=1, align="C")
                self.set_font("helvetica", "I", 10)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, "NeuroSurf Neural Analytics Report", border=0, ln=1, align="C")
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font("helvetica", "I", 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, f"Page {self.page_no()} | Generated by Neuro Assistant on {os.environ.get('COMPUTERNAME', 'LocalNode')}", align="C")

        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Body styling
        pdf.set_font("helvetica", size=11)
        pdf.set_text_color(40, 40, 40)
        
        for section in sections:
            lines = section.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    pdf.ln(4)
                    continue
                
                if line.startswith('## '):
                    pdf.ln(8)
                    pdf.set_font("helvetica", "B", 16)
                    pdf.set_text_color(0, 100, 200)
                    pdf.cell(0, 10, line[3:], ln=1)
                    pdf.set_draw_color(0, 212, 255)
                    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
                    pdf.ln(4)
                elif line.startswith('# '):
                    pdf.ln(10)
                    pdf.set_font("helvetica", "B", 20)
                    pdf.set_text_color(0, 50, 150)
                    pdf.cell(0, 12, line[2:], ln=1)
                    pdf.ln(5)
                elif line.startswith('- ') or line.startswith('* '):
                    pdf.set_font("helvetica", size=11)
                    pdf.set_text_color(60, 60, 60)
                    pdf.set_x(15)
                    pdf.multi_cell(0, 7, f"• {line[2:]}")
                else:
                    pdf.set_font("helvetica", size=11)
                    pdf.set_text_color(40, 40, 40)
                    pdf.multi_cell(0, 7, line)
            pdf.ln(10)

        if sources:
            pdf.ln(10)
            pdf.set_font("helvetica", "B", 14)
            pdf.set_text_color(255, 100, 0)
            pdf.cell(0, 10, "SOURCES", ln=1)
            pdf.set_font("helvetica", size=9)
            pdf.set_text_color(0, 0, 255)
            for src in sources:
                pdf.cell(0, 6, src, ln=1, link=src)

        export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        safe_title = ''.join(c if c.isalnum() or c in ' _-' else '' for c in title)[:50].strip().replace(' ', '_')
        filename = f"{safe_title}_{int(_time.time())}.pdf"
        filepath = os.path.join(export_dir, filename)
        
        pdf.output(filepath)
        logger.info(f"PDF Research document saved: {filepath}")
        
        import webbrowser
        try:
            webbrowser.open(f'file:///{filepath.replace(os.sep, "/")}')
        except Exception as e:
            logger.warning(f"Could not auto-open PDF: {e}")
            
        return {
            "action": "research_pdf_created",
            "path": filepath,
            "title": title
        }
    
    # ==================== Browser Operations ====================
    
    async def browser_open_tab(
        self,
        url: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Open a new tab in the browser
        Returns the command to be sent to frontend
        """
        logger.info(f"🌐 Opening tab: {url}")
        
        # This returns an action that main.py will emit to frontend
        return {
            "action": "browser_new_tab",
            "url": url,
            "title": title or url,
            "status": "command_queued"
        }
    
    # ==================== Sub-Agent Spawning ====================
    
    async def spawn_task_agent(
        self,
        task: str,
        urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Spawn a sub-agent for a specific task
        
        Args:
            task: Task description
            urls: Optional URLs to process
            
        Returns:
            Task results
        """
        try:
            from scraping_agent import get_scraping_agent
            from .context_memory import get_context_memory
            
            logger.info(f"🤖 Spawning sub-agent for: {task}")
            
            results = {"task": task, "results": []}
            scraper = get_scraping_agent()
            memory = get_context_memory()
            
            # If URLs provided, scrape them
            if urls:
                for url in urls[:5]:  # Limit to 5 URLs
                    try:
                        scraped = await scraper.scrape(url, extract_text=True)
                        if scraped.get("success"):
                            results["results"].append({
                                "url": url,
                                "title": scraped.get("title", ""),
                                "text_preview": scraped.get("text", "")[:500]
                            })
                    except Exception as e:
                        results["results"].append({
                            "url": url,
                            "error": str(e)
                        })
            
            # Optional: Use LLM to synthesize findings if we have data
            summary = ""
            if results["results"]:
                context = "\n".join([f"Source: {r['url']}\nContent: {r['text_preview']}" for r in results["results"]])
                prompt = f"Summarize the following research data for the task: {task}\n\n{context}\n\nSummary:"
                
                try:
                    import ollama
                    response = ollama.generate(model='qwen2.5:3b', prompt=prompt)
                    summary = response.get('response', '')
                    results["summary"] = summary
                except:
                    results["summary"] = "Data gathered but synthesis failed."
            
            # Store task result in context memory
            await memory.store_task_result(
                task=task,
                result=summary or f"Processed {len(results['results'])} items",
                actions=[f"Scraped {url.get('url', 'unknown')}" for url in results["results"]]
            )
            
            results["status"] = "completed"
            return results
            
        except Exception as e:
            logger.error(f"Sub-agent failed: {e}")
            raise Exception(f"Sub-agent task failed: {e}")

