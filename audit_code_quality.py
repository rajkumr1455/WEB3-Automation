"""
Code Quality Audit for Web3 Hunter
Checks for common issues and best practices
"""
import os
import re
from typing import List, Dict

class CodeAuditor:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.suggestions = []
        
    def audit_file(self, filepath: str):
        """Audit a single Python file"""
        if not filepath.endswith('.py'):
            return
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            self.check_error_handling(filepath, content, lines)
            self.check_logging(filepath, content)
            self.check_hardcoded_values(filepath, content)
            self.check_async_consistency(filepath, content)
            self.check_docstrings(filepath, content)
            
        except Exception as e:
            print(f"Error auditing {filepath}: {e}")
    
    def check_error_handling(self, filepath, content, lines):
        """Check for bare except clauses and missing error handling"""
        # Bare except
        if re.search(r'except\s*:', content):
            self.warnings.append(f"{filepath}: Bare except clause found - should specify exception type")
        
        # Functions without try-except
        func_pattern = r'async\s+def|def\s+'
        funcs = re.finditer(func_pattern, content)
        for match in funcs:
            start = match.start()
            # Get function body (simplified)
            func_end = content.find('\ndef ', start + 10)
            if func_end == -1:
                func_end = len(content)
            func_body = content[start:func_end]
            
            if 'httpx' in func_body or 'ollama' in func_body or 'requests' in func_body:
                if 'try:' not in func_body:
                    line_num = content[:start].count('\n') + 1
                    self.suggestions.append(f"{filepath}:{line_num}: Network call without try-except")
    
    def check_logging(self, filepath, content):
        """Check logging coverage"""
        if 'import logging' in content:
            # Good - logging is imported
            pass
        else:
            if 'print(' in content:
                self.suggestions.append(f"{filepath}: Uses print() instead of proper logging")
    
    def check_hardcoded_values(self, filepath, content):
        """Check for hardcoded configurations"""
        # API keys
        if re.search(r'api_key\s*=\s*["\'](?!YOUR_)[^"\']+["\']', content):
            self.warnings.append(f"{filepath}: Possible hardcoded API key")
        
        # Hardcoded ports/hosts
        if '127.0.0.1' in content or 'localhost' in content:
            if 'os.getenv' not in content:
                self.suggestions.append(f"{filepath}: Hardcoded host/port - consider using environment variables")
    
    def check_async_consistency(self, filepath, content):
        """Check async/await consistency"""
        # Calling async function without await
        async_calls = re.findall(r'(\w+)\(.*\)', content)
        async_defs = re.findall(r'async\s+def\s+(\w+)', content)
        
        # This is simplified - full check would need AST
        pass
    
    def check_docstrings(self, filepath, content):
        """Check for missing docstrings"""
        funcs = re.findall(r'def\s+(\w+)\(', content)
        if len(funcs) > 0:
            # Check if there are docstrings
            if '"""' not in content and "'''" not in content:
                self.suggestions.append(f"{filepath}: Missing docstrings")
    
    def audit_directory(self, directory: str):
        """Audit all Python files in directory"""
        for root, dirs, files in os.walk(directory):
            # Skip virtual env and cache
            if 'venv' in root or '__pycache__' in root or 'legacy_archive' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self.audit_file(filepath)
    
    def print_report(self):
        """Print audit report"""
        print("=" * 70)
        print("CODE QUALITY AUDIT REPORT")
        print("=" * 70)
        print()
        
        if self.issues:
            print(f"CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  [!] {issue}")
            print()
        
        if self.warnings:
            print(f"WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f"  [*] {warn}")
            print()
        
        if self.suggestions:
            print(f"SUGGESTIONS ({len(self.suggestions)}):")
            for sugg in self.suggestions[:10]:  # Limit to 10
                print(f"  [-] {sugg}")
            if len(self.suggestions) > 10:
                print(f"  ... and {len(self.suggestions) - 10} more")
            print()
        
        total = len(self.issues) + len(self.warnings) + len(self.suggestions)
        if total == 0:
            print("✓ No issues found! Code quality is good.")
        else:
            print(f"Total: {len(self.issues)} issues, {len(self.warnings)} warnings, {len(self.suggestions)} suggestions")

if __name__ == "__main__":
    auditor = CodeAuditor()
    auditor.audit_directory(".")
    auditor.print_report()
