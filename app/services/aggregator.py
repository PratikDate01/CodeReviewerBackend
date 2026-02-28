import logging
from typing import Dict, Any, List
from app.services.static_analysis import StaticAnalysisEngine
from app.services.security_analysis import SecurityAnalysisEngine
from app.services.complexity_analyzer import ComplexityAnalyzer
from app.services.scoring_engine import ScoringEngine
from app.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

class ReviewAggregator:
    """
    Main entry point for combining multiple analysis engines
    """
    
    def __init__(self):
        self.ai_engine = AIEngine()
        self.scoring_engine = ScoringEngine()
        
    def perform_review(self, code: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Runs all engines and aggregates the results"""
        
        static_engine = StaticAnalysisEngine(code)
        security_engine = SecurityAnalysisEngine(code)
        complexity_engine = ComplexityAnalyzer(code)
        
        # 1. Static & Complexity Analysis
        static_results = static_engine.analyze()
        complexity_data = complexity_engine.analyze()
        
        # 2. Security Risk Detection
        security_issues = security_engine.analyze()
        security_score = security_engine.get_security_score()
        
        # 3. AI Engine (pluggable)
        ai_data = {}
        if mode in ("ai", "hybrid", "advanced"):
            ai_data = self.ai_engine.review(code, mode)
            
        # 4. Scoring Engine
        loc = complexity_data["lines_of_code"]
        static_issue_count = len(static_results["unused_variables"]) + \
                             len(static_results["dead_code"]) + \
                             len(static_results["exception_handling"])
        
        static_score = self.scoring_engine.calculate_static_score(static_issue_count, loc)
        
        # Average CC for maintainability
        avg_cc = complexity_engine.get_avg_complexity(complexity_data["cyclomatic_complexity"])
        maintainability_score = self.scoring_engine.calculate_maintainability_score(avg_cc, loc)
        
        ai_quality_score = ai_data.get("ai_quality_score", 5)
        
        final_scores = self.scoring_engine.calculate_final_score(
            static_score, security_score, maintainability_score, ai_quality_score
        )
        
        # 6. Issue counts for severity
        critical = 0
        major = 0
        minor = 0
        for issue in security_issues:
            sev = issue.severity.value.lower()
            if sev == "minor": minor += 1
            elif sev == "major": major += 1
            elif sev == "critical": critical += 1
        
        # Prepare breakdown
        breakdown = {
            "static_score": round(static_score, 1),
            "security_score": round(security_score, 1),
            "maintainability_score": round(maintainability_score, 1),
            "ai_score": round(ai_quality_score, 1)
        }
        
        # Prepare complexity analysis
        complexity_analysis = {
            "function_count": complexity_data["total_functions"],
            "long_functions": len(complexity_data["long_functions"]),
            "long_functions_list": complexity_data["long_functions"],
            "cyclomatic_complexity": complexity_data["total_complexity"],
            "cyclomatic_complexity_list": complexity_data["cyclomatic_complexity"],
            "avg_complexity": round(avg_cc, 2),
            "lines_of_code": loc
        }
        
        # Prepare security analysis
        security_analysis = {
            "issues": [i.to_dict() for i in security_issues],
            "critical": critical,
            "major": major,
            "minor": minor,
            "security_score": round(security_score, 1)
        }
        
        # 5. Visual Metrics for Graphs
        graphs = self._prepare_graph_data(complexity_data, security_issues, breakdown)

        # 7. Final Clean Response (Frontend-compatible)
        response = {
            "final_score": round(final_scores["final_score"] / 10, 1),
            "grade": final_scores["grade"],
            "breakdown": breakdown,
            "static_analysis": static_results,
            "complexity_analysis": complexity_analysis,
            "security_analysis": security_analysis,
            "ai_review": ai_data,
            "graphs": graphs,
            "metadata": {
                "loc": loc,
                "review_mode": mode,
                "pylint_score": round(static_score / 10, 1),
                "maintainability_index": round(maintainability_score / 10, 1)
            }
        }
        
        return response
        
    def _prepare_graph_data(self, complexity: Dict[str, Any], 
                            security_issues: List[Any], 
                            breakdown: Dict[str, Any]) -> Dict[str, Any]:
        """Format data for frontend charts"""
        
        # Complexity per function
        complexity_graph = [
            {"function": c["function"], "complexity": c["complexity"]}
            for c in complexity["cyclomatic_complexity"]
        ]
        
        # Risk distribution (pie chart)
        risk_levels = {"low": 0, "medium": 0, "high": 0}
        for issue in security_issues:
            sev = issue.severity.value.lower()
            if sev == "minor": risk_levels["low"] += 1
            elif sev == "major": risk_levels["medium"] += 1
            elif sev == "critical": risk_levels["high"] += 1
            
        # Radar chart for code quality
        quality_radar = [
            {"subject": "Static", "score": breakdown["static_score"]},
            {"subject": "Security", "score": breakdown["security_score"]},
            {"subject": "Maintainability", "score": breakdown["maintainability_score"]},
            {"subject": "AI Insights", "score": breakdown["ai_score"]},
            {"subject": "Complexity", "score": max(0, 100 - complexity_graph[0]["complexity"] * 5) if complexity_graph else 100}
        ]
        
        return {
            "complexity": complexity_graph,
            "risk_levels": risk_levels,
            "quality_radar": quality_radar
        }
