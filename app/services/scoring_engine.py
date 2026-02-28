import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ScoringEngine:
    """
    Weighted Scoring Model:
    - Static Score (40%)
    - Security Score (25%)
    - Maintainability Score (20%)
    - AI Quality Score (15%)
    
    Returns breakdown like:
    {
      "final_score": 82,
      "grade": "A",
      "breakdown": {
          "static_score": 75,
          "security_score": 90,
          "maintainability_score": 70,
          "ai_score": 80
      }
    }
    """
    
    def __init__(self):
        self.weights = {
            "static": 0.40,
            "security": 0.25,
            "maintainability": 0.20,
            "ai": 0.15
        }
    
    def calculate_final_score(self, static_score: float, security_score: float, 
                              maintainability_score: float, ai_score: float) -> Dict[str, Any]:
        """
        Calculates a final weighted score (0-100) and grade.
        
        Args:
            static_score: 0-100 score for static analysis
            security_score: 0-100 score for security risks
            maintainability_score: 0-100 maintainability index
            ai_score: 0-10 score (will be scaled to 100)
        """
        
        scaled_ai_score = ai_score * 10
        
        final_score = (
            (static_score * self.weights["static"]) +
            (security_score * self.weights["security"]) +
            (maintainability_score * self.weights["maintainability"]) +
            (scaled_ai_score * self.weights["ai"])
        )
        
        final_score = round(final_score, 1)
        grade = self._get_grade(final_score)
        
        return {
            "final_score": final_score,
            "grade": grade,
            "breakdown": {
                "static_score": round(static_score, 1),
                "security_score": round(security_score, 1),
                "maintainability_score": round(maintainability_score, 1),
                "ai_score": round(scaled_ai_score, 1)
            }
        }
        
    def _get_grade(self, score: float) -> str:
        if score >= 90: return "A+"
        if score >= 80: return "A"
        if score >= 70: return "B"
        if score >= 60: return "C"
        if score >= 50: return "D"
        return "F"
        
    def calculate_static_score(self, issue_count: int, loc: int) -> float:
        """Penalty-based static score"""
        if loc <= 0: return 100.0
        # 10 points penalty per 1 issue per 100 lines
        penalty = (issue_count / (loc / 100 or 1)) * 5
        return max(0, 100 - penalty)
        
    def calculate_maintainability_score(self, complexity: float, loc: int) -> float:
        """Simple MI approximation"""
        if loc <= 0: return 100.0
        # More complex/long functions -> lower score
        score = 171 - 5.2 * (complexity / loc * 100) - 0.23 * complexity
        return max(0, min(100, score))
