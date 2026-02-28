import ast
import logging
from typing import Dict, Any, List
from radon.complexity import cc_visit, sorted_results

logger = logging.getLogger(__name__)

class ComplexityAnalyzer:
    """
    Complexity Analysis Engine
    Analyzes:
    - Cyclomatic complexity (per function + total)
    - Maintainability Index
    - Long functions detection
    - Deep nesting detection
    - Total functions
    - Lines of code
    """
    
    def __init__(self, code: str):
        self.code = code
        self.tree = None
        try:
            self.tree = ast.parse(code)
        except SyntaxError:
            pass
        
    def analyze(self) -> Dict[str, Any]:
        """Run all complexity checks"""
        cc_data = self._calculate_cyclomatic_complexity()
        total_complexity = sum(c['complexity'] for c in cc_data) if cc_data else 0
        
        results = {
            "total_functions": self._count_functions(),
            "lines_of_code": self._count_loc(),
            "cyclomatic_complexity": cc_data,
            "total_complexity": total_complexity,
            "long_functions": self._detect_long_functions(),
            "deep_nesting": self._detect_deep_nesting()
        }
        return results
        
    def _count_functions(self) -> int:
        if not self.tree:
            return 0
        return len([node for node in ast.walk(self.tree) if isinstance(node, ast.FunctionDef)])
        
    def _count_loc(self) -> int:
        return len(self.code.split('\n'))
        
    def _calculate_cyclomatic_complexity(self) -> List[Dict[str, Any]]:
        """Calculate cyclomatic complexity per function using radon"""
        try:
            blocks = cc_visit(self.code)
            results = []
            for block in blocks:
                result = {
                    "function": block.name,
                    "complexity": block.complexity
                }
                if hasattr(block, 'rank'):
                    result["rank"] = block.rank
                results.append(result)
            return results
        except Exception as e:
            logger.warning(f"Could not calculate CC: {e}")
            return []
            
    def _detect_long_functions(self, threshold: int = 40) -> List[Dict[str, Any]]:
        if not self.tree:
            return []
        
        long_funcs = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                line_count = node.end_lineno - node.lineno + 1
                if line_count >= threshold:
                    long_funcs.append({
                        "name": node.name,
                        "lines": line_count,
                        "line": node.lineno
                    })
        return long_funcs
        
    def _detect_deep_nesting(self, threshold: int = 4) -> List[Dict[str, Any]]:
        if not self.tree:
            return []
            
        deep_nesting = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                max_depth = self._get_max_nesting(node)
                if max_depth >= threshold:
                    deep_nesting.append({
                        "name": node.name,
                        "depth": max_depth,
                        "line": node.lineno
                    })
        return deep_nesting
        
    def _get_max_nesting(self, node: ast.AST, depth: int = 0) -> int:
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                child_depth = self._get_max_nesting(child, depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth

    def get_avg_complexity(self, complexities: List[Dict[str, Any]]) -> float:
        if not complexities:
            return 0.0
        total = sum(c['complexity'] for c in complexities)
        return round(total / len(complexities), 2)
