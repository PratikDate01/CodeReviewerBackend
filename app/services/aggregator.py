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
        
    async def perform_review(self, code: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Runs all engines asynchronously where applicable and aggregates the results"""
        
        static_engine = StaticAnalysisEngine(code)
        security_engine = SecurityAnalysisEngine(code)
        complexity_engine = ComplexityAnalyzer(code)
        
        # 1. Static & Complexity Analysis
        static_results = static_engine.analyze()
        complexity_data = complexity_engine.analyze()
        
        # 2. Security Risk Detection
        security_issues = security_engine.analyze()
        security_score = security_engine.get_security_score()
        
        # 3. AI Engine (pluggable, async)
        ai_data = {}
        if mode in ("ai", "hybrid", "advanced"):
            ai_data = await self.ai_engine.review(code, mode)
            
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
            "ai_score": round(ai_quality_score * 10.0, 1) # Scale to 0-100 like other scores
        }
        
        # Prepare complexity analysis
        complexity_analysis = {
            "function_count": complexity_data["total_functions"],
            "long_functions": len(complexity_data["long_functions"]),
            "long_functions_list": complexity_data["long_functions"],
            "cyclomatic_complexity": complexity_data["total_complexity"],
            "cyclomatic_complexity_list": complexity_data["cyclomatic_complexity"],
            "avg_complexity": round(avg_cc, 2),
            "lines_of_code": loc,
            "maintainability_index": round(maintainability_score, 1)
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

        # Synthesize a clean, professional summary
        issue_count = static_issue_count + len(security_issues)
        summary_text = (
            f"Code review completed in '{mode}' mode. "
            f"Overall health score is {round(final_scores['final_score'] / 10, 1)}/10.0 (Grade {final_scores['grade']}). "
            f"Detected {issue_count} total issues ({critical} critical, {major} major, {minor} minor)."
        )

        # Build recommendations list
        recommendations_list = []
        if ai_data and "recommendations" in ai_data and ai_data["recommendations"]:
            recommendations_list.extend(ai_data["recommendations"])
        else:
            if ai_data.get("design_pattern_recommendations"):
                recommendations_list.extend(ai_data["design_pattern_recommendations"])
            if ai_data.get("architecture_suggestions"):
                recommendations_list.extend(ai_data["architecture_suggestions"])
                
        if avg_cc > 8:
            recommendations_list.append("Refactor functions with high cyclomatic complexity (above 8) to improve maintainability.")

        # Build top-level issues list
        issues_list = []
        for issue in security_issues:
            issues_list.append({
                "type": f"Security: {issue.type}",
                "severity": issue.severity.value,
                "message": issue.message,
                "line": issue.line,
                "column": issue.column
            })
        for issue in static_results.get("unused_variables", []):
            issues_list.append({
                "type": "Static Analysis: Unused Variable",
                "severity": "Minor",
                "message": issue,
                "line": 0,
                "column": 0
            })
        for issue in static_results.get("dead_code", []):
            issues_list.append({
                "type": "Static Analysis: Dead Code",
                "severity": "Major",
                "message": issue,
                "line": 0,
                "column": 0
            })
        for issue in static_results.get("exception_handling", []):
            issues_list.append({
                "type": "Static Analysis: Exception Handling",
                "severity": "Major",
                "message": issue,
                "line": 0,
                "column": 0
            })

        # Top-level charts data
        charts_data = {
            "radar": graphs.get("quality_radar", []),
            "complexity": graphs.get("complexity", []),
            "risk": graphs.get("risk_levels", {})
        }

        # Add test-compatibility keys to ai_data
        ai_data["bugs"] = ai_data.get("logical_flaws", [])
        ai_data["performance_issues"] = ai_data.get("performance_optimization", [])
        ai_data["security_issues"] = []
        ai_data["ai_score"] = ai_data.get("ai_quality_score", 5)

        # Integration test compatibility fields
        scoring_compat = {
            "final_score": round(final_scores["final_score"] / 10, 1),
            "static_score": round(static_score / 10, 1),
            "ai_score": round(ai_quality_score, 1),
            "critical": critical,
            "major": major,
            "minor": minor,
            "severity_breakdown": {
                "critical": critical,
                "major": major,
                "minor": minor,
                "security": len(security_issues)
            }
        }

        advanced_analysis_compat = {
            "function_count": complexity_data["total_functions"],
            "long_functions": len(complexity_data["long_functions"]),
            "cyclomatic_complexity": complexity_data["total_complexity"],
            "maintainability_index": round(maintainability_score, 1),
            "issues": issues_list,
            "recommendations": recommendations_list
        }

        # 7. Final Clean Response (Frontend-compatible)
        response = {
            "final_score": round(final_scores["final_score"] / 10, 1),
            "grade": final_scores["grade"],
            "summary": summary_text,
            "issues": issues_list,
            "recommendations": recommendations_list,
            "charts": charts_data,
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
            },
            
            # Integration test compatibility fields
            "review_mode": mode,
            "scoring": scoring_compat,
            "advanced_analysis": advanced_analysis_compat
        }
        
        # Self-referencing fullData for full backwards compatibility
        response["fullData"] = response.copy()
        
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
