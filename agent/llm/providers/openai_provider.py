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

@register_llm("openai")
class OpenAIProvider(BaseLLMProvider):
    """OpenAI / Azure OpenAI provider using stdlib urllib to avoid third-party dependencies."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.model = self.config.get("llm_model") or os.environ.get("OPENAI_MODEL", "gpt-4o")
        self.api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")

    @property
    def name(self) -> str:
        return "openai"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key.strip())

    def complete(self, prompt: str, system: str = "", timeout: int = 30, debug_log: Optional[IO] = None) -> str:
        if not self.is_available:
            print("[llm] Warning: OPENAI_API_KEY environment variable is not set.", file=sys.stderr)
            return ""

        url = f"{self.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": float(self.config.get("llm_temperature", 0.2))
        }

        if debug_log:
            debug_log.write(f"\n## OpenAI Request (model={self.model})\n")
            debug_log.write(f"System: {system[:200]}{'...' if len(system) > 200 else ''}\n")
            debug_log.write(f"Prompt: {prompt[:500]}{'...' if len(prompt) > 500 else ''}\n")
            debug_log.flush()

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                resp_json = json.loads(response.read().decode("utf-8"))
                choices = resp_json.get("choices", [])
                if choices:
                    result = choices[0].get("message", {}).get("content", "").strip()
                    if debug_log:
                        debug_log.write(f"Response: {result[:500]}{'...' if len(result) > 500 else ''}\n")
                        debug_log.write("---\n")
                        debug_log.flush()
                    return result
        except urllib.error.URLError as e:
            print(f"[llm] OpenAI connection error: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[llm] OpenAI request error: {e}", file=sys.stderr)

        if debug_log:
            debug_log.write("Response: <error/empty>\n---\n")
            debug_log.flush()

        return ""
