"""
Base class for linters

Company: Copyright (c) 2026  IC Verimeter  
         Licensed under the MIT License.

Description: Abstract base class for implementing linters
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .base_rule import BaseRule, RuleViolation, RuleSeverity


@dataclass
class LinterResult:
    """
    Results from running a linter on files
    
    Attributes:
        linter_name: Name of the linter that produced these results
        files_checked: Number of files successfully checked
        files_failed: Number of files that failed to parse/check
        violations: List of all violations found
        errors: Dictionary mapping file paths to error messages
    """
    linter_name: str
    files_checked: int = 0
    files_failed: int = 0
    violations: List[RuleViolation] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)
    
    @property
    def error_count(self) -> int:
        """Count violations with ERROR severity"""
        return sum(1 for v in self.violations if v.severity == RuleSeverity.ERROR)
    
    @property
    def warning_count(self) -> int:
        """Count violations with WARNING severity"""
        return sum(1 for v in self.violations if v.severity == RuleSeverity.WARNING)
    
    @property
    def info_count(self) -> int:
        """Count violations with INFO severity"""
        return sum(1 for v in self.violations if v.severity == RuleSeverity.INFO)
    
    def add_violation(self, violation: RuleViolation):
        """Add a violation to the results"""
        self.violations.append(violation)
    
    def add_error(self, file_path: str, error_msg: str):
        """Add a file-level error (e.g., parse failure)"""
        self.errors[file_path] = error_msg
        self.files_failed += 1

    def format_report(self) -> str:
        """Format the linter result as a human-readable text report"""
        lines = [
            f"Files checked: {self.files_checked}",
            f"Files failed: {self.files_failed}",
            f"Errors found: {self.error_count}",
            f"Warnings found: {self.warning_count}"
        ]
        
        if self.violations:
            lines.append("\nViolations:")
            for v in sorted(self.violations, key=lambda x: (x.file, x.line)):
                severity = v.severity.name if hasattr(v.severity, 'name') else str(v.severity)
                lines.append(f"{v.file}:{v.line}: [{severity}] {v.rule_id} {v.message}")
                
        if self.errors:
            lines.append("\nInternal Errors:")
            for k, v in sorted(self.errors.items()):
                lines.append(f"  {k}: {v}")
                
        return "\n".join(lines) + "\n"

    def to_dict(self) -> dict:
        """Convert linter result to a dictionary representation"""
        return {
            "linter_name": self.linter_name,
            "files_checked": self.files_checked,
            "files_failed": self.files_failed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "violations": [
                {
                    "file": v.file,
                    "line": v.line,
                    "column": v.column,
                    "severity": v.severity.name if hasattr(v.severity, 'name') else str(v.severity),
                    "rule_id": v.rule_id,
                    "message": v.message,
                    "context": v.context,
                }
                for v in sorted(self.violations, key=lambda x: (x.file, x.line))
            ],
            "errors": self.errors,
        }

    def format_json(self, indent: int = 2) -> str:
        """Format the linter result as a JSON string"""
        import json
        return json.dumps(self.to_dict(), indent=indent) + "\n"

    def write_log(self, log_path: str):
        """Write formatted report to a log file"""
        log_dir = os.path.dirname(os.path.abspath(log_path))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(self.format_report())


class BaseLinter(ABC):
    """
    Abstract base class for all linters
    
    Each linter implementation should:
    - Register rules it supports
    - Implement file checking logic
    - Return structured results
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize linter with configuration
        
        Args:
            config: Configuration dictionary for the linter
        """
        self.config = config or {}
        self.rules: List[BaseRule] = []
        self._register_rules()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of this linter
        
        Returns:
            String name of the linter
        """
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """
        File extensions this linter can handle
        
        Returns:
            List of file extensions (e.g., ['.sv', '.svh'])
        """
        pass
    
    @abstractmethod
    def _register_rules(self):
        """
        Register all rules for this linter
        
        This method should populate self.rules with rule instances
        """
        pass
    
    @abstractmethod
    def prepare_context(self, file_path: str, file_content: str) -> Optional[any]:
        """
        Prepare any context needed for rule checking
        
        This might include:
        - Parsing the file into an AST
        - Building symbol tables
        - Extracting metadata
        
        Args:
            file_path: Path to file being checked
            file_content: Content of the file
        
        Returns:
            Context object to pass to rules, or None if preparation fails
        """
        pass
    
    def lint_file(self, file_path: str) -> LinterResult:
        """
        Lint a single file using all registered rules
        
        Args:
            file_path: Path to file to lint
        
        Returns:
            LinterResult containing all violations found
        """
        result = LinterResult(linter_name=self.name)
        
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                file_content = f.read()
        except Exception as e:
            result.add_error(file_path, f"Failed to read file: {str(e)}")
            return result
        
        # Prepare context (e.g., parse AST)
        context = self.prepare_context(file_path, file_content)
        if context is None:
            result.add_error(file_path, "Failed to prepare context")
            return result
        
        # Run all enabled rules
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                violations = rule.check(file_path, file_content, context)
                for violation in violations:
                    result.add_violation(violation)
            except Exception as e:
                result.add_error(file_path, f"Rule {rule.rule_id} failed: {str(e)}")
        
        result.files_checked = 1
        return result
    
    def lint_files(self, file_paths: List[str]) -> LinterResult:
        """
        Lint multiple files
        
        Args:
            file_paths: List of file paths to lint
        
        Returns:
            Combined LinterResult for all files
        """
        combined_result = LinterResult(linter_name=self.name)
        
        for file_path in file_paths:
            # Check if this linter supports this file type
            if not any(file_path.endswith(ext) for ext in self.supported_extensions):
                continue
            
            # Lint the file
            file_result = self.lint_file(file_path)
            
            # Merge results
            combined_result.files_checked += file_result.files_checked
            combined_result.files_failed += file_result.files_failed
            combined_result.violations.extend(file_result.violations)
            combined_result.errors.update(file_result.errors)
        
        return combined_result
    
    def add_rule(self, rule: BaseRule):
        """
        Add a rule to this linter
        
        Args:
            rule: Rule instance to add
        """
        self.rules.append(rule)

