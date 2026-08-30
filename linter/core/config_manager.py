"""
Configuration management for linters

Company: Copyright (c) 2026  IC Verimeter
         Licensed under the MIT License.

Description: Handles loading and managing hierarchical configuration for linters and rules.
             Supports linking individual linter configurations from a root configuration.
"""

import json
import os
import sys
from copy import deepcopy
from typing import Any, Dict, Optional, TextIO
from pathlib import Path

# Environment variable: directory containing project sv-nd-scribe JSON configs (e.g. lint_config.json).
ENV_SV_ND_SCRIBE_PROJECT_CONFIG = "SV_ND_SCRIBE_PROJECT_CONFIG"

# Emit "SV_ND_SCRIBE_PROJECT_CONFIG is not set" at most once per process (ConfigManager may be constructed twice).
_SV_ND_SCRIBE_PROJECT_CONFIG_WARNED = False


def _sv_nd_scribe_config_warning_stream() -> TextIO:
    """Use sys.stderr for warnings and logs to prevent stdout pollution."""
    return sys.stderr


def resolve_sv_nd_scribe_project_config_dir(*, emit_unset_warning: bool = True) -> Path:
    """
    Resolve the project config directory for sv-nd-scribe.

    - If SV_ND_SCRIBE_PROJECT_CONFIG is set to an existing directory, use it (resolved).
    - If unset/empty: default to <linter_root>/configs and optionally warn (once per process).
    - If set but not a directory: warn and fall back to <linter_root>/configs.

    Warnings go to stdout by default (flush=True) so they show in typical IDE output; with --json,
    warnings use stderr so stdout remains parseable JSON.

    Args:
        emit_unset_warning: If False, skip the "env not set" message (internal/testing).
    """
    global _SV_ND_SCRIBE_PROJECT_CONFIG_WARNED
    script_dir = Path(__file__).resolve().parent.parent
    default_dir = (script_dir / "configs").resolve()
    warn_stream = _sv_nd_scribe_config_warning_stream()

    raw = os.environ.get(ENV_SV_ND_SCRIBE_PROJECT_CONFIG, "").strip()
    if not raw:
        if emit_unset_warning and not _SV_ND_SCRIBE_PROJECT_CONFIG_WARNED:
            print(
                f"sv-nd-scribe: Warning: {ENV_SV_ND_SCRIBE_PROJECT_CONFIG} is not set; using default "
                f"project config directory {default_dir}",
                file=warn_stream,
                flush=True,
            )
            _SV_ND_SCRIBE_PROJECT_CONFIG_WARNED = True
        return default_dir

    candidate = Path(raw).expanduser()
    try:
        resolved = candidate.resolve()
    except (OSError, RuntimeError):
        resolved = candidate if candidate.is_absolute() else (Path.cwd() / candidate).resolve()

    if not resolved.is_dir():
        if not _SV_ND_SCRIBE_PROJECT_CONFIG_WARNED:
            print(
                f"sv-nd-scribe: Warning: {ENV_SV_ND_SCRIBE_PROJECT_CONFIG}={raw!r} is not a directory; "
                f"using default {default_dir}",
                file=warn_stream,
                flush=True,
            )
            _SV_ND_SCRIBE_PROJECT_CONFIG_WARNED = True
        return default_dir

    return resolved


