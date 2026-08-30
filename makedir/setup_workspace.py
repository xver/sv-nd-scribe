#!/usr/bin/env python3
# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

"""
Configure VS Code Workspace Settings & Environment Variables for SV ND Scribe.
Automatically configures:
  1. .vscode/settings.json (sv-nd-scribe settings, terminal env, file associations)
  2. .env file in the workspace root
  3. makedir/env.sh for sourcing in terminal shells
  4. linter/configs/lint_config.json default configuration
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional

def get_default_workspace_dir() -> str:
    """Resolve project root directory from script location."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)

def resolve_python_path() -> str:
    """Detect current virtualenv python or default to 'python3'."""
    if os.environ.get("VIRTUAL_ENV"):
        return sys.executable
    return "python3"

def load_existing_settings(settings_path: str) -> Dict[str, Any]:
    """Read existing .vscode/settings.json safely, stripping simple comments if any."""
    if not os.path.exists(settings_path):
        return {}
    
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Remove single-line comments // from JSON if present
        clean_lines = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            clean_lines.append(line)
        clean_content = "\n".join(clean_lines)
        return json.loads(clean_content)
    except Exception as e:
        print(f"[configure_vscode] Warning: Could not parse existing settings.json ({e}). Overwriting with fresh settings.", file=sys.stderr)
        return {}

def save_settings(settings_path: str, settings: Dict[str, Any]) -> None:
    """Write formatted JSON to .vscode/settings.json."""
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")

def write_env_file(env_path: str, env_vars: Dict[str, str]) -> None:
    """Write standard key=value .env file."""
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("# SV ND Scribe Workspace Environment Variables\n")
        f.write("# Generated automatically by makedir/setup_workspace.py\n\n")
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

def write_env_sh(env_sh_path: str, env_vars: Optional[Dict[str, str]] = None) -> None:
    """Write shell script for sourcing with dynamic root path resolution."""
    content = (
        "#!/usr/bin/env bash\n"
        "# SV ND Scribe Shell Environment\n"
        "# Source with: source makedir/env.sh\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n\n'
        'export SVND_SCRIBE_HOME="${PROJECT_ROOT}"\n'
        'export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"\n'
        'export SV_ND_SCRIBE_PROJECT_CONFIG="${PROJECT_ROOT}/linter/configs"\n'
    )
    with open(env_sh_path, "w", encoding="utf-8") as f:
        f.write(content)
    try:
        os.chmod(env_sh_path, 0o755)
    except Exception:
        pass

