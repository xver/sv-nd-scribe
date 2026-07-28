"""
Core framework for modular linting system

Company: Copyright (c) 2026  IC Verimeter  
         Licensed under the MIT License.

"""

from .base_linter import BaseLinter, LinterResult
from .base_rule import BaseRule, RuleViolation, RuleSeverity
from .linter_registry import LinterRegistry, get_registry, register_linter
from .config_manager import ConfigManager

__all__ = [
    'BaseLinter',
    'LinterResult',
    'BaseRule',
    'RuleViolation',
    'RuleSeverity',
    'LinterRegistry',
    'get_registry',
    'register_linter',
    'ConfigManager'
]

