"""
Browser Agent - Playwright-based web automation with vision fallback
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright.async_api import async_playwright, Page as AsyncPage

from vision_helper import VisionHelper

logger = logging.getLogger('NeuroSurf.BrowserAgent')


class BrowserAgent:
    """
    Playwright-based browser automation agent
    Features:
    - Standard DOM-based element selection
    - Vision fallback using LLaVA for screenshots
    - Coordinate-based clicking for canvas/non-DOM elements
    """
    
    def __init__(self, vision_helper: Optional[VisionHelper] = None):
        """
        Initialize browser agent
        
        Args:
            vision_helper: VisionHelper instance for screenshot analysis
        """
        self.vision = vision_helper or VisionHelper()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[AsyncPage] = None
        self.screenshot_dir = Path("./data/screenshots")
        
    async def initialize(self, headless: bool = False):
        """
        Initialize the browser
        
        Args:
            headless: Run browser in headless mode
        """
        logger.info("🌐 Initializing Browser Agent...")
        
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
        logger.info("  ✅ Browser ready")
        
    async def shutdown(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("🌐 Browser Agent shutdown")
        
    async def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL
        
        Args:
            url: Target URL
            
        Returns:
            Navigation result with page info
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        logger.info(f"  → Navigating to: {url}")
        
        response = await self.page.goto(url, wait_until='networkidle')
        title = await self.page.title()
        
        return {
            "url": self.page.url,
            "title": title,
            "status": response.status if response else None
        }
    
    async def find_element(
        self,
        description: str,
        use_vision: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Find an element on the page by description
        Uses DOM selectors first, falls back to vision if needed
        
        Args:
            description: Natural language description of element
            use_vision: Whether to use vision fallback
            
        Returns:
            Element info with selector or coordinates
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        # Step 1: Try common selector patterns
        selectors = self._generate_selectors(description)
        
        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    box = await element.bounding_box()
                    return {
                        "method": "selector",
                        "selector": selector,
                        "box": box
                    }
            except Exception:
                continue
        
        # Step 2: Vision fallback
        if use_vision:
            return await self._vision_find_element(description)
        
        return None
    
    def _generate_selectors(self, description: str) -> List[str]:
        """Generate CSS selectors from natural language description"""
        desc_lower = description.lower()
        selectors = []
        
        # Common button patterns
        if 'button' in desc_lower or 'btn' in desc_lower or 'click' in desc_lower:
            words = description.split()
            for word in words:
                if word.lower() not in ('button', 'btn', 'the', 'a', 'click'):
                    selectors.extend([
                        f'button:has-text("{word}")',
                        f'[type="submit"]:has-text("{word}")',
                        f'a:has-text("{word}")',
                        f'.btn:has-text("{word}")',
                    ])
        
        # Input fields
        if 'input' in desc_lower or 'field' in desc_lower or 'search' in desc_lower:
            selectors.extend([
                'input[type="text"]',
                'input[type="search"]',
                'input[placeholder*="search" i]',
                'textarea',
            ])
        
        # Links
        if 'link' in desc_lower:
            words = [w for w in description.split() if w.lower() != 'link']
            for word in words:
                selectors.append(f'a:has-text("{word}")')
        
        # Generic text matching
        selectors.append(f'text="{description}"')
        selectors.append(f':has-text("{description}")')
        
        return selectors
    
    async def _vision_find_element(
        self,
        description: str
    ) -> Optional[Dict[str, Any]]:
        """
        Use vision model to find element by screenshot
        
        Args:
            description: Element description
            
        Returns:
            Element coordinates if found
        """
        logger.info(f"  👁️ Using vision to find: {description}")
        
        # Take screenshot
        screenshot_path = self.screenshot_dir / f"vision_{id(self)}.png"
        await self.page.screenshot(path=str(screenshot_path), full_page=False)
        
        # Use vision helper
        result = await self.vision.find_element_coordinates(
            str(screenshot_path),
            description
        )
        
        if result and result.get('found'):
            return {
                "method": "vision",
                "coordinates": result['coordinates'],
                "confidence": result.get('confidence', 0.5)
            }
        
        return None
    
    async def click(
        self,
        target: Dict[str, Any],
        button: str = 'left'
    ) -> bool:
        """
        Click on an element
        
        Args:
            target: Element info from find_element
            button: Mouse button to use
            
        Returns:
            True if click succeeded
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        try:
            if target.get('method') == 'selector':
                await self.page.click(target['selector'], button=button)
                logger.info(f"  ✓ Clicked selector: {target['selector']}")
                
            elif target.get('method') == 'vision':
                x, y = target['coordinates']
                await self.page.mouse.click(x, y, button=button)
                logger.info(f"  ✓ Clicked coordinates: ({x}, {y})")
                
            else:
                return False
            
            # Wait for any navigation or response
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False
    
    async def type_text(
        self,
        target: Dict[str, Any],
        text: str,
        delay: int = 50
    ) -> bool:
        """
        Type text into an element
        
        Args:
            target: Element info from find_element
            text: Text to type
            delay: Delay between keystrokes in ms
            
        Returns:
            True if typing succeeded
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        try:
            if target.get('method') == 'selector':
                await self.page.fill(target['selector'], text)
                logger.info(f"  ✓ Typed into selector: {target['selector']}")
                
            elif target.get('method') == 'vision':
                x, y = target['coordinates']
                await self.page.mouse.click(x, y)
                await self.page.keyboard.type(text, delay=delay)
                logger.info(f"  ✓ Typed at coordinates: ({x}, {y})")
                
            else:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return False
    
    async def get_page_content(self) -> Dict[str, Any]:
        """
        Get current page content and metadata
        
        Returns:
            Page content info
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        title = await self.page.title()
        content = await self.page.content()
        text = await self.page.inner_text('body')
        
        return {
            "url": self.page.url,
            "title": title,
            "html_length": len(content),
            "text": text[:10000] if len(text) > 10000 else text
        }
    
    async def screenshot(self, full_page: bool = False) -> str:
        """
        Take a screenshot
        
        Args:
            full_page: Capture full page or viewport
            
        Returns:
            Path to screenshot
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        path = self.screenshot_dir / f"screenshot_{int(asyncio.get_event_loop().time() * 1000)}.png"
        await self.page.screenshot(path=str(path), full_page=full_page)
        return str(path)
    
    async def execute_step(
        self,
        step: Dict[str, Any],
        callback=None
    ) -> Dict[str, Any]:
        """
        Execute a single task step
        
        Args:
            step: Step definition from task planner
            callback: Progress callback
            
        Returns:
            Step result
        """
        action = step.get('action', '')
        target = step.get('target', '')
        value = step.get('value', '')
        
        result = {"action": action, "status": "pending"}
        
        try:
            if action == 'navigate':
                nav_result = await self.navigate(target)
                result.update(nav_result)
                result['status'] = 'success'
                
            elif action == 'click':
                element = await self.find_element(target)
                if element:
                    success = await self.click(element)
                    result['status'] = 'success' if success else 'failed'
                else:
                    result['status'] = 'element_not_found'
                    
            elif action == 'type':
                element = await self.find_element(target)
                if element:
                    success = await self.type_text(element, value)
                    result['status'] = 'success' if success else 'failed'
                else:
                    result['status'] = 'element_not_found'
                    
            elif action == 'read':
                content = await self.get_page_content()
                result.update(content)
                result['status'] = 'success'
                
            elif action == 'screenshot':
                path = await self.screenshot()
                result['screenshot_path'] = path
                result['status'] = 'success'
                
            else:
                result['status'] = 'unknown_action'
                
        except Exception as e:
            logger.error(f"Step execution error: {e}")
            result['status'] = 'error'
            result['error'] = str(e)
        
        if callback:
            await callback(f"Step {action}: {result['status']}", 'action')
        
        return result
