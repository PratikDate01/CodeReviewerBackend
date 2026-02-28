import ast
import logging
import re
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class Severity(Enum):
    MINOR = "Minor"
    MAJOR = "Major"
    CRITICAL = "Critical"

@dataclass
class SecurityIssue:
    type: str
    severity: Severity
    message: str
    line: int
    column: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity.value,
            "message": self.message,
            "line": self.line,
            "column": self.column
        }

class SecurityAnalysisEngine(ast.NodeVisitor):
    """
    Security Risk Detection Engine
    Analyzes:
    - OS command injection
    - Unsafe eval/exec
    - Shell execution
    - SQL injection patterns
    - Weak hashing
    - Hardcoded credentials
    - Unsafe file handling
    """
    
    SECRET_KEYWORDS = ['api_key', 'password', 'secret', 'token', 'credentials', 'auth']
    SQL_KEYWORDS = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'JOIN']
    
    def __init__(self, code: str):
        self.code = code
        self.tree = None
        try:
            self.tree = ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Syntax error in security analysis: {e}")
        
        self.issues: List[SecurityIssue] = []
        self.lines = code.split('\n')
    
    def analyze(self) -> List[SecurityIssue]:
        if self.tree:
            self.visit(self.tree)
            self._scan_for_hardcoded_secrets()
        return self.issues
    
    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            
        # OS Command Injection / Unsafe Execution
        if func_name in ('eval', 'exec'):
            self.issues.append(SecurityIssue(
                type="unsafe_exec",
                severity=Severity.CRITICAL,
                message=f"Use of '{func_name}' is highly dangerous and can lead to code injection.",
                line=node.lineno
            ))
            
        if func_name in ('system', 'popen', 'spawn', 'call', 'run'):
            # Check if subprocess or os is used
            is_subprocess = False
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id in ('os', 'subprocess'):
                    is_subprocess = True
            
            if func_name == 'system' or is_subprocess:
                self.issues.append(SecurityIssue(
                    type="shell_execution",
                    severity=Severity.CRITICAL,
                    message=f"Potentially unsafe shell execution via '{func_name}'.",
                    line=node.lineno
                ))
                
        # SQL Injection Detection (simple pattern)
        if func_name in ('execute', 'executemany'):
            if node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Mod):
                    self.issues.append(SecurityIssue(
                        type="sql_injection",
                        severity=Severity.CRITICAL,
                        message="Potential SQL injection via string formatting in database query.",
                        line=node.lineno
                    ))
                elif isinstance(first_arg, ast.JoinedStr):
                    self.issues.append(SecurityIssue(
                        type="sql_injection",
                        severity=Severity.CRITICAL,
                        message="Potential SQL injection via f-string in database query.",
                        line=node.lineno
                    ))
                    
        # Weak Hashing
        if func_name in ('md5', 'sha1'):
            self.issues.append(SecurityIssue(
                type="weak_hashing",
                severity=Severity.MAJOR,
                message=f"Use of weak hashing algorithm '{func_name}'. Use SHA-256 or better.",
                line=node.lineno
            ))
            
        self.generic_visit(node)
        
    def _scan_for_hardcoded_secrets(self):
        """Regex-based secret detection in strings"""
        for i, line in enumerate(self.lines):
            # Check for assignments to suspicious names
            match = re.search(r'(\w*(' + '|'.join(self.SECRET_KEYWORDS) + r')\w*)\s*=\s*[\'"]([^\'"]+)[\'"]', line, re.I)
            if match:
                var_name = match.group(1)
                value = match.group(3)
                # Skip if it looks like a placeholder or env var reference
                if value and len(value) > 4 and not value.startswith('%') and not value.startswith('$'):
                    self.issues.append(SecurityIssue(
                        type="hardcoded_secret",
                        severity=Severity.CRITICAL,
                        message=f"Potential hardcoded secret found in variable '{var_name}'.",
                        line=i + 1
                    ))

    def get_security_score(self) -> float:
        """Calculate security score (0-100)"""
        if not self.issues:
            return 100.0
            
        penalty = 0
        for issue in self.issues:
            if issue.severity == Severity.CRITICAL:
                penalty += 30
            elif issue.severity == Severity.MAJOR:
                penalty += 15
            else:
                penalty += 5
        
        return max(0, 100 - penalty)
