"""
Vision Helper - LLaVA integration for screenshot analysis
Used when DOM-based element detection fails
"""

import logging
import re
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import ollama

logger = logging.getLogger('NeuroSurf.Vision')


class VisionHelper:
    """
    LLaVA-based vision analysis for screenshots
    Used to find elements when standard DOM selectors fail
    """
    
    def __init__(self, model: str = "llava:latest"):
        """
        Initialize vision helper
        
        Args:
            model: Ollama vision model to use
        """
        self.model = model
        
    async def find_element_coordinates(
        self,
        screenshot_path: str,
        element_description: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find element coordinates in a screenshot
        
        Args:
            screenshot_path: Path to screenshot image
            element_description: Natural language description of element
            
        Returns:
            Dict with found status and coordinates
        """
        if not Path(screenshot_path).exists():
            logger.error(f"Screenshot not found: {screenshot_path}")
            return None
        
        prompt = f"""Look at this screenshot of a web page.
I need to find the location of: {element_description}

Please respond with the X and Y coordinates of the CENTER of this element.
The image is 1920x1080 pixels.
Format your response as: X=<number> Y=<number>

If you cannot find the element, respond with: NOT_FOUND

Coordinates:"""

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                images=[screenshot_path]
            )
            
            return self._parse_coordinates(response['response'])
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return None
    
    def _parse_coordinates(self, response: str) -> Dict[str, Any]:
        """Parse coordinates from LLaVA response"""
        response_upper = response.upper()
        
        if 'NOT_FOUND' in response_upper or 'CANNOT FIND' in response_upper:
            return {"found": False}
        
        # Try to extract X and Y values
        x_match = re.search(r'X\s*[=:]\s*(\d+)', response, re.IGNORECASE)
        y_match = re.search(r'Y\s*[=:]\s*(\d+)', response, re.IGNORECASE)
        
        if x_match and y_match:
            x = int(x_match.group(1))
            y = int(y_match.group(1))
            
            # Validate coordinates are within viewport
            if 0 <= x <= 1920 and 0 <= y <= 1080:
                return {
                    "found": True,
                    "coordinates": (x, y),
                    "confidence": 0.7
                }
        
        # Try alternative format: (X, Y)
        coord_match = re.search(r'\((\d+)\s*,\s*(\d+)\)', response)
        if coord_match:
            x, y = int(coord_match.group(1)), int(coord_match.group(2))
            if 0 <= x <= 1920 and 0 <= y <= 1080:
                return {
                    "found": True,
                    "coordinates": (x, y),
                    "confidence": 0.6
                }
        
        return {"found": False}
    
    async def analyze_page(
        self,
        screenshot_path: str,
        query: str
    ) -> str:
        """
        General page analysis using vision
        
        Args:
            screenshot_path: Path to screenshot
            query: Question about the page
            
        Returns:
            Analysis response
        """
        if not Path(screenshot_path).exists():
            return "Screenshot not found"
        
        try:
            response = ollama.generate(
                model=self.model,
                prompt=query,
                images=[screenshot_path]
            )
            return response['response']
            
        except Exception as e:
            logger.error(f"Page analysis failed: {e}")
            return f"Analysis failed: {e}"
    
    async def detect_captcha(
        self,
        screenshot_path: str
    ) -> Dict[str, Any]:
        """
        Detect if page has a CAPTCHA
        
        Args:
            screenshot_path: Path to screenshot
            
        Returns:
            Detection result
        """
        prompt = """Analyze this webpage screenshot.
Is there a CAPTCHA, reCAPTCHA, or similar verification challenge visible?
If yes, what type is it (checkbox, image selection, puzzle, etc.)?

Respond with:
CAPTCHA_DETECTED: yes/no
TYPE: <type if detected>
DESCRIPTION: <brief description>"""

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                images=[screenshot_path]
            )
            
            text = response['response'].upper()
            detected = 'CAPTCHA_DETECTED: YES' in text or 'YES' in text.split('\n')[0]
            
            return {
                "captcha_detected": detected,
                "raw_response": response['response']
            }
            
        except Exception as e:
            logger.error(f"CAPTCHA detection failed: {e}")
            return {"captcha_detected": False, "error": str(e)}
    
    async def read_text_from_region(
        self,
        screenshot_path: str,
        region: Tuple[int, int, int, int]
    ) -> str:
        """
        Read text from a specific region of the screenshot
        
        Args:
            screenshot_path: Path to screenshot
            region: (x1, y1, x2, y2) bounding box
            
        Returns:
            Extracted text
        """
        x1, y1, x2, y2 = region
        
        prompt = f"""Look at the area in the screenshot from coordinates ({x1}, {y1}) to ({x2}, {y2}).
What text can you read in this region? 
Provide only the text content, no explanations."""

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                images=[screenshot_path]
            )
            return response['response'].strip()
            
        except Exception as e:
            logger.error(f"Text reading failed: {e}")
            return ""
