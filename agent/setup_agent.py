# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

"""
Setup & Environment Troubleshooter Agent for SV ND Scribe.
Provides programmatic diagnostics (--doctor) and automated repair (--fix-setup).
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

DEFAULT_LINT_CONFIG = {
    "project": {
        "name": "sv-nd-scribe",
        "company": "IC Verimeter",
        "description": "SystemVerilog NaturalDocs & Wellknown Style Linter"
    },
    "linters": {
        "naturaldoc": {
            "enabled": True
        },
        "wellknown": {
            "enabled": True
        }
    },
    "global": {
        "strict_mode": False,
        "use_color": True
    }
}

class SetupAgent:
    """Diagnoses and fixes SV ND Scribe setup, environment, and workspace configuration."""

    def __init__(self, repo_dir: Optional[str] = None):
        if repo_dir:
            self.repo_dir = Path(repo_dir).resolve()
        else:
            # Auto-detect repository root by locating 'linter' and 'agent' dirs
            current = Path(__file__).resolve().parent.parent
            if (current / "linter").exists() and (current / "agent").exists():
                self.repo_dir = current
            else:
                self.repo_dir = Path(os.environ.get("SVND_SCRIBE_HOME", str(current))).resolve()

    def diagnose(self) -> List[Dict[str, Any]]:
        """Run 7-step diagnostics and return report list."""
        results = []

        # ── Step 1: Python Version ──────────────────────────────────────
        py_ver = sys.version_info
        py_ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
        if py_ver.major >= 3 and py_ver.minor >= 9:
            results.append({
                "step": 1,
                "name": "Python 3.9+",
                "status": "pass",
                "message": f"Python {py_ver_str} ({sys.executable})"
            })
        else:
            results.append({
                "step": 1,
                "name": "Python 3.9+",
                "status": "fail",
                "message": f"Python {py_ver_str} is too old (3.9+ required)",
                "fix_action": "Install Python 3.9 or newer"
            })

        # ── Step 2: Verible ─────────────────────────────────────────────
        verible_bin = shutil.which("verible-verilog-syntax") or shutil.which("verible-verilog-syntax.exe")
        verible_home = os.environ.get("VERIBLE_HOME")
        if not verible_bin and verible_home:
            candidate = Path(verible_home) / "bin" / "verible-verilog-syntax"
            candidate_win = Path(verible_home) / "bin" / "verible-verilog-syntax.exe"
            if candidate.exists():
                verible_bin = str(candidate)
            elif candidate_win.exists():
                verible_bin = str(candidate_win)

        if verible_bin:
            try:
                out = subprocess.check_output([verible_bin, "--version"], stderr=subprocess.STDOUT, text=True)
                first_line = out.strip().split("\n")[0]
                results.append({
                    "step": 2,
                    "name": "Verible Parser",
                    "status": "pass",
                    "message": f"{first_line} ({verible_bin})"
                })
            except Exception as e:
                results.append({
                    "step": 2,
                    "name": "Verible Parser",
                    "status": "warn",
                    "message": f"Found at {verible_bin} but execution failed: {e}"
                })
        else:
            results.append({
                "step": 2,
                "name": "Verible Parser",
                "status": "fail",
                "message": "verible-verilog-syntax not found in PATH or VERIBLE_HOME",
                "fix_action": "Download Verible release from https://github.com/chipsalliance/verible/releases"
            })

        # ── Step 3: PyYAML ──────────────────────────────────────────────
        try:
            import yaml
            results.append({
                "step": 3,
                "name": "PyYAML",
                "status": "pass",
                "message": f"PyYAML {yaml.__version__}"
            })
        except ImportError:
            results.append({
                "step": 3,
                "name": "PyYAML",
                "status": "fail",
                "message": "pyyaml package is not installed",
                "fix_action": "pip install pyyaml"
            })

        # ── Step 4: Repository Structure ────────────────────────────────
        linter_dir = self.repo_dir / "linter"
        agent_dir = self.repo_dir / "agent"
        if linter_dir.exists() and agent_dir.exists():
            results.append({
                "step": 4,
                "name": "Repository Root",
                "status": "pass",
                "message": f"Valid repository tree at {self.repo_dir}"
            })
        else:
            results.append({
                "step": 4,
                "name": "Repository Root",
                "status": "fail",
                "message": f"Directory {self.repo_dir} missing linter/ or agent/ subdirectories",
                "fix_action": "Clone repository: git clone https://github.com/xver/sv-nd-scribe.git"
            })

        # ── Step 5: SVND_SCRIBE_HOME ────────────────────────────────────
        env_home = os.environ.get("SVND_SCRIBE_HOME", "").strip()
        if env_home:
            resolved_env_home = Path(env_home).resolve()
            if resolved_env_home.exists():
                results.append({
                    "step": 5,
                    "name": "SVND_SCRIBE_HOME",
                    "status": "pass",
                    "message": f"Set to {env_home}"
                })
            else:
                results.append({
                    "step": 5,
                    "name": "SVND_SCRIBE_HOME",
                    "status": "warn",
                    "message": f"Set to {env_home} but path does not exist",
                    "fix_action": f"Export SVND_SCRIBE_HOME={self.repo_dir}"
                })
        else:
            results.append({
                "step": 5,
                "name": "SVND_SCRIBE_HOME",
                "status": "warn",
                "message": f"Environment variable not set (auto-detected: {self.repo_dir})",
                "fix_action": f"Export SVND_SCRIBE_HOME={self.repo_dir} or run setup automation"
            })

        # ── Step 6: Workspace Configuration ─────────────────────────────
        settings_file = self.repo_dir / ".vscode" / "settings.json"
        env_file = self.repo_dir / ".env"
        config_dir = self.repo_dir / "linter" / "configs"
        config_file = config_dir / "lint_config.json"

        cfg_issues = []
        if not settings_file.exists():
            cfg_issues.append("missing .vscode/settings.json")
        if not env_file.exists():
            cfg_issues.append("missing .env")
        if not config_file.exists():
            cfg_issues.append("missing linter/configs/lint_config.json")

        if not cfg_issues:
            results.append({
                "step": 6,
                "name": "Workspace Config",
                "status": "pass",
                "message": ".vscode/settings.json, .env, and lint_config.json present"
            })
        else:
            results.append({
                "step": 6,
                "name": "Workspace Config",
                "status": "warn",
                "message": f"Partially configured ({', '.join(cfg_issues)})",
                "fix_action": "Run 'python3 -m agent --fix-setup' or 'make setup_workspace'"
            })

        # ── Step 7: Linter Execution ────────────────────────────────────
        linter_entry = self.repo_dir / "linter" / "linter.py"
        if not linter_entry.exists():
            linter_entry = self.repo_dir / "linter" / "__main__.py"

        if linter_entry.exists():
            env = dict(os.environ)
            env["SVND_SCRIBE_HOME"] = str(self.repo_dir)
            curr_pypath = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = f"{self.repo_dir}:{curr_pypath}" if curr_pypath else str(self.repo_dir)
            env["SV_ND_SCRIBE_PROJECT_CONFIG"] = str(config_dir)

            try:
                proc = subprocess.run(
                    [sys.executable, str(linter_entry), "--status"],
                    capture_output=True,
                    text=True,
                    env=env,
                    cwd=str(self.repo_dir),
                    timeout=10
                )
                if proc.returncode == 0:
                    results.append({
                        "step": 7,
                        "name": "Linter Module",
                        "status": "pass",
                        "message": proc.stdout.strip() or "Initialized cleanly"
                    })
                else:
                    results.append({
                        "step": 7,
                        "name": "Linter Module",
                        "status": "fail",
                        "message": (proc.stderr.strip() or proc.stdout.strip() or "Initialization failed"),
                        "fix_action": "Check Python dependencies and paths"
                    })
            except Exception as e:
                results.append({
                    "step": 7,
                    "name": "Linter Module",
                    "status": "fail",
                    "message": f"Failed to execute linter: {e}",
                    "fix_action": "Check Python interpreter and permissions"
                })
        else:
            results.append({
                "step": 7,
                "name": "Linter Module",
                "status": "fail",
                "message": f"Linter executable not found at {linter_entry}",
                "fix_action": "Re-download repository"
            })

        return results

    def fix_setup(self) -> Dict[str, Any]:
        """Perform automated repair of workspace configuration and defaults."""
        actions_taken = []

        # 1. Ensure linter/configs/lint_config.json exists
        config_dir = self.repo_dir / "linter" / "configs"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "lint_config.json"
        if not config_file.exists():
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_LINT_CONFIG, f, indent=2)
            actions_taken.append(f"Created {config_file.relative_to(self.repo_dir)}")

        # 2. Invoke setup_workspace.py to configure .vscode/settings.json, .env, and makedir/env.sh
        setup_script = self.repo_dir / "makedir" / "setup_workspace.py"
        if setup_script.exists():
            try:
                proc = subprocess.run(
                    [sys.executable, str(setup_script), "-w", str(self.repo_dir)],
                    capture_output=True,
                    text=True,
                    cwd=str(self.repo_dir),
                    timeout=15
                )
                if proc.returncode == 0:
                    actions_taken.append("Ran setup_workspace.py (configured .vscode/settings.json, .env, and makedir/env.sh)")
                else:
                    actions_taken.append(f"setup_workspace.py warning: {proc.stderr.strip() or proc.stdout.strip()}")
            except Exception as e:
                actions_taken.append(f"Failed to run setup_workspace.py: {e}")

        # 3. Post-repair diagnostic
        diagnostics = self.diagnose()
        all_passed = all(d["status"] in ("pass", "warn") for d in diagnostics)
        hard_fails = [d for d in diagnostics if d["status"] == "fail"]

        return {
            "success": all_passed and len(hard_fails) == 0,
            "actions": actions_taken,
            "diagnostics": diagnostics
        }

    def print_doctor_report(self, as_json: bool = False) -> int:
        """Run diagnose and print human-readable or JSON report."""
        report = self.diagnose()
        if as_json:
            print(json.dumps({"checks": report}, indent=2))
        else:
            print("=================================================================")
            print("  SV ND Scribe — Environment Doctor & Verification")
            print("=================================================================")
            for item in report:
                icon = "✅" if item["status"] == "pass" else "⚠️" if item["status"] == "warn" else "❌"
                print(f"{icon} Step {item['step']}/7: {item['name']}")
                print(f"   Detail: {item['message']}")
                if "fix_action" in item:
                    print(f"   Action: {item['fix_action']}")
            print("=================================================================")

        has_failure = any(d["status"] == "fail" for d in report)
        return 1 if has_failure else 0