import json
import logging
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError
import cohere
from app.config import settings

logger = logging.getLogger(__name__)

class AISchema(BaseModel):
    logical_flaws: List[str] = Field(default_factory=list)
    architecture_suggestions: List[str] = Field(default_factory=list)
    performance_optimization: List[str] = Field(default_factory=list)
    readability_suggestions: List[str] = Field(default_factory=list)
    refactoring_proposal: str = Field(default="")
    refactored_code: Optional[str] = Field(default=None)
    design_pattern_recommendations: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    ai_quality_score: int = Field(default=5, ge=1, le=10)

class AIEngine:
    """
    AI Review Engine (LLM-based)
    Pluggable integration for LLMs (default Cohere V2 Async)
    """
    
    def __init__(self):
        self.keys = [k for k in settings.cohere_api_keys if k]
        if settings.cohere_api_key and settings.cohere_api_key not in self.keys:
            self.keys.append(settings.cohere_api_key)
            
        self.current_key_index = 0
        self.clients = []
        
        for key in self.keys:
            try:
                # Initialize AsyncClientV2 with a 30s timeout
                self.clients.append(cohere.AsyncClientV2(api_key=key, timeout=30.0))
                logger.info(f"AI Engine: Cohere Async client initialized with key {key[:4]}...{key[-4:]}")
            except Exception as e:
                logger.error(f"AI Engine initialization error for key {key[:4]}...: {e}")
                
        if not self.clients:
            logger.warning("No valid COHERE_API_KEYS set. AI review will use fallback.")

    async def review(self, code: str, mode: str = "hybrid", attempt: int = 0) -> Dict[str, Any]:
        """Perform AI code review with key rotation"""
        if not self.clients:
            return self._get_fallback_response()
            
        if attempt >= len(self.clients):
            logger.error("All AI API keys exhausted or failed.")
            return self._get_fallback_response()
            
        client = self.clients[self.current_key_index]
        
        try:
            prompt = self._build_prompt(code, mode)
            # Use client.chat with response_format for structured JSON output
            response = await client.chat(
                model="command-r",
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            content = response.message.content[0].text
            return self._parse_json(content)
        except Exception as e:
            logger.error(f"AI Review error with key {self.current_key_index}: {e}")
            
            # Rotate key on error (similar to Node.js logic)
            self.current_key_index = (self.current_key_index + 1) % len(self.clients)
            return await self.review(code, mode, attempt + 1)
            
    def _build_prompt(self, code: str, mode: str = "hybrid") -> str:
        return f"""
        Analyze this code for DevPilot AI and provide a deep review in JSON format:
        MODE: {mode}

        CODE:
        {code}

        Provide ONLY this JSON structure:
        {{
            "logical_flaws": ["string"],
            "architecture_suggestions": ["string"],
            "performance_optimization": ["string"],
            "readability_suggestions": ["string"],
            "refactoring_proposal": "string explanation of changes",
            "refactored_code": "string with refactored python code",
            "design_pattern_recommendations": ["string"],
            "recommendations": ["string summarizing key recommended fixes"],
            "ai_quality_score": 1-10 (integer)
        }}
        """
        
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Safely extract and validate JSON from response using Pydantic"""
        try:
            # Try strict JSON load first
            data = json.loads(text)
        except json.JSONDecodeError:
            try:
                # Non-greedy regex fallback if there's surrounding text
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                else:
                    raise ValueError("No JSON object found")
            except Exception as e:
                logger.error(f"Failed to extract JSON: {e}")
                return self._get_fallback_response()
        
        # Pydantic schema validation
        try:
            validated = AISchema(**data)
            # Ensure recommendations is populated if empty
            res_dict = validated.model_dump()
            if not res_dict.get("recommendations"):
                merged_recs = []
                if res_dict.get("design_pattern_recommendations"):
                    merged_recs.extend(res_dict["design_pattern_recommendations"])
                if res_dict.get("architecture_suggestions"):
                    merged_recs.extend(res_dict["architecture_suggestions"])
                res_dict["recommendations"] = merged_recs[:5]
            return res_dict
        except ValidationError as val_err:
            logger.error(f"Pydantic validation error: {val_err}")
            # Try to fix partial dict or use defaults
            fallback = self._get_fallback_response()
            # Merge whatever keys we can salvage
            for k in fallback.keys():
                if k in data and type(data[k]) == type(fallback[k]):
                    fallback[k] = data[k]
            return fallback
            
    def _get_fallback_response(self) -> Dict[str, Any]:
        return {
            "logical_flaws": ["AI review service temporarily unavailable. Please verify manually."],
            "architecture_suggestions": ["Follow standard clean code and SOLID principles."],
            "performance_optimization": ["Optimize time and memory usage where applicable."],
            "readability_suggestions": ["Ensure code adheres to standard styling format."],
            "refactoring_proposal": "AI refactoring proposal not available.",
            "refactored_code": None,
            "design_pattern_recommendations": ["Use common architectural design patterns."],
            "recommendations": ["Review manual checks for code health."],
            "ai_quality_score": 5
        }