def ensure_default_config(workspace_dir: str) -> None:
    """Ensure linter/configs/lint_config.json exists with default settings."""
    cfg_dir = os.path.join(workspace_dir, "linter", "configs")
    os.makedirs(cfg_dir, exist_ok=True)
    cfg_file = os.path.join(cfg_dir, "lint_config.json")
    if not os.path.exists(cfg_file):
        default_cfg = {
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
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(default_cfg, f, indent=2)
            f.write("\n")

def main():
    parser = argparse.ArgumentParser(
        description="Configure workspace environment, shell env scripts, and IDE settings for SV ND Scribe"
    )
    parser.add_argument(
        "-w", "--workspace",
        default=get_default_workspace_dir(),
        help="Path to workspace root directory (default: parent of makedir)"
    )
    parser.add_argument(
        "-p", "--python-path",
        help="Path or name of Python interpreter (default: active python or 'python3')"
    )
    parser.add_argument(
        "--absolute",
        action="store_true",
        help="Use absolute filesystem paths in settings.json instead of ${workspaceFolder} variables"
    )
    parser.add_argument(
        "--run-on",
        choices=["onSave", "onOpen"],
        default="onSave",
        help="When to trigger linter diagnostics: onSave or onOpen (default: onSave)"
    )
    parser.add_argument(
        "--disable-quick-fix",
        action="store_true",
        help="Disable Quick Fix suggestions"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Display current SV ND Scribe configuration and environment status"
    )

    args = parser.parse_args()
    workspace_dir = os.path.abspath(args.workspace)
    vscode_dir = os.path.join(workspace_dir, ".vscode")
    settings_path = os.path.join(vscode_dir, "settings.json")
    env_file_path = os.path.join(workspace_dir, ".env")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_sh_path = os.path.join(script_dir, "env.sh")

    existing_settings = load_existing_settings(settings_path)

    if args.status:
        print("=== SV ND Scribe VS Code Configuration Status ===")
        print(f"Workspace Directory : {workspace_dir}")
        print(f"Settings Path       : {settings_path} ({'Found' if os.path.exists(settings_path) else 'Not Found'})")
        print(f".env File Path      : {env_file_path} ({'Found' if os.path.exists(env_file_path) else 'Not Found'})")
        print(f"Shell env script    : {env_sh_path} ({'Found' if os.path.exists(env_sh_path) else 'Not Found'})")
        print()
        if os.path.exists(settings_path):
            print("Settings in settings.json:")
            scribe_keys = [k for k in existing_settings if k.startswith("sv-nd-scribe")]
            if scribe_keys:
                for k in sorted(scribe_keys):
                    print(f"  {k:32} : {existing_settings[k]}")
            else:
                print("  No 'sv-nd-scribe.*' settings found.")
        sys.exit(0)

    # Ensure linter/configs/lint_config.json is present
    ensure_default_config(workspace_dir)

    # Determine paths
    if args.absolute:
        linter_path = os.path.join(workspace_dir, "linter", "linter.py")
        agent_path = os.path.join(workspace_dir, "agent")
        scribe_home = workspace_dir
        python_path_env = workspace_dir
        project_config_dir = os.path.join(workspace_dir, "linter", "configs")
    else:
        linter_path = "${workspaceFolder}/linter/linter.py"
        agent_path = "${workspaceFolder}/agent"
        scribe_home = "${workspaceFolder}"
        python_path_env = "${workspaceFolder}"
        project_config_dir = "${workspaceFolder}/linter/configs"

    python_path = args.python_path or resolve_python_path()
    enable_quick_fix = not args.disable_quick_fix

    # Merge into existing settings
    updated_settings = dict(existing_settings)
    updated_settings["sv-nd-scribe.linterPath"] = linter_path
    updated_settings["sv-nd-scribe.agentPath"] = agent_path
    updated_settings["sv-nd-scribe.pythonPath"] = python_path
    updated_settings["sv-nd-scribe.runOn"] = args.run_on
    updated_settings["sv-nd-scribe.enableQuickFix"] = enable_quick_fix

    # 1. Environment variables for sv-nd-scribe extension processes
    updated_settings["sv-nd-scribe.env"] = {
        "SVND_SCRIBE_HOME": scribe_home,
        "PYTHONPATH": python_path_env,
        "SV_ND_SCRIBE_PROJECT_CONFIG": project_config_dir
    }

    # 2. Environment variables for VS Code Integrated Terminals
    term_env_posix = {
        "SVND_SCRIBE_HOME": scribe_home,
        "PYTHONPATH": f"{python_path_env}:${{env:PYTHONPATH}}",
        "SV_ND_SCRIBE_PROJECT_CONFIG": project_config_dir
    }
    term_env_win = {
        "SVND_SCRIBE_HOME": scribe_home,
        "PYTHONPATH": f"{python_path_env};${{env:PYTHONPATH}}",
        "SV_ND_SCRIBE_PROJECT_CONFIG": project_config_dir
    }
    updated_settings["terminal.integrated.env.linux"] = term_env_posix
    updated_settings["terminal.integrated.env.osx"] = term_env_posix
    updated_settings["terminal.integrated.env.windows"] = term_env_win

    # 3. Python extension environment file
    updated_settings["python.envFile"] = "${workspaceFolder}/.env"

    # 4. File associations for SystemVerilog / Verilog
    file_associations = updated_settings.get("files.associations", {})
    if not isinstance(file_associations, dict):
        file_associations = {}
    if "*.sv" not in file_associations:
        file_associations["*.sv"] = "systemverilog"
    if "*.svh" not in file_associations:
        file_associations["*.svh"] = "systemverilog"
    if "*.v" not in file_associations:
        file_associations["*.v"] = "verilog"
    updated_settings["files.associations"] = file_associations

    # Save settings.json
    save_settings(settings_path, updated_settings)

    # 5. Write workspace root .env file with resolved absolute paths
    raw_env_vars = {
        "SVND_SCRIBE_HOME": workspace_dir,
        "PYTHONPATH": workspace_dir,
        "SV_ND_SCRIBE_PROJECT_CONFIG": os.path.join(workspace_dir, "linter", "configs")
    }
    write_env_file(env_file_path, raw_env_vars)

    # 6. Write makedir/env.sh for shell sourcing
    write_env_sh(env_sh_path, raw_env_vars)

    print("=================================================================")
    print("  SV ND Scribe — Workspace & Environment Setup")
    print("=================================================================")
    print(f"Target settings file : {settings_path}")
    print(f"Workspace .env file  : {env_file_path}")
    print(f"Shell source script  : {env_sh_path}")
    print()
    print("Configured Extension Properties:")
    print(f"  sv-nd-scribe.linterPath          : {linter_path}")
    print(f"  sv-nd-scribe.agentPath           : {agent_path}")
    print(f"  sv-nd-scribe.pythonPath          : {python_path}")
    print(f"  sv-nd-scribe.runOn               : {args.run_on}")
    print(f"  sv-nd-scribe.enableQuickFix      : {enable_quick_fix}")
    print()
    print("Configured Environment Variables:")
    print(f"  SVND_SCRIBE_HOME                 : {workspace_dir}")
    print(f"  PYTHONPATH                       : {workspace_dir}")
    print(f"  SV_ND_SCRIBE_PROJECT_CONFIG      : {os.path.join(workspace_dir, 'linter', 'configs')}")
    print()
    print("  terminal.integrated.env.*        : Linux/macOS/Windows terminal env configured")
    print("  python.envFile                   : ${workspaceFolder}/.env")
    print("  files.associations               : *.sv, *.svh -> systemverilog, *.v -> verilog")
    print("=================================================================")

if __name__ == "__main__":
    main()