"""
NeuroSurf Neural Backend - Neuro AI Assistant
Uses Ollama LLM (Nemotron) & Local Speech Recognition
AUTONOMOUS AGENT with full tool access
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import uvicorn
import re
import ollama
import os
import subprocess
import shutil
import platform
import json
import sys
import time

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from pathlib import Path
NEUROSURF_ROOT = Path(__file__).parent.parent.resolve()

from autonomous_agent import AutonomousAgent, get_agent, get_ollama_client
from memory import MemoryStore

# Speech Recognition
try:
    import speech_recognition as sr
    speech_available = True
except ImportError:
    speech_available = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Neuro')

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*', logger=False, engineio_logger=False)

# Fast model optimized for CPU (Intel i5-13th gen / Iris Xe)
MODEL = 'qwen2.5:3b'

# Initialize memory store
memory_store = None
# Multi-Thread Management
thread_agents = {}
autonomous_agent = None

# Voice State
recognizer = None
mic = None
if speech_available:
    recognizer = sr.Recognizer()
    try:
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
    except Exception as e:
        logger.error(f"Microphone error: {e}")
        speech_available = False


def extract_url(text: str) -> str:
    """Simple extraction of URL or search term from command"""
    text = text.lower()
    match = re.match(r'^(open|browse|go to|show me)\s+(.+)', text)
    if match:
        target = match.group(2).strip()
        if target.startswith('http'):
            return target
        if '.' in target and ' ' not in target: # naive "is domain" check
            return f"https://{target}"
        return f"https://www.google.com/search?q={target.replace(' ', '+')}"
    return None


async def agent_callback(message: str, msg_type: str, sid: str, thread_id: str = 'main'):
    """Callback for agent to send updates to frontend"""
    await sio.emit('agent:thought', {'text': message, 'type': msg_type, 'thread_id': thread_id}, room=sid)


async def listen_to_mic(sid):
    """Listen to microphone using Python SpeechRecognition"""
    global recognizer, mic
    
    if not speech_available or not mic:
        await sio.emit('agent:thought', {'text': 'Voice error: Microphone not available on server', 'type': 'error'}, room=sid)
        await sio.emit('voice:stop', room=sid)
        return

    logger.info("🎤 Listening...")
    await sio.emit('agent:thought', {'text': '🎤 Listening...', 'type': 'voice'}, room=sid)
    
    try:
        with mic as source:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        
        logger.info("🎤 Processing audio...")
        await sio.emit('agent:thought', {'text': '🎤 Processing...', 'type': 'voice'}, room=sid)
        
        try:
            text = recognizer.recognize_google(audio)
            logger.info(f"🎤 Heard: {text}")
            await sio.emit('agent:thought', {'text': f'🎤 You: "{text}"', 'type': 'voice'}, room=sid)
            await agent_command(sid, {'command': text})
            
        except sr.UnknownValueError:
            await sio.emit('agent:thought', {'text': '🎤 Could not understand audio', 'type': 'error'}, room=sid)
        except sr.RequestError as e:
            await sio.emit('agent:thought', {'text': f'🎤 Speech service error: {e}', 'type': 'error'}, room=sid)
            
    except Exception as e:
        logger.error(f"Voice catch error: {e}")
        await sio.emit('agent:thought', {'text': '🎤 Listening timed out', 'type': 'error'}, room=sid)
    
    await sio.emit('voice:stop', room=sid)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global memory_store, thread_agents
    thread_agents = {}
    
    logger.info("="*50)
    logger.info("  🧠 NEURO - Autonomous AI Agent (Nemotron Powered)")
    logger.info(f"  📦 Model: {MODEL}")
    logger.info("="*50)
    
    # Initialize memory store
    try:
        memory_store = MemoryStore()
        memory_store.initialize()
        logger.info("  💾 Memory store initialized")
    except Exception as e:
        logger.error(f"Memory store init failed: {e}")
        memory_store = None
    
    # Initialize primary agent for 'main' thread
    thread_agents['main'] = AutonomousAgent(memory_store=memory_store)
    logger.info("  🤖 Primary Autonomous Agent ready")
    
    # Warm up the model - force Ollama to load it into memory
    logger.info("  🔥 Warming up LLM (preloading into memory)...")
    try:
        client = get_ollama_client()
        await client.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': 'hi'}],
            keep_alive='5m',
            options={'num_predict': 1, 'num_ctx': 32}
        )
        logger.info("  ✅ Model preloaded and ready")
    except Exception as e:
        logger.warning(f"  ⚠️ Model warm-up failed: {e}")
    
    yield
    
    # Cleanup
    if memory_store:
        memory_store.shutdown()

app = FastAPI(title="Neuro", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)


@sio.event
async def connect(sid, environ):
    logger.info(f"✅ Client connected: {sid}")
    await sio.emit('agent:state', {'state': 'idle'}, room=sid)
    await sio.emit('agent:thought', {'text': f'🧠 Neuro ready! (Nemotron Autonomous Agent)', 'type': 'system'}, room=sid)


@sio.event
async def disconnect(sid):
    logger.info(f"❌ Disconnected: {sid}")


@sio.event
async def webcam_frame(sid, data):
    """Receive and save webcam frame from frontend"""
    try:
        frame_data = data.get('frame')
        if not frame_data: return
        
        # Remove header if present
        if ',' in frame_data:
            frame_data = frame_data.split(',')[1]
            
        import base64
        image_bytes = base64.b64decode(frame_data)
        
        webcam_dir = NEUROSURF_ROOT / "data" / "webcam"
        webcam_dir.mkdir(parents=True, exist_ok=True)
        
        with open(webcam_dir / "current_frame.jpg", "wb") as f:
            f.write(image_bytes)
            
    except Exception as e:
        logger.error(f"Failed to save webcam frame: {e}")


async def perform_research(sid, query, thread_id='main'):
    """
    Direct research pipeline — bypasses the LLM agent loop.
    Steps: web_search → web_scrape top results → LLM summarize → write_research_document
    """
    from agent_tools import AgentTools
    
    tools = AgentTools(memory_store=memory_store)
    
    try:
        # Step 1: Web Search
        await sio.emit('agent:thought', {
            'text': f'🔍 Searching the web for: {query}',
            'type': 'system', 'thread_id': thread_id
        }, room=sid)
        
        search_result = await tools.web_search(query=query, num_results=5)
        results = search_result.get('results', [])
        
        if not results:
            await sio.emit('agent:thought', {
                'text': '❌ No search results found. Try a different query.',
                'type': 'error', 'thread_id': thread_id
            }, room=sid)
            return
        
        await sio.emit('agent:thought', {
            'text': f'📊 Found {len(results)} results. Scraping top pages...',
            'type': 'system', 'thread_id': thread_id
        }, room=sid)
        
        # Step 2: Scrape top 3 results
        scraped_content = []
        source_urls = []
        
        for i, r in enumerate(results[:3]):
            # Support multiple possible key names from different search backends
            url = r.get('url') or r.get('href') or r.get('link', '')
            title = r.get('title', f'Result {i+1}')
            snippet = r.get('snippet') or r.get('body') or r.get('description', '')
            
            if not url:
                # Use snippet if URL missing but title exists
                if snippet and title:
                    scraped_content.append(f"### {title}\n{snippet}")
                continue
                
            source_urls.append(url)
            
            try:
                scrape_result = await tools.web_scrape(url=url)
                text = scrape_result.get('text', '') or scrape_result.get('content', '') or snippet
                # Limit each page to ~2000 chars to keep LLM context manageable but informative
                if len(text) > 2000:
                    text = text[:2000] + '...'
                scraped_content.append(f"### {title}\nSource: {url}\n{text}")
                
                await sio.emit('agent:thought', {
                    'text': f'📄 Scraped ({i+1}/3): {title[:50]}',
                    'type': 'system', 'thread_id': thread_id
                }, room=sid)
            except Exception as e:
                logger.warning(f"Scrape failed for {url}: {e}")
                if snippet:
                    scraped_content.append(f"### {title}\nSource: {url}\n{snippet}")
        
        if not scraped_content:
            # Fall back to using search snippets as content if scraping failed
            for r in results[:5]:
                title = r.get('title', 'Result')
                url = r.get('url') or r.get('href') or ''
                snippet = r.get('snippet') or r.get('body') or r.get('description', '')
                if snippet:
                    scraped_content.append(f"### {title}\nURL: {url}\n{snippet}")
        
        # Step 3: Use LLM to summarize scraped content into sections
        await sio.emit('agent:thought', {
            'text': '🧠 Analyzing and organizing findings...',
            'type': 'system', 'thread_id': thread_id
        }, room=sid)
        
        combined_text = '\n\n'.join(scraped_content)
        # Keep combined text under 3000 chars for the 3B model
        if len(combined_text) > 3000:
            combined_text = combined_text[:3000] + '\n...(truncated)'
        
        summarize_prompt = f"""Summarize the following research about "{query}" into clearly organized sections.
