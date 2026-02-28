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
        self.api_key = settings.cohere_api_key
        self.client = None
        if self.api_key:
            try:
                self.client = cohere.ClientV2(api_key=self.api_key)
                logger.info("AI Engine: Cohere client initialized")
            except Exception as e:
                logger.error(f"AI Engine initialization error: {e}")
        else:
            logger.warning("COHERE_API_KEY not set. AI review will use fallback.")

    def review(self, code: str) -> Dict[str, Any]:
        """Perform AI code review"""
        if not self.client:
            return self._get_fallback_response()
            
        try:
            prompt = self._build_prompt(code)
            response = self.client.chat(
                model="command-a-03-2025",
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                temperature=0.1,
                max_tokens=1500
            )
            
            content = response.message.content[0].text
            return self._parse_json(content)
        except Exception as e:
            logger.error(f"AI Review error: {e}")
            return self._get_fallback_response()
            
    def _build_prompt(self, code: str) -> str:
        return f"""
        Analyze this Python code and provide a deep review in JSON format:
        
        {code}
        
        Provide the following fields:
        - "logical_flaws": List of potential bugs or flaws
        - "architecture_suggestions": Ways to improve structure
        - "performance_optimization": Specific code improvements
        - "readability_suggestions": Variable naming, docstrings, etc
        - "refactoring_proposal": A new version of the code (simplified)
        - "design_pattern_recommendations": Patterns to use (SOLID, etc)
        - "ai_quality_score": Score from 1 to 10
        
        Respond ONLY with the JSON object.
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
