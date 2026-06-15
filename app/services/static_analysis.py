import ast
import logging
import io
from typing import List, Dict, Any
from pylint import lint
from pylint.reporters import JSONReporter
import json
import os

logger = logging.getLogger(__name__)

class StaticAnalysisEngine:
    """
    Static Code Analysis Engine
    Analyzes:
    - Code quality (Pylint)
    - Unused variables
    - Dead code detection
    - Exception handling quality
    - Input validation detection
    """
    
    def __init__(self, code: str):
        self.code = code
        self.tree = None
        try:
            self.tree = ast.parse(code)
        except SyntaxError:
            pass
            
    def analyze(self) -> Dict[str, Any]:
        """Run all static checks"""
        results = {
            "pylint_score": self._get_pylint_score(),
            "unused_variables": self._find_unused_variables(),
            "dead_code": self._detect_dead_code(),
            "exception_handling": self._check_exception_handling(),
            "input_validation": self._check_input_validation()
        }
        return results
        
    def _get_pylint_score(self) -> float:
        """Calculate pylint score for the code."""
        import tempfile
        temp_fd, temp_path = tempfile.mkstemp(suffix=".py", prefix="linter_")
        try:
            with os.fdopen(temp_fd, "w") as f:
                f.write(self.code)
            
            stdout = io.StringIO()
            # Minimalistic linting for faster response
            options = ["--disable=all", "--enable=E,W,R,C", temp_path]
            lint.Run(options, exit=False, reporter=JSONReporter(stdout))
            
            report = json.loads(stdout.getvalue() or "[]")
            error_count = len(report)
            score = max(0, 10 - (error_count * 0.5))
            return round(min(score, 10.0), 2)
        except Exception as e:
            logger.warning(f"Could not get pylint score: {e}")
            return 7.0
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                logger.error(f"Error removing temp file {temp_path}: {e}")

    def _find_unused_variables(self) -> List[str]:
        if not self.tree: return []
        defined = set()
        used = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    defined.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    used.add(node.id)
        unused = defined - used
        return [f"Unused variable: '{var}'" for var in unused if not var.startswith('_')]

    def _detect_dead_code(self) -> List[str]:
        if not self.tree: return []
        dead_code = []
        # Check for code after return/raise
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for i, stmt in enumerate(node.body):
                    if isinstance(stmt, (ast.Return, ast.Raise)):
                        if i < len(node.body) - 1:
                            dead_code.append(f"Unreachable code after {type(stmt).__name__} in '{node.name}'")
                            break
        return dead_code

    def _check_exception_handling(self) -> List[str]:
        if not self.tree: return []
        issues = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ExceptHandler):
                # Check for bare except or 'pass' in except
                if node.type is None:
                    issues.append("Bare 'except:' used. Catch specific exceptions instead.")
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    issues.append("Empty 'except:' block with 'pass' hides errors.")
        return issues

    def _check_input_validation(self) -> bool:
        """Simple heuristic to detect if code validates input (e.g. using 'if' or 'isinstance')"""
        if not self.tree: return False
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.If, ast.Assert)):
                return True
        return False
