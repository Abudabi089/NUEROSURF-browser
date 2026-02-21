import asyncio
import logging
from mcp.server.fastmcp import FastMCP
from browser_agent import BrowserAgent

# Initialize Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('NeuroSurf.MCP')

# Initialize Browser Agent
agent = BrowserAgent()

# Create MCP Server
mcp = FastMCP("NeuroSurf Chrome Agent")

@mcp.tool()
async def navigate(url: str) -> str:
    """Navigate the browser to a specific URL."""
    if not agent.page:
        await agent.initialize(headless=False)
    
    result = await agent.navigate(url)
    return f"Navigated to {result['url']} - Title: {result['title']}"

@mcp.tool()
async def click(element_description: str) -> str:
    """Click an element on the page described by text."""
    if not agent.page:
        return "Error: Browser not initialized. Navigate first."

    element = await agent.find_element(element_description)
    if element:
        success = await agent.click(element)
        return "Clicked successfully" if success else "Failed to click"
    return f"Element '{element_description}' not found"

@mcp.tool()
async def type_text(element_description: str, text: str) -> str:
    """Type text into an input field described by text."""
    if not agent.page:
        return "Error: Browser not initialized. Navigate first."

    element = await agent.find_element(element_description)
    if element:
        success = await agent.type_text(element, text)
        return f"Typed '{text}' successfully" if success else "Failed to type"
    return f"Element '{element_description}' not found"

@mcp.tool()
async def get_page_content() -> str:
    """Get the text content of the current page."""
    if not agent.page:
        return "Error: Browser not initialized."
    
    content = await agent.get_page_content()
    return content['text'][:5000]  # Return first 5000 chars

@mcp.tool()
async def screenshot() -> str:
    """Take a screenshot of the current page."""
    if not agent.page:
        return "Error: Browser not initialized."
    
    path = await agent.screenshot()
    return f"Screenshot saved to {path}"

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
