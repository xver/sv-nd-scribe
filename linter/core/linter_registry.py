"""
Registry for managing multiple linters

Company: Copyright (c) 2026  IC Verimeter  
         Licensed under the MIT License.

Description: Central registry for discovering and managing linters
"""

from typing import Dict, List, Type, Optional
from .base_linter import BaseLinter


class LinterRegistry:
    """
    Central registry for linters
    
    Provides:
    - Registration of linter classes
    - Discovery of available linters
    - Creation of linter instances
    """
    
    def __init__(self):
        """Initialize empty registry"""
        self._linters: Dict[str, Type[BaseLinter]] = {}
    
    def register(self, linter_class: Type[BaseLinter]):
        """
        Register a linter class
        
        Args:
            linter_class: Class (not instance) of a linter
        """
        # Create temporary instance to get name
        temp_instance = linter_class()
        linter_name = temp_instance.name
        
        self._linters[linter_name] = linter_class
    
    def get_linter(self, name: str, config: Optional[dict] = None) -> Optional[BaseLinter]:
        """
        Get an instance of a registered linter
        
        Args:
            name: Name of the linter
            config: Configuration to pass to linter
        
        Returns:
            Linter instance or None if not found
        """
        linter_class = self._linters.get(name)
        if linter_class:
            return linter_class(config)
        return None
    
    def get_all_linters(self, config: Optional[dict] = None) -> List[BaseLinter]:
        """
        Get instances of all registered linters
        
        Args:
            config: Configuration to pass to all linters
        
        Returns:
            List of linter instances
        """
        return [linter_class(config) for linter_class in self._linters.values()]
    
    def list_linters(self) -> List[str]:
        """
        List names of all registered linters
        
        Returns:
            List of linter names
        """
        return list(self._linters.keys())
    
    def is_registered(self, name: str) -> bool:
        """
        Check if a linter is registered
        
        Args:
            name: Linter name to check
        
        Returns:
            True if linter is registered
        """
        return name in self._linters


# Global registry instance
_global_registry = LinterRegistry()


def register_linter(linter_class: Type[BaseLinter]):
    """
    Decorator to register a linter class
    
    Usage:
        @register_linter
        class MyLinter(BaseLinter):
            ...
    
    Args:
        linter_class: Linter class to register
    
    Returns:
        The same linter class (for use as decorator)
    """
    _global_registry.register(linter_class)
    return linter_class


def get_registry() -> LinterRegistry:
    """
    Get the global linter registry
    
    Returns:
        Global LinterRegistry instance
    """
    return _global_registry

