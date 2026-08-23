# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import sys
from typing import Dict, Type, Optional, Any
from .base_llm import BaseLLMProvider

_PROVIDER_REGISTRY: Dict[str, Type[BaseLLMProvider]] = {}

def register_llm(name: str):
    """Decorator to register an LLM provider class under a key."""
    def decorator(cls: Type[BaseLLMProvider]):
        _PROVIDER_REGISTRY[name.lower()] = cls
        return cls
    return decorator

def get_provider(name: str, config: Optional[Dict[str, Any]] = None) -> BaseLLMProvider:
    """
    Factory function to instantiate an LLM provider.
    If requested provider is unregistered, misconfigured, or unavailable, logs reason
    and falls back to NoneProvider ('none').
    """
    config = config or {}
    provider_name = (name or "none").lower()

    # Parse provider:model format if passed e.g. "ollama:llama3.2" or "openai:gpt-4o-mini"
    model_override = None
    if ":" in provider_name:
        provider_name, model_override = provider_name.split(":", 1)
        config["llm_model"] = model_override

    provider_cls = _PROVIDER_REGISTRY.get(provider_name)
    if not provider_cls:
        if provider_name not in ("none", ""):
            print(f"[llm] Warning: Provider '{provider_name}' is not supported in MVP. Falling back to 'none'.", file=sys.stderr)
        provider_cls = _PROVIDER_REGISTRY.get("none")

    try:
        instance = provider_cls(config)
        if not instance.is_available:
            print(f"[llm] Warning: Provider '{provider_name}' is not available/configured. Falling back to 'none'.", file=sys.stderr)
            fallback_cls = _PROVIDER_REGISTRY.get("none")
            return fallback_cls(config)
        return instance
    except Exception as e:
        print(f"[llm] Error initializing provider '{provider_name}': {e}. Falling back to 'none'.", file=sys.stderr)
        fallback_cls = _PROVIDER_REGISTRY.get("none")
        return fallback_cls(config)
