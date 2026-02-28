from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CodeReviewRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50000, description="Python code to review")
    mode: str = Field(default="hybrid", pattern="^(static|ai|hybrid|advanced)$")

class SecurityIssue(BaseModel):
    type: str
    severity: str
    message: str
    line: int
    column: int = 0

class GraphData(BaseModel):
    complexity: List[Dict[str, Any]]
    risk_levels: Dict[str, int]
    quality_radar: List[Dict[str, Any]]

class AnalysisBreakdown(BaseModel):
    static_score: float
    security_score: float
    maintainability_score: float
    ai_score: float

class CodeReviewResponse(BaseModel):
    final_score: float
    grade: str
    breakdown: AnalysisBreakdown
    static_analysis: Dict[str, Any]
    complexity_analysis: Dict[str, Any]
    security_analysis: Dict[str, Any]
    ai_review: Dict[str, Any]
    graphs: GraphData
    metadata: Dict[str, Any]
