import re
from typing import List


def sanitize_code(code: str) -> str:
    code = code.strip()
    return code


def validate_python_code(code: str) -> bool:
    try:
        compile(code, '<string>', 'exec')
        return True
    except SyntaxError:
        return False


def extract_function_names(code: str) -> List[str]:
    pattern = r'def\s+(\w+)\s*\('
    matches = re.findall(pattern, code)
    return matches


def extract_imports(code: str) -> List[str]:
    pattern = r'^(?:from|import)\s+(.+)$'
    matches = re.findall(pattern, code, re.MULTILINE)
    return matches
