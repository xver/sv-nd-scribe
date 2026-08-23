# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import sys
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, IO
from ..base_llm import BaseLLMProvider
from ..llm_registry import register_llm

@register_llm("ollama")
class OllamaProvider(BaseLLMProvider):
    """Local Ollama provider using stdlib urllib."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.host = self.config.get("ollama_host") or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.host = self.host.rstrip("/")
        self.model = self.config.get("llm_model") or "llama3.2"

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def is_available(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            url = f"{self.host}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def complete(self, prompt: str, system: str = "", timeout: int = 30, debug_log: Optional[IO] = None) -> str:
        url = f"{self.host}/api/generate"
        headers = {"Content-Type": "application/json"}
        
        full_prompt = prompt
        if system:
            full_prompt = f"System Instruction: {system}\n\nUser Prompt: {prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": float(self.config.get("llm_temperature", 0.2))
            }
        }

        if debug_log:
            debug_log.write(f"\n## Ollama Request (model={self.model})\n")
            debug_log.write(f"System: {system[:200]}{'...' if len(system) > 200 else ''}\n")
            debug_log.write(f"Prompt: {prompt[:500]}{'...' if len(prompt) > 500 else ''}\n")
            debug_log.flush()

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                resp_json = json.loads(response.read().decode("utf-8"))
                result = resp_json.get("response", "").strip()
                if debug_log:
                    debug_log.write(f"Response: {result[:500]}{'...' if len(result) > 500 else ''}\n")
                    debug_log.write("---\n")
                    debug_log.flush()
                return result
        except urllib.error.URLError as e:
            print(f"[llm] Ollama connection error ({self.host}): {e}", file=sys.stderr)
        except Exception as e:
            print(f"[llm] Ollama request error: {e}", file=sys.stderr)

        if debug_log:
            debug_log.write("Response: <error/empty>\n---\n")
            debug_log.flush()

        return ""