class ConfigManager:
    """
    Manages hierarchical configuration loading and access

    Supports:
    - Root configuration with linter enable/disable flags
    - Linked individual linter configuration files
    - JSON configuration files
    - Default configurations
    - Per-linter configurations
    - Per-rule configurations

    Hierarchical Structure:
        root_config.json:
        {
            "linters": {
                "naturaldocs": {
                    "enabled": true,
                    "config_file": "configs/naturaldocs.json"
                },
                "verible": {
                    "enabled": false,
                    "config_file": "configs/verible.json"
                }
            }
        }
    """

    def __init__(self, config_file: Optional[str] = None, base_config_file: Optional[str] = None):
        """
        Initialize configuration manager with hierarchical support

        Args:
            config_file: Path to project/root configuration file (JSON)
            base_config_file: Optional path to common/base configuration file (JSON)
        """
        self.config_file = config_file
        self.base_config_file = base_config_file
        # Project config dir: SV_ND_SCRIBE_PROJECT_CONFIG or <linter>/configs (see resolve_sv_nd_scribe_project_config_dir).
        # Always warn when SV_ND_SCRIBE_PROJECT_CONFIG is unset (visible on stdout unless --json).
        self.project_config_dir = resolve_sv_nd_scribe_project_config_dir()
        # Directory used to resolve relative paths in the loaded root config (linked linter JSON, etc.).
        if config_file:
            self.config_dir = Path(config_file).parent
        else:
            self.config_dir = self.project_config_dir
        self.loaded_configs = {}  # Cache for loaded linked configs
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """
        Load hierarchical configuration from file or use defaults

        Supports loading a root config that links to individual linter configs.

        Returns:
            Configuration dictionary
        """
        project_config = None
        project_config_dir = self.config_dir

        # Try to load from explicit -c/--config path
        if self.config_file:
            if os.path.exists(self.config_file):
                project_config = self._load_json_file(self.config_file, "config")
                project_config_dir = Path(self.config_file).parent
            else:
                print(f"Warning: Config file not found: {self.config_file}", file=sys.stderr)

        # Implicit root: $SV_ND_SCRIBE_PROJECT_CONFIG/lint_config.json (default dir is configs)
        if project_config is None:
            candidate = self.project_config_dir / "lint_config.json"
            if candidate.exists():
                project_config = self._load_json_file(str(candidate), "project lint config")
                project_config_dir = self.project_config_dir
                if not self.config_file:
                    self.config_dir = self.project_config_dir

        # Bundled fallback if project dir has no lint_config.json
        if project_config is None:
            script_dir = Path(__file__).parent.parent
            bundled = script_dir / "configs" / "lint_config.json"
            if bundled.exists():
                project_config = self._load_json_file(str(bundled), "default config")
                project_config_dir = bundled.parent
                if not self.config_file:
                    self.config_dir = bundled.parent

        # Return minimal default configuration
        if project_config is None:
            return self._get_default_config()

        # Resolve and load base/common config if provided.
        # Precedence is: --base-config (CLI) > "extends" key in project config.
        base_reference = self.base_config_file or project_config.get("extends")
        if base_reference:
            base_config = self._load_base_config(base_reference, project_config_dir)
            if base_config is not None:
                project_config = self._deep_merge_configs(base_config, project_config)

        if "extends" in project_config:
            project_config.pop("extends")

        # Process hierarchical structure if present
        return self._process_hierarchical_config(project_config)

    def _load_json_file(self, config_path: str, label: str) -> Optional[dict]:
        """Load JSON file with warning handling."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load {label} from {config_path}: {e}")
            return None

    def _resolve_config_path(self, path_value: str, base_dir: Path) -> str:
        """Resolve config path relative to base_dir unless already absolute."""
        if os.path.isabs(path_value):
            return path_value
        return str((base_dir / path_value).resolve())

    def _load_base_config(self, base_reference: str, reference_dir: Path) -> Optional[dict]:
        """
        Load base/common config and normalize linked config_file paths.

        Also supports chained inheritance via "extends" inside base config.
        """
        resolved_base_path = self._resolve_config_path(base_reference, reference_dir)
        base_config = self._load_json_file(resolved_base_path, "base config")
        if base_config is None:
            return None

        base_dir = Path(resolved_base_path).parent
        nested_base_reference = base_config.get("extends")
        if nested_base_reference:
            nested_base = self._load_base_config(nested_base_reference, base_dir)
            if nested_base is not None:
                base_config = self._deep_merge_configs(nested_base, base_config)

        if "extends" in base_config:
            base_config.pop("extends")

        # Convert relative linked linter config paths to absolute paths so they
        # continue to resolve correctly after merging into a project config.
        normalized = deepcopy(base_config)
        linters = normalized.get("linters", {})
        if isinstance(linters, dict):
            for _, linter_cfg in linters.items():
                if isinstance(linter_cfg, dict) and "config_file" in linter_cfg:
                    cfg_path = linter_cfg["config_file"]
                    if isinstance(cfg_path, str) and not os.path.isabs(cfg_path):
                        linter_cfg["config_file"] = self._resolve_config_path(cfg_path, base_dir)
        return normalized

    def _deep_merge_configs(self, base: Any, override: Any) -> Any:
        """
        Merge two config values with project-precedence semantics.

        Merge rules:
        - Dicts: recursively merged.
        - Scalars/bools/strings: override replaces base.
        - Lists: override replaces base (predictable, explicit behavior).
        """
        if isinstance(base, dict) and isinstance(override, dict):
            merged = deepcopy(base)
            for key, value in override.items():
                if key in merged:
                    merged[key] = self._deep_merge_configs(merged[key], value)
                else:
                    merged[key] = deepcopy(value)
            return merged

        if isinstance(override, list):
            return deepcopy(override)

        return deepcopy(override)

    def _process_hierarchical_config(self, config: dict) -> dict:
        """
        Process hierarchical configuration structure

        This method checks if linters have linked config files and merges them.

        Args:
            config: Root configuration dictionary

        Returns:
            Processed configuration with linked configs merged
        """
        if "linters" not in config:
            return config

        linters = config["linters"]

        for linter_name, linter_config in linters.items():
            # Check if this linter has a linked config file
            if isinstance(linter_config, dict) and "config_file" in linter_config:
                linked_config_path = linter_config["config_file"]

                # Resolve relative path from config directory
                if not os.path.isabs(linked_config_path):
                    linked_config_path = os.path.join(self.config_dir, linked_config_path)

                # Load linked configuration
                linked_config = self._load_linked_config(linked_config_path)

                if linked_config:
                    # Merge linked config into linter config
                    # Root config settings take precedence (especially 'enabled')
                    enabled = linter_config.get("enabled", True)
                    merged_config = {**linked_config, **linter_config}
                    merged_config["enabled"] = enabled

                    # Remove config_file from final config to avoid confusion
                    if "config_file" in merged_config:
                        merged_config["_source_config"] = merged_config.pop("config_file")

                    config["linters"][linter_name] = merged_config

        return config

    def _load_linked_config(self, config_path: str, visited: Optional[set] = None) -> Optional[dict]:
        """
        Load a linked configuration file

        Args:
            config_path: Path to linked configuration file
            visited: Set of visited config paths for cycle detection

        Returns:
            Configuration dictionary or None if loading fails
        """
        if visited is None:
            visited = set()

        resolved_path = os.path.realpath(config_path)
        if resolved_path in visited:
            print(f"Warning: Cyclic linked config inheritance detected: {resolved_path}")
            return None
        visited.add(resolved_path)

        # Check cache first
        if resolved_path in self.loaded_configs:
            return self.loaded_configs[resolved_path]

        if not os.path.exists(resolved_path):
            print(f"Warning: Linked config file not found: {resolved_path}")
            return None

        try:
            with open(resolved_path, 'r') as f:
                config = json.load(f)

            # Support inheritance for linked linter configs as well.
            # "extends" path is resolved relative to the current linked config file.
            extends_ref = config.get("extends")
            if extends_ref:
                base_dir = Path(resolved_path).parent
                base_path = self._resolve_config_path(extends_ref, base_dir)
                base_config = self._load_linked_config(base_path, visited)
                if base_config is not None:
                    config = self._deep_merge_configs(base_config, config)
                config.pop("extends", None)

            self.loaded_configs[resolved_path] = config
            return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load linked config from {resolved_path}: {e}")
            return None

    def _get_default_config(self) -> dict:
        """
        Get default configuration structure

        Returns:
            Default configuration dictionary with empty strings for project info
        """
        return {
            "project": {
                "name": "",
                "company": "",
                "description": ""
            },
            "linters": {},
            "global": {
                "strict_mode": False,
                "use_color": False
            }
        }

    def get_linter_config(self, linter_name: str) -> dict:
        """
        Get configuration for a specific linter

        Args:
            linter_name: Name of the linter

        Returns:
            Configuration dictionary for the linter (merged from linked configs if present)
        """
        return self.config.get("linters", {}).get(linter_name, {})

    def is_linter_enabled(self, linter_name: str) -> bool:
        """
        Check if a linter is enabled in the configuration

        Args:
            linter_name: Name of the linter

        Returns:
            True if linter is enabled (default: True)
        """
        linter_config = self.get_linter_config(linter_name)
        return linter_config.get("enabled", True)

    def get_rule_config(self, linter_name: str, rule_id: str) -> dict:
        """
        Get configuration for a specific rule

        Args:
            linter_name: Name of the linter
            rule_id: ID of the rule

        Returns:
            Configuration dictionary for the rule
        """
        linter_config = self.get_linter_config(linter_name)
        rules_config = linter_config.get("rules", {})
        return rules_config.get(rule_id, {})

    def is_rule_enabled(self, linter_name: str, rule_id: str) -> bool:
        """
        Check if a rule is enabled

        Args:
            linter_name: Name of the linter
            rule_id: ID of the rule

        Returns:
            True if rule is enabled (default: True)
        """
        rule_config = self.get_rule_config(linter_name, rule_id)
        return rule_config.get("enabled", True)

    def get_rule_severity(self, linter_name: str, rule_id: str, default: str = "ERROR") -> str:
        """
        Get severity level for a rule

        Checks both 'rules' and 'severity_levels' sections for compatibility

        Args:
            linter_name: Name of the linter
            rule_id: ID of the rule
            default: Default severity if not configured

        Returns:
            Severity string ("ERROR", "WARNING", or "INFO")
        """
        linter_config = self.get_linter_config(linter_name)

        # Check 'rules' section first (new format)
        rule_config = self.get_rule_config(linter_name, rule_id)
        if 'severity' in rule_config:
            return rule_config['severity']

        # Check 'severity_levels' section (NaturalDocs format)
        severity_levels = linter_config.get('severity_levels', {})
        if rule_id in severity_levels:
            return severity_levels[rule_id]

        return default

    def get_global_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a global setting

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        return self.config.get("global", {}).get(key, default)

    def get_project_info(self) -> dict:
        """
        Get project information

        Returns:
            Project info dictionary
        """
        return self.config.get("project", {})

    def get_project_config_directory(self) -> Path:
        """
        Directory from SV_ND_SCRIBE_PROJECT_CONFIG (or default configs).

        Used as the first place to look for lint_config.json when -c is omitted.
        """
        return self.project_config_dir

    def save_config(self, output_path: str):
        """
        Save current configuration to file

        Args:
            output_path: Path to save configuration
        """
        with open(output_path, 'w') as f:
            json.dump(self.config, f, indent=2)

