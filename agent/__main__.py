# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import sys
import json
import argparse

# Add parent directory to path so agent can be executed via python3 -m agent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import ScribeAgent
from agent.fixer.base_fixer import LinterError
from agent.setup_agent import SetupAgent

def parse_manifest_file(manifest_path: str) -> list:
    files = []
    manifest_dir = os.path.dirname(os.path.abspath(manifest_path))
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                line = os.path.expandvars(line)
                line = line.split("//")[0].split("#")[0].strip()
                if not line or line.startswith("+") or line.startswith("-"):
                    continue
                path = line
                if not os.path.isabs(path):
                    if not os.path.exists(path) and os.path.exists(os.path.join(manifest_dir, path)):
                        path = os.path.join(manifest_dir, path)
                files.append(path)
    except Exception as e:
        print(f"[agent] Error reading manifest file {manifest_path}: {e}", file=sys.stderr)
        sys.exit(1)
    return files

def main():
    parser = argparse.ArgumentParser(description="SV ND Scribe: SystemVerilog NaturalDocs AI Agent")
    parser.add_argument("files", nargs="*", help="SystemVerilog files to analyze and fix (.sv, .svh)")
    parser.add_argument("-f", "--file-list", help="Read files from a .f manifest file")
    parser.add_argument("--interactive", action="store_true", help="Prompt before applying each fix (default mode)")
    parser.add_argument("--batch", action="store_true", help="Apply all safe fixes without prompting")
    parser.add_argument("--dry-run", action="store_true", help="Print diff/proposals without writing to files")
    parser.add_argument("--rules", help="Restrict fixes to comma-separated rule IDs (e.g. ND-009,WKL-005)")
    parser.add_argument("--llm", default="none", help="Select LLM provider: none | openai | ollama (default: none)")
    parser.add_argument("--json", action="store_true", help="Output results in machine-readable JSON format")
    parser.add_argument("--skills-dir", help="Phase 2 override skills directory path")
    parser.add_argument("--rules-dir", help="Phase 2 override rules directory path")
    parser.add_argument("--no-backup", action="store_true", help="Disable all backup writes (CI mode)")
    parser.add_argument("--debug-llm", action="store_true", help="Dump LLM prompts and raw responses to log file")
    parser.add_argument("-c", "--config", help="Path to configuration file (JSON)")
    parser.add_argument("--status", action="store_true", help="Check LLM connectivity and active skill/rule paths")
    parser.add_argument("--doctor", action="store_true", help="Diagnose environment, dependencies, and workspace setup")
    parser.add_argument("--fix-setup", action="store_true", help="Automatically repair workspace configuration and environment")
    parser.add_argument("--open-header-template", action="store_true", help="Print path and content of active header_template.txt")
    parser.add_argument("--reset-header-template", action="store_true", help="Reset active header_template.txt to built-in default")
    parser.add_argument("--overwrite-header", action="store_true", help="Force overwrite file header from template")

    args = parser.parse_args()

    # Reject Phase 2 override directories in Phase 1
    if args.skills_dir or args.rules_dir:
        print("[agent] Error: --skills-dir and --rules-dir overrides are Phase 2 features and not supported in Phase 1 MVP.", file=sys.stderr)
        sys.exit(1)

    if args.doctor:
        setup_agent = SetupAgent()
        exit_code = setup_agent.print_doctor_report(as_json=args.json)
        sys.exit(exit_code)

    if args.fix_setup:
        setup_agent = SetupAgent()
        res = setup_agent.fix_setup()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("=================================================================")
            print("  SV ND Scribe — Setup Auto-Repair")
            print("=================================================================")
            for act in res.get("actions", []):
                print(f"  • {act}")
            print()
            exit_code = setup_agent.print_doctor_report(as_json=False)
            print("=================================================================")
        sys.exit(0 if res.get("success") else 1)

    agent = ScribeAgent(config_file=args.config)

    if args.open_header_template:
        tpath = agent.get_header_template_path(args.files[0] if args.files else None)
        print(f"Header Template Path: {tpath}")
        if os.path.exists(tpath):
            with open(tpath, "r", encoding="utf-8") as f:
                print(f.read())
        sys.exit(0)

    if args.reset_header_template:
        tpath = agent.reset_header_template(args.files[0] if args.files else None)
        print(f"Reset header template at: {tpath}")
        sys.exit(0)

    if args.status:
        exit_code = agent.run(files=[], status_check=True, llm_provider=args.llm)
        sys.exit(exit_code)

    files_to_fix = []
    if args.file_list:
        files_to_fix.extend(parse_manifest_file(args.file_list))
    if args.files:
        files_to_fix.extend(args.files)

    if not files_to_fix:
        parser.error("No input files specified. Provide files as positional arguments, use -f/--file-list, or run --doctor / --fix-setup.")

    rules_filter = None
    if args.rules:
        rules_filter = [r.strip() for r in args.rules.split(",") if r.strip()]

    mode = "batch" if args.batch else "interactive"

    try:
        exit_code = agent.run(
            files=files_to_fix,
            mode=mode,
            rules_filter=rules_filter,
            llm_provider=args.llm,
            no_backup=args.no_backup,
            dry_run=args.dry_run,
            json_output=args.json,
            debug_llm=args.debug_llm,
            overwrite_header=args.overwrite_header,
        )
        sys.exit(exit_code)
    except LinterError as e:
        print(f"[agent] Fatal linter error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[agent] Aborted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[agent] Unexpected runtime error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()