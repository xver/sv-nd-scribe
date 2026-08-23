# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import sys
import json
import yaml
import importlib
import subprocess
from typing import List, Dict, Any, Optional, Tuple

from linter.core.config_manager import ConfigManager
from agent.fixer.base_fixer import BaseFixer, FixProposal, LinterError
from agent.fixer.file_fixer import FileFixer
from agent.llm.llm_registry import get_provider

class ScribeAgent:
    """Orchestrator for SV ND Scribe AI Agent."""

    def __init__(self, config_file: Optional[str] = None):
        self.config_mgr = ConfigManager(config_file=config_file)
        self.agent_config = self.config_mgr.config.get("agent", {})
        
        # Resolve home path for built-in skills and rules
        self.scribe_home = os.environ.get(
            "SVND_SCRIBE_HOME",
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.skills_dir = os.path.join(self.scribe_home, "skills")
        self.rules_dir = os.path.join(self.scribe_home, "agent", "rules")
        
        self.rules_cache: Dict[str, Dict[str, Any]] = {}
        self._skipped_rules: List[str] = []
        self._fixer_cache: Dict[str, BaseFixer] = {}
        self._llm_debug_log = None
        self._load_built_in_rules()

    def _load_built_in_rules(self) -> None:
        """Load all rule YAML definitions from built-in directory."""
        if not os.path.exists(self.rules_dir):
            return
            
        for fname in os.listdir(self.rules_dir):
            if fname.endswith(".yaml") or fname.endswith(".yml"):
                filepath = os.path.join(self.rules_dir, fname)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        rule_def = yaml.safe_load(f)
                        if not rule_def:
                            continue
                        required = ("rule_id", "fixer_class", "safety")
                        missing = [f for f in required if f not in rule_def]
                        if missing:
                            print(f"[agent] Warning: Rule YAML {fname} missing required fields {missing}, skipping.", file=sys.stderr)
                            self._skipped_rules.append(fname)
                            continue
                        rule_id = rule_def["rule_id"]
                        self.rules_cache[rule_id] = rule_def
                except Exception as e:
                    print(f"[agent] Warning: Skipping rule YAML {filepath}: {e}", file=sys.stderr)
                    self._skipped_rules.append(fname)
                    continue

    def _get_fixer_instance(self, rule_def: Dict[str, Any]) -> Optional[BaseFixer]:
        """Dynamically import and instantiate fixer class specified in rule YAML.
        
        Caches instances by fixer_class path to avoid redundant imports.
        """
        fixer_class_path = rule_def.get("fixer_class")
        if not fixer_class_path:
            return None

        # Check cache first
        if fixer_class_path in self._fixer_cache:
            return self._fixer_cache[fixer_class_path]
            
        try:
            module_name, class_name = fixer_class_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
            instance = cls(rule_config=rule_def)
            self._fixer_cache[fixer_class_path] = instance
            return instance
        except Exception as e:
            print(f"[agent] Warning: Could not load fixer '{fixer_class_path}': {e}", file=sys.stderr)
            return None

    def run_linter(self, files: List[str]) -> Dict[str, Any]:
        """Invoke linter subprocess using sys.executable to preserve active virtualenv.
        
        Raises:
            LinterError: If linter returns empty output, unparseable JSON, or subprocess fails.
        """
        cmd = [sys.executable, "-m", "linter", "--json"] + files
        try:
            env = dict(os.environ)
            env["PYTHONPATH"] = self.scribe_home + os.pathsep + env.get("PYTHONPATH", "")
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, env=env)
            if not res.stdout.strip():
                raise LinterError(f"Linter returned empty response. Stderr: {res.stderr}")
            return json.loads(res.stdout)
        except json.JSONDecodeError as e:
            raise LinterError(f"Failed to parse linter JSON output: {e}") from e
        except LinterError:
            raise
        except Exception as e:
            raise LinterError(f"Error running linter: {e}") from e

    def run(
        self,
        files: List[str],
        mode: str = "interactive",
        rules_filter: Optional[List[str]] = None,
        llm_provider: str = "none",
        no_backup: bool = False,
        dry_run: bool = False,
        json_output: bool = False,
        status_check: bool = False,
        debug_llm: bool = False,
    ) -> int:
        """
        Main execution pipeline.
        Returns exit code: 0 = Clean success, 1 = Failure, 2 = Unresolved violations.
        """
        if debug_llm:
            import datetime
            self._llm_debug_log = open("agent_llm_debug.log", "a", encoding="utf-8")
            self._llm_debug_log.write(
                f"\n# Session: {datetime.datetime.now().isoformat()}\n"
            )
            self._llm_debug_log.flush()
        else:
            self._llm_debug_log = None

        try:
            return self._run_pipeline(
                files=files,
                mode=mode,
                rules_filter=rules_filter,
                llm_provider=llm_provider,
                no_backup=no_backup,
                dry_run=dry_run,
                json_output=json_output,
                status_check=status_check,
            )
        finally:
            if self._llm_debug_log is not None:
                try:
                    self._llm_debug_log.close()
                except Exception:
                    pass
                self._llm_debug_log = None

    def _run_pipeline(
        self,
        files: List[str],
        mode: str = "interactive",
        rules_filter: Optional[List[str]] = None,
        llm_provider: str = "none",
        no_backup: bool = False,
        dry_run: bool = False,
        json_output: bool = False,
        status_check: bool = False,
    ) -> int:
        """Internal pipeline implementation, wrapped by run() for resource cleanup."""
        if status_check:
            return self.print_status(llm_provider)

        if not files:
            print("[agent] Error: No files specified for agent execution.", file=sys.stderr)
            return 1

        provider = get_provider(llm_provider, self.agent_config)
        if llm_provider not in ("none", "") and provider.name not in ("none", ""):
            print(
                f"[agent] Note: LLM provider '{provider.name}' is loaded. "
                f"LLM-assisted generation is Phase 2; deterministic fixers run now.",
                file=sys.stderr,
            )

        # 1. Initial linter run
        linter_data = self.run_linter(files)
        violations = linter_data.get("violations", [])
        
        if not violations:
            if json_output:
                print(json.dumps({"status": "clean", "fixed_count": 0, "remaining_count": 0}))
            else:
                print("[agent] \u2705 No linter violations found. Source code is clean.")
            return 0

        # Filter by rules if requested
        if rules_filter:
            rules_filter_set = {r.strip("[]") for r in rules_filter}
            violations = [v for v in violations if v.get("rule_id", "").strip("[]") in rules_filter_set]

        # Group violations by file
        violations_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for v in violations:
            file_path = v.get("file")
            if file_path:
                violations_by_file.setdefault(file_path, []).append(v)

        file_fixer = FileFixer(
            backup_strategy=self.agent_config.get("backup", "auto"),
            no_backup=no_backup
        )

        all_proposals: List[FixProposal] = []
        file_proposals_map: Dict[str, List[FixProposal]] = {}

        # 2. Generate proposals per file
        for filepath, file_viols in violations_by_file.items():
            if not os.path.exists(filepath):
                continue
                
            source_lines = file_fixer.read_file_lines(filepath)
            
            # Sort violations descending by line number to maintain offset invariant
            sorted_viols = sorted(file_viols, key=lambda v: v.get("line", 0), reverse=True)
            
            # Identify line numbers handled by construct-specific rules to suppress duplicate ND-004 proposals
            specific_rule_lines = {
                v.get("line") for v in sorted_viols
                if v.get("rule_id", "").strip("[]") in {
                    "ND-008", "ND-009", "ND-010", "ND-011", "ND-013", "ND-014", "ND-015",
                    "ND-017", "ND-018", "ND-020", "ND-021", "ND-022", "ND-023", "ND-025",
                    "ND-026", "ND-027", "ND-028", "ND-029", "ND-031", "ND-032"
                }
            }

            seen_rules = set()
            file_props = []
            for v in sorted_viols:
                raw_rule_id = v.get("rule_id", "")
                rule_id = raw_rule_id.strip("[]")
                if rule_id == "ND-001":
                    if "ND-001" in seen_rules:
                        continue
                    seen_rules.add("ND-001")
                raw_rule_id = v.get("rule_id", "")
                rule_id = raw_rule_id.strip("[]")
                rule_def = self.rules_cache.get(rule_id, {})
                
                # Skip generic ND-004 if a specific construct rule handles the same line
                if rule_id == "ND-004" and v.get("line") in specific_rule_lines:
                    continue

                safety = rule_def.get("safety", "unsafe")
                # Removed hardcoded skip for unsafe rules so they can be shown in interactive/dry-run mode
                # Batch mode inherently skips proposals where p.is_safe == False
                    
                fixer = self._get_fixer_instance(rule_def)
                if not fixer:
                    continue
                    
                # Normalize violation rule_id for fixer
                norm_viol = dict(v)
                norm_viol["rule_id"] = rule_id

                proposal = fixer.propose(norm_viol, source_lines, config=self.agent_config, provider=provider)
                if proposal:
                    if isinstance(proposal, list):
                        file_props.extend(proposal)
                        all_proposals.extend(proposal)
                    else:
                        file_props.append(proposal)
                        all_proposals.append(proposal)
                    
            file_proposals_map[filepath] = file_props

        if not all_proposals:
            if json_output:
                print(json.dumps({"status": "no_fixable_violations", "violations": violations}))
            else:
                print("[agent] No auto-fixable safe proposals generated.")
            return 0

        # 3. Dry-run mode
        if dry_run:
            if json_output:
                output_data = {
                    "dry_run": True,
                    "proposals": [
                        {
                            "rule_id": p.rule_id,
                            "file": p.file,
                            "line": p.line,
                            "description": p.description,
                            "is_safe": p.is_safe,
                            "patch_lines": p.patch_lines,
                            "replace_line": p.replace_line,
                            "replace_range": list(p.replace_range) if p.replace_range else None
                        }
                        for p in all_proposals
                    ]
                }
                print(json.dumps(output_data, indent=2))
            else:
                print(f"=== SV ND Scribe Agent \u2014 Dry Run ({len(all_proposals)} proposals) ===")
                for p in all_proposals:
                    print(f"[{p.rule_id}] {p.file}:{p.line} \u2014 {p.description}")
                    for line in p.patch_lines:
                        print(f"  + {line.rstrip()}")
            return 0

        # 4. Apply fixes
        total_applied = 0
        for filepath, proposals in file_proposals_map.items():
            if not proposals:
                continue

            accepted_proposals = []
            if mode == "batch":
                for p in proposals:
                    # Phase 1 Batch policy: skip non-safe or LLM rules if provider is none
                    if p.is_safe:
                        accepted_proposals.append(p)
            else:
                # Interactive mode
                for p in proposals:
                    print(f"\n[{p.rule_id}] {p.file}:{p.line} \u2014 {p.description}")
                    for line in p.patch_lines:
                        print(f"  + {line.rstrip()}")
                    choice = input("Apply fix? [y/n/q]: ").strip().lower()
                    if choice == "y":
                        accepted_proposals.append(p)
                    elif choice == "q":
                        break

            if accepted_proposals:
                source_lines = file_fixer.read_file_lines(filepath)
                # Single-pass line mutation sorted line-desc
                modified_lines = file_fixer.apply_proposals_in_memory(source_lines, accepted_proposals)
                
                # Backup and atomic write
                file_fixer.handle_backup(filepath)
                file_fixer.write_file_atomic(filepath, modified_lines)
                total_applied += len(accepted_proposals)

        # 5. Post-fix re-lint verification
        post_linter_data = self.run_linter(files)
        post_violations = post_linter_data.get("violations", [])
        
        remaining_safe_viols = [
            v for v in post_violations
            if self.rules_cache.get(
                v.get("rule_id", "").strip("[]"), {}
            ).get("safety") == "safe"
        ]

        if json_output:
            print(json.dumps({
                "status": "applied",
                "applied_count": total_applied,
                "remaining_count": len(post_violations),
                "remaining_safe_count": len(remaining_safe_viols)
            }))
        else:
            print(f"\n[agent] Re-lint verification complete.")
            print(f"  Fixes applied           : {total_applied}")
            print(f"  Remaining total errors  : {len(post_violations)}")
            print(f"  Remaining safe violations: {len(remaining_safe_viols)}")

        if remaining_safe_viols:
            print("[agent] Warning: Remaining safe violations detected after batch fix.", file=sys.stderr)
            return 2

        return 0

    def print_status(self, llm_provider: str = "none") -> int:
        """Print status report of agent environment and connectivity."""
        provider = get_provider(llm_provider, self.agent_config)
        reachable = "reachable" if provider.is_available else "unreachable / disabled"
        
        print("SV ND Scribe Agent \u2014 Status")
        print("=" * 50)
        print(f"LLM Provider   : {provider.name} (from agent_config.json)")
        print(f"LLM Model      : {self.agent_config.get('llm_model', 'default')}")
        print(f"Connectivity   : {'[OK]' if provider.is_available else '[FAIL]'} {reachable}")
        print(f"Fallback       : none (deterministic) if LLM fails")
        print(f"Skills dir     : {self.skills_dir}  [built-in only]")
        print(f"Rules dir      : {self.rules_dir}   [built-in only]")
        if self._skipped_rules:
            print(f"Skipped rules  : {len(self._skipped_rules)} invalid YAML rule(s)")
        print(f"Backup strategy: {self.agent_config.get('backup', 'auto')}")
        print(f"Config file    : {self.config_mgr.config_file or 'built-in defaults'}")
        print("=" * 50)
        print("*(Note: Project/user overrides appear only in Phase 2.)*")
        
        return 0 if provider.is_available else 1