Format: Use ## for section headings. Write 2-3 sentences per section. Include 4-6 sections.
Do NOT use any JSON or tool calls. Just write the sections directly.

RESEARCH DATA:
{combined_text}

FORMATTED SUMMARY:"""

        try:
            client = get_ollama_client()
            summary_response = ""
            async for chunk in await client.chat(
                model=MODEL,
                messages=[
                    {'role': 'system', 'content': 'You are a research summarizer. Write clear, factual summaries organized with ## headings. No tool calls, no JSON.'},
                    {'role': 'user', 'content': summarize_prompt}
                ],
                stream=True,
                keep_alive='5m',
                options={'temperature': 0.3, 'num_predict': 600, 'num_ctx': 4096, 'num_batch': 256, 'num_thread': 8}
            ):
                summary_response += chunk.get('message', {}).get('content', '')
            
            summary_response = summary_response.strip()
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            # Fallback: use raw scraped content as sections
            summary_response = combined_text
        
        # Step 4: Parse summary into sections
        sections = []
        if summary_response:
            # Try to split by markdown headers
            parts = summary_response.split('\n## ')
            if len(parts) > 1:
                # The first part might be an intro before any ##
                if parts[0].strip() and not parts[0].strip().startswith('#'):
                    sections.append(f"## Overview\n{parts[0].strip()}")
                
                for part in parts[1:]:
                    sections.append(f"## {part}")
            else:
                # No headings found — wrap entire response as one section
                sections = [f"## Research Findings\n{summary_response}"]
        
        if not sections:
            sections = [f"## Research Summary\n{summary_response}"]
        
        # Step 4: Create PDF document
        await sio.emit('agent:thought', {
            'text': '📄 Formatting findings into a PDF document...',
            'type': 'system', 'thread_id': thread_id
        }, room=sid)
        
        try:
            pdf_result = await tools.write_research_pdf(
                title=f"Research: {query}",
                sections=sections,
                sources=source_urls
            )
            
            await sio.emit('agent:thought', {
                'text': f'✅ Research PDF created and opened! (Stored in exports folder)',
                'type': 'system', 'thread_id': thread_id
            }, room=sid)
            
            # Emit tool results for frontend awareness
            await sio.emit('agent:tool_action', {
                'tool': 'write_research_pdf',
                'action': 'created',
                'path': pdf_result.get('path'),
                'thread_id': thread_id
            }, room=sid)
            
        except Exception as e:
            logger.error(f"Failed to create research PDF: {e}")
            await sio.emit('agent:thought', {
                'text': f'❌ Failed to create PDF: {str(e)[:100]}. Check console for details.',
                'type': 'error', 'thread_id': thread_id
            }, room=sid)
            
    except Exception as e:
        logger.error(f"Research pipeline error: {e}")
        await sio.emit('agent:thought', {
            'text': f'❌ Research failed: {str(e)}',
            'type': 'error', 'thread_id': thread_id
        }, room=sid)
    finally:
        await sio.emit('agent:state', {'state': 'idle', 'thread_id': thread_id}, room=sid)


@sio.event
async def agent_command(sid, data):
    """Main command handler - routes to autonomous agent"""
    global thread_agents, memory_store
    
    # Set agent to acting state
    await sio.emit('agent:state', {'state': 'acting'}, room=sid)
    
    command = data.get('command', '').strip()
    thread_id = data.get('thread_id', 'main')
    if not command: return
    
    logger.info(f"💬 Thread[{thread_id}] User: {command}")
    
    # Check for direct browser commands FIRST (for quick navigation)
    # Skip navigation check if it's an internal RESEARCH TASK
    target_url = None if command.startswith("RESEARCH TASK:") else extract_url(command)
    
    if target_url:
        logger.info(f"🌐 Navigating to: {target_url}")
        await sio.emit('browser_navigate', {'url': target_url}, room=sid)
        await sio.emit('agent:thought', {'text': f'🌐 Opening {target_url}...', 'type': 'action', 'thread_id': thread_id}, room=sid)
        return

    # Check for intense research keyword or manual trigger
    command_lower = command.lower()
    is_research = any(kw in command_lower for kw in ['research', 'deep study', 'investigate', 'search the web', 'browse for']) or "RESEARCH TASK:" in command
    
    # Route research to direct pipeline (bypasses unreliable LLM tool calling)
    if is_research:
        # Extract the actual query
        if "RESEARCH TASK:" in command:
            # Extract query from: RESEARCH TASK: Research "quantum computing". 1. Use web_search...
            import re as _re
            match = _re.search(r'Research\s+"([^"]+)"', command)
            if match:
                research_query = match.group(1)
            else:
                research_query = command.split("RESEARCH TASK:")[-1].strip()[:100]
        else:
            # Strip research keywords from the raw command
            research_query = command_lower
            for kw in ['research', 'deep study', 'investigate', 'search the web for', 'search the web', 'browse for']:
                research_query = research_query.replace(kw, '').strip()
            research_query = research_query.strip(' "\'') or command
        
        logger.info(f"🔬 Research pipeline: {research_query}")
        # Run asynchronously so the client doesn't block
        asyncio.create_task(perform_research(sid, research_query, thread_id))
        return

    # If NOT a research task and NOT a complex multi-step command, use simple chatbot mode
    if len(command) < 150:
        logger.info(f"🤖 Simple Chatbot Mode: {command}")
        await sio.emit('agent:thought', {'text': '◌ Thinking...', 'type': 'system', 'thread_id': thread_id}, room=sid)
        
        response_id = int(time.time() * 1000)
        full_response = ""
        
        try:
            client = get_ollama_client()
            async for chunk in await client.chat(
                model=MODEL,
                messages=[{'role': 'system', 'content': "You are Neuro, a helpful AI assistant. Be concise and friendly."}, 
                         {'role': 'user', 'content': command}],
                stream=True,
                keep_alive='5m',
                options={'temperature': 0.5, 'num_predict': 300, 'num_ctx': 2048, 'num_batch': 256, 'num_thread': 8}
            ):
                text_chunk = chunk.get('message', {}).get('content', '')
                full_response += text_chunk
                await sio.emit('agent:thought_chunk', {
                    'id': response_id,
                    'chunk': text_chunk,
                    'type': 'system',
                    'thread_id': thread_id
                }, room=sid)
                
            # Final sync
            await sio.emit('agent:thought', {'id': response_id, 'text': f'🤖 {full_response.strip()}', 'type': 'system', 'thread_id': thread_id}, room=sid)
            await sio.emit('agent:state', {'state': 'idle', 'thread_id': thread_id}, room=sid)
            return

        except Exception as e:
            if "connection" in str(e).lower():
                err_msg = "❌ Ollama not found. Please ensure Ollama is running on your system."
            else:
                err_msg = f"❌ LLM Error: {e}"
            logger.error(f"Chatbot error: {e}")
            await sio.emit('agent:thought', {'text': err_msg, 'type': 'error', 'thread_id': thread_id}, room=sid)
            await sio.emit('agent:state', {'state': 'idle', 'thread_id': thread_id}, room=sid)
            return

    # Check for halt command
    if command.lower() in ['stop', 'halt', 'cancel', 'abort']:
        thread_id = data.get('thread_id', 'main')
        if thread_id in thread_agents:
            thread_agents[thread_id].halt()
        await sio.emit('agent:thought', {'text': '🛑 Agent halted', 'type': 'system', 'thread_id': thread_id}, room=sid)
        return

    # Check for MCP command
    if "start mcp" in command.lower() or "enable mcp" in command.lower():
        mcp_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agent', 'chrome_mcp.py')
        try:
            if sys.platform == 'win32':
                subprocess.Popen(['start', 'cmd', '/k', sys.executable, mcp_path], shell=True)
            else:
                subprocess.Popen(['x-terminal-emulator', '-e', f'{sys.executable} {mcp_path}'])
                
            await sio.emit('agent:thought', {'text': '🚀 Starting Chrome MCP Server...', 'type': 'system', 'thread_id': thread_id}, room=sid)
            return
        except Exception as e:
            logger.error(f"Failed to start MCP: {e}")
            await sio.emit('agent:thought', {'text': f'❌ Failed to start MCP: {e}', 'type': 'error', 'thread_id': thread_id}, room=sid)
            return

    # Route to autonomous agent for complex tasks (Thread-Aware)
    thread_id = data.get('thread_id', 'main')
    
    if thread_id not in thread_agents:
        thread_agents[thread_id] = AutonomousAgent(memory_store=memory_store)
        
    current_agent = thread_agents[thread_id]
    
    if current_agent:
        try:
            # Immediate responsive feedback
            await sio.emit('agent:thought', {
                'text': '◌ Neural Link Active. Processing...', 
                'type': 'system', 
                'thread_id': thread_id
            }, room=sid)

            # Create callback that includes sid and thread_id
            async def callback(msg, msg_type):
                await agent_callback(msg, msg_type, sid, thread_id=thread_id)
                
            # Create unique ID for the final response block
            response_id = int(time.time() * 1000)
            
            async def on_chunk(chunk):
                await sio.emit('agent:thought_chunk', {
                    'id': response_id,
                    'chunk': chunk,
                    'type': 'system',
                    'thread_id': thread_id
                }, room=sid)
            
            # Start processing immediately

            result = await current_agent.process_task(command, callback=callback, on_chunk=on_chunk)
            
            # Send final response (ensure the final block is fully sync'd)
            response = result.get('response', 'Task completed.')
            await sio.emit('agent:thought', {
                'id': response_id, 
                'text': f'🤖 {response}', 
                'type': 'system',
                'thread_id': thread_id
            }, room=sid)


            # Emit tool actions if any
            actions = result.get('actions', [])
            if actions:
                await sio.emit('agent:actions', {'actions': actions, 'thread_id': thread_id}, room=sid)
                
                # Check for terminal output to send to Terminal View (F3)
                for action in actions:
                    tool = action.get('tool')
                    result_data = action.get('result', {})
                    
                    if tool == 'terminal_execute':
                        output = result_data.get('stdout', '') + result_data.get('stderr', '')
                        if output:
                            await sio.emit('terminal:output', {'output': output}, room=sid)
                    
                    elif tool == 'browser_open_tab':
                        # The tool returns an action block directly
                        if result_data.get('action') == 'browser_new_tab':
                            await sio.emit('browser:new_tab', {
                                'url': result_data.get('url'),
                                'title': result_data.get('title')
                            }, room=sid)
                    
                    elif tool == 'write_research_document':
                        if result_data.get('action') == 'research_document_created':
                            await sio.emit('agent:thought', {
                                'text': f"📄 Research document created: {result_data.get('title', 'Research')}",
                                'type': 'system',
                                'thread_id': thread_id
                            }, room=sid)
                    
                    elif tool == 'spawn_task_agent':
                        # Send specialized agent results to thought stream
                        agent_task = action.get('parameters', {}).get('task', 'Specialized Task')
                        await sio.emit('agent:thought', {
                            'text': f'🧪 Specialized Agent finished: {agent_task}',
                            'type': 'system',
                            'thread_id': thread_id
                        }, room=sid)

        except Exception as e:
            logger.error(f"Agent error: {e}")
            await sio.emit('agent:thought', {
                'text': f'❌ Error: {str(e)}', 
                'type': 'error',
                'thread_id': thread_id
            }, room=sid)
        finally:
            await sio.emit('agent:state', {'state': 'idle', 'thread_id': thread_id}, room=sid)
    else:
        # Fallback to simple LLM query with non-blocking streaming
        response_id = int(time.time() * 1000)
        full_response = ""
        
        try:
            client = get_ollama_client()
            async for chunk in await client.chat(
                model=MODEL,
                messages=[{'role': 'user', 'content': command}],
                stream=True,
                keep_alive='5m',
                options={'temperature': 0.5, 'num_predict': 300, 'num_ctx': 2048, 'num_batch': 256, 'num_thread': 8}
            ):
                text_chunk = chunk.get('message', {}).get('content', '')
                full_response += text_chunk
                await sio.emit('agent:thought_chunk', {
                    'id': response_id,
                    'chunk': text_chunk,
                    'type': 'system'
                }, room=sid)
                
            # Final sync
            await sio.emit('agent:thought', {'id': response_id, 'text': f'🤖 {full_response.strip()}', 'type': 'system'}, room=sid)
            
        except Exception as e:
            logger.error(f"Ollama fallback error: {e}")
            await sio.emit('agent:thought', {'text': f'❌ LLM Error: {e}', 'type': 'error'}, room=sid)



@sio.event
async def analyze_page(sid, data):
    """Analyze page content sent from frontend"""
    text = data.get('text', '')[:2000]
    if not text: return

    logger.info(f"📄 Analyzing page content ({len(text)} chars)...")
    
    loop = asyncio.get_event_loop()
    
    def summarize():
        try:
            response = ollama.generate(
                model=MODEL,
                prompt=f"Summarize this web page content in one concise sentence:\n\n{text}",
                options={'temperature': 0.3, 'num_predict': 60, 'num_ctx': 2048, 'num_batch': 256, 'num_thread': 8}
            )
            return response.get('response', '').strip()
        except Exception as e:
            logger.error(f"Ollama Summarize Error: {e}")
            return "Could not summarize page."

    try:
        summary = await loop.run_in_executor(None, summarize)
        logger.info(f"📄 Summary: {summary}")
        await sio.emit('agent:thought', {'text': f'💡 Page Insight: {summary}', 'type': 'system'}, room=sid)
    except Exception as e:
        logger.error(f"Analysis error: {e}")


@sio.event
async def voice_start(sid):
    """Start listening on backend"""
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, lambda: asyncio.run(listen_to_mic(sid)))


@sio.event
async def voice_stop(sid):
    pass


# --- Agent Tool Events (for direct frontend tool requests) ---

@sio.event
async def agent_tool(sid, data):
    """Execute a specific agent tool directly"""
    global autonomous_agent
    
    tool_name = data.get('tool', '')
    parameters = data.get('parameters', {})
    
    if not tool_name:
        await sio.emit('agent:tool_result', {'error': 'No tool specified'}, room=sid)
        return
    
    if autonomous_agent:
        try:
            result = await autonomous_agent.tools.execute_tool(tool_name, parameters)
            await sio.emit('agent:tool_result', {'tool': tool_name, 'result': result}, room=sid)
        except Exception as e:
            await sio.emit('agent:tool_result', {'tool': tool_name, 'error': str(e)}, room=sid)


@sio.event
async def screenshot_data(sid, data):
    """Receive screenshot data from Electron frontend"""
    global autonomous_agent
    
    image_data = data.get('image', '')
    if not image_data:
        return
    
    # Store for agent to use
    if autonomous_agent and autonomous_agent.tools:
        autonomous_agent.tools._pending_screenshot = image_data
        logger.info("📸 Screenshot received from frontend")


# --- Terminal & File System Integration (legacy, kept for compatibility) ---

@sio.event
async def terminal_command(sid, data):
    """Execute a shell command and return output"""
    command = data.get('command', '')
    if not command: return
    
    logger.info(f"🐚 Terminal Command: {command}")
    
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(timeout=30)
        
        output = stdout if stdout else stderr
        await sio.emit('terminal:output', {'output': output, 'returnCode': process.returncode}, room=sid)
    except Exception as e:
        await sio.emit('terminal:output', {'output': f"Error: {str(e)}", 'returnCode': -1}, room=sid)


@sio.event
async def fs_list(sid, data):
    """List directory contents"""
    path = data.get('path', '.')
    try:
        abs_path = os.path.abspath(path)
        items = os.listdir(abs_path)
        result = []
        for item in items:
            full = os.path.join(abs_path, item)
            result.append({
                'name': item,
                'isDir': os.path.isdir(full),
                'size': os.path.getsize(full) if os.path.isfile(full) else 0
            })
        await sio.emit('fs:list_result', {'path': abs_path, 'items': result}, room=sid)
    except Exception as e:
        await sio.emit('fs:error', {'message': str(e)}, room=sid)


@sio.event
async def fs_read(sid, data):
    """Read file content"""
    path = data.get('path', '')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        await sio.emit('fs:read_result', {'path': path, 'content': content}, room=sid)
    except Exception as e:
        await sio.emit('fs:error', {'message': str(e)}, room=sid)


@sio.event
async def fs_write(sid, data):
    """Write file content"""
    path = data.get('path', '')
    content = data.get('content', '')
    try:
        if path.endswith(('.exe', '.dll', '.sys')):
             raise Exception("Writing to system files is restricted.")
             
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        await sio.emit('fs:write_result', {'path': path, 'status': 'success'}, room=sid)
    except Exception as e:
        await sio.emit('fs:error', {'message': str(e)}, room=sid)


if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8000, log_level="info")
