"""
Swarm Router - Model Manager for Ollama LLM Swarm
Dynamically loads/unloads models to prevent OOM crashes
"""

import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import ollama

logger = logging.getLogger('NeuroSurf.Swarm')


class ModelRole(Enum):
    """Roles for different LLM models in the swarm"""
    EXECUTIVE = "executive"    # Planning and goal decomposition
    NAVIGATOR = "navigator"    # DOM/Code generation
    EYE = "eye"               # Vision analysis
    CLERK = "clerk"           # Fast JSON formatting


@dataclass
class ModelConfig:
    """Configuration for a model in the swarm"""
    name: str
    role: ModelRole
    loaded: bool = False
    priority: int = 0  # Higher = more likely to stay loaded
    last_used: float = 0
    vram_estimate_gb: float = 0


class ModelManager:
    """
    Manages Ollama models with dynamic loading/unloading
    to prevent Out of Memory (OOM) crashes
    """
    
    # Default model configurations
    DEFAULT_MODELS = {
        ModelRole.EXECUTIVE: ModelConfig(
            name="nemotron-3-nano:30b-a3b-q4_K_M",  # Nemotron for main reasoning
            role=ModelRole.EXECUTIVE,
            priority=10,
            vram_estimate_gb=16.0
        ),
        ModelRole.NAVIGATOR: ModelConfig(
            name="deepseek-coder-v2:16b",
            role=ModelRole.NAVIGATOR,
            priority=8,
            vram_estimate_gb=16.0
        ),
        ModelRole.EYE: ModelConfig(
            name="llava:latest",
            role=ModelRole.EYE,
            priority=5,
            vram_estimate_gb=8.0
        ),
        ModelRole.CLERK: ModelConfig(
            name="llama3.2:3b",
            role=ModelRole.CLERK,
            priority=7,
            vram_estimate_gb=3.0
        )
    }
    
    def __init__(self, max_vram_gb: float = 24.0):
        """
        Initialize ModelManager
        
        Args:
            max_vram_gb: Maximum VRAM budget in GB
        """
        self.max_vram_gb = max_vram_gb
        self.models: Dict[ModelRole, ModelConfig] = {}
        self.current_vram_usage = 0.0
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize the model manager and check available models"""
        logger.info("📦 Initializing Model Manager...")
        
        # Copy default configs
        self.models = {k: ModelConfig(**vars(v)) for k, v in self.DEFAULT_MODELS.items()}
        
        # Check which models are available
        try:
            available = ollama.list()
            available_names = {m['name'] for m in available.get('models', [])}
            
            for role, config in self.models.items():
                if config.name in available_names or config.name.split(':')[0] in available_names:
                    logger.info(f"  ✅ {role.value}: {config.name}")
                else:
                    logger.warning(f"  ❌ {role.value}: {config.name} (not found)")
                    
        except Exception as e:
            logger.error(f"Failed to check Ollama models: {e}")
            
    async def request_model(self, role: ModelRole) -> bool:
        """
        Request a model to be loaded for use
        Will unload other models if necessary to free VRAM
        
        Returns:
            bool: True if model is ready for use
        """
        async with self._lock:
            config = self.models.get(role)
            if not config:
                logger.error(f"Unknown model role: {role}")
                return False
            
            if config.loaded:
                return True
            
            # Check if we need to free VRAM
            needed_vram = config.vram_estimate_gb
            available_vram = self.max_vram_gb - self.current_vram_usage
            
            if needed_vram > available_vram:
                # Need to unload some models
                await self._free_vram(needed_vram - available_vram)
            
            # "Load" the model (Ollama loads on first use)
            config.loaded = True
            self.current_vram_usage += config.vram_estimate_gb
            logger.info(f"📥 Model ready: {config.name} ({config.vram_estimate_gb}GB)")
            
            return True
    
    async def _free_vram(self, needed_gb: float):
        """Unload models to free VRAM, starting with lowest priority"""
        # Sort loaded models by priority (ascending)
        loaded = [
            (role, config) 
            for role, config in self.models.items() 
            if config.loaded
        ]
        loaded.sort(key=lambda x: x[1].priority)
        
        freed = 0.0
        for role, config in loaded:
            if freed >= needed_gb:
                break
            
            await self._unload_model(role)
            freed += config.vram_estimate_gb
            
    async def _unload_model(self, role: ModelRole):
        """Unload a specific model"""
        config = self.models.get(role)
        if not config or not config.loaded:
            return
        
        # Ollama doesn't have explicit unload, but we track state
        config.loaded = False
        self.current_vram_usage -= config.vram_estimate_gb
        logger.info(f"📤 Model unloaded: {config.name}")
    
    def get_model_name(self, role: ModelRole) -> Optional[str]:
        """Get the model name for a role"""
        config = self.models.get(role)
        return config.name if config else None
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        return {
            role.value: {
                "name": config.name,
                "loaded": config.loaded,
                "vram_gb": config.vram_estimate_gb
            }
            for role, config in self.models.items()
        }


class SwarmController:
    """
    Main controller for the LLM swarm
    Routes requests to appropriate models and manages task execution
    """
    
    def __init__(self):
        self.model_manager = ModelManager()
        self.is_ready = False
        self._halt_flag = False
        self._current_task = None
        
    async def initialize(self):
        """Initialize the swarm controller"""
        await self.model_manager.initialize()
        self.is_ready = True
        logger.info("🐝 Swarm Controller initialized")
        
    async def shutdown(self):
        """Shutdown the swarm controller"""
        self._halt_flag = True
        self.is_ready = False
        logger.info("🐝 Swarm Controller shutdown")
        
    async def halt(self):
        """Emergency halt all processing"""
        self._halt_flag = True
        self._current_task = None
        logger.warning("🛑 Swarm HALTED")
        
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        return self.model_manager.get_status()
    
    async def process_command(
        self, 
        command: str, 
        callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Process a user command through the swarm
        
        Args:
            command: Natural language command
            callback: Callback for streaming updates
            
        Returns:
            Dict with result summary
        """
        self._halt_flag = False
        
        try:
            # Step 1: Use Executive to plan
            if callback:
                await callback("Analyzing command with Executive model...", "planning")
            
            await self.model_manager.request_model(ModelRole.EXECUTIVE)
            plan = await self._call_executive(command)
            
            if self._halt_flag:
                return {"summary": "Halted by user", "steps": []}
            
            if callback:
                await callback(f"Plan created: {len(plan.get('steps', []))} steps", "planning")
            
            # Step 2: Execute each step
            results = []
            for i, step in enumerate(plan.get('steps', [])):
                if self._halt_flag:
                    break
                
                if callback:
                    await callback(f"Step {i+1}: {step.get('action', 'unknown')}", "action")
                
                result = await self._execute_step(step, callback)
                results.append(result)
            
            return {
                "summary": plan.get('summary', 'Task completed'),
                "steps": results
            }
            
        except Exception as e:
            logger.error(f"Error in swarm processing: {e}")
            raise
    
    async def _call_executive(self, command: str) -> Dict[str, Any]:
        """Use Executive model to create a plan"""
        model = self.model_manager.get_model_name(ModelRole.EXECUTIVE)
        
        prompt = f"""You are a planning AI. Break down this user command into actionable steps.
        
User Command: {command}

Respond with a JSON object containing:
- summary: Brief description of what will be done
- steps: Array of step objects, each with:
  - action: "navigate" | "click" | "type" | "read" | "summarize"
  - target: Selector or URL or element description
  - value: Optional value for typing

Example response:
{{"summary": "Search for cats on Google", "steps": [{{"action": "navigate", "target": "https://google.com"}}, {{"action": "type", "target": "search box", "value": "cats"}}, {{"action": "click", "target": "search button"}}]}}

JSON Response:"""

        try:
            response = ollama.generate(
                model=model,
                prompt=prompt,
                format='json'
            )
            
            import json
            return json.loads(response['response'])
            
        except Exception as e:
            logger.error(f"Executive model error: {e}")
            return {"summary": command, "steps": []}
    
    async def _execute_step(
        self, 
        step: Dict[str, Any], 
        callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute a single step in the plan"""
        action = step.get('action', '')
        
        # For now, simulate execution
        await asyncio.sleep(0.5)
        
        return {
            "action": action,
            "status": "completed",
            "result": f"Simulated: {action}"
        }
    
    async def vision_analyze(
        self, 
        image_path: str, 
        query: str
    ) -> Dict[str, Any]:
        """
        Use Eye model (LLaVA) to analyze a screenshot
        
        Args:
            image_path: Path to screenshot
            query: Question about the image
            
        Returns:
            Vision analysis result
        """
        await self.model_manager.request_model(ModelRole.EYE)
        model = self.model_manager.get_model_name(ModelRole.EYE)
        
        try:
            response = ollama.generate(
                model=model,
                prompt=query,
                images=[image_path]
            )
            
            return {
                "analysis": response['response'],
                "model": model
            }
            
        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            return {"analysis": None, "error": str(e)}
