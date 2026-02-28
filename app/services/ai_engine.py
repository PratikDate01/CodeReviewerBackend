import json
import logging
import re
from typing import Dict, Any
import cohere
from app.config import settings

logger = logging.getLogger(__name__)

class AIEngine:
    """
    AI Review Engine (LLM-based)
    Pluggable integration for LLMs (default Cohere)
    """
    
    def __init__(self):
        self.keys = [k for k in settings.cohere_api_keys if k]
        if settings.cohere_api_key and settings.cohere_api_key not in self.keys:
            self.keys.append(settings.cohere_api_key)
            
        self.current_key_index = 0
        self.clients = []
        
        for key in self.keys:
            try:
                self.clients.append(cohere.ClientV2(api_key=key))
                logger.info(f"AI Engine: Cohere client initialized with key {key[:4]}...{key[-4:]}")
            except Exception as e:
                logger.error(f"AI Engine initialization error for key {key[:4]}...: {e}")
                
        if not self.clients:
            logger.warning("No valid COHERE_API_KEYS set. AI review will use fallback.")

    def review(self, code: str, mode: str = "hybrid", attempt: int = 0) -> Dict[str, Any]:
        """Perform AI code review with key rotation"""
        if not self.clients:
            return self._get_fallback_response()
            
        if attempt >= len(self.clients):
            logger.error("All AI API keys exhausted or failed.")
            return self._get_fallback_response()
            
        client = self.clients[self.current_key_index]
        
        try:
            prompt = self._build_prompt(code, mode)
            response = client.chat(
                model="command-r-plus",
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.message.content[0].text
            return self._parse_json(content)
        except Exception as e:
            logger.error(f"AI Review error with key {self.current_key_index}: {e}")
            
            # Rotate key on error (similar to Node.js logic)
            self.current_key_index = (self.current_key_index + 1) % len(self.clients)
            return self.review(code, mode, attempt + 1)
            
    def _build_prompt(self, code: str, mode: str = "hybrid") -> str:
        return f"""
        Analyze this code for DevPilot AI and provide a deep review in JSON format:
        MODE: {mode}

        CODE:
        {code}

        Provide ONLY this JSON structure:
        {{
            "logical_flaws": [],
            "architecture_suggestions": [],
            "performance_optimization": [],
            "readability_suggestions": [],
            "refactoring_proposal": "string",
            "design_pattern_recommendations": [],
            "ai_quality_score": 1-10 (integer)
        }}
        """
        
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Safely extract JSON from response"""
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(text)
        except:
            return self._get_fallback_response()
            
    def _get_fallback_response(self) -> Dict[str, Any]:
        return {
            "logical_flaws": "AI unavailable. Check for logic errors manually.",
            "architecture_suggestions": "AI unavailable. Use SOLID principles.",
            "performance_optimization": "AI unavailable. Use efficient algorithms.",
            "readability_suggestions": "AI unavailable. Follow PEP 8.",
            "refactoring_proposal": "AI unavailable.",
            "design_pattern_recommendations": "AI unavailable.",
            "ai_quality_score": 5
        }
