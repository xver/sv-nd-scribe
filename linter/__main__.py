# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import sys
import argparse

# Add the parent directory to the path so that 'linter' can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linter.core.linter_registry import get_registry
from linter.core.config_manager import ConfigManager

def parse_manifest_file(manifest_path):
    files = []
    manifest_dir = os.path.dirname(os.path.abspath(manifest_path))
    try:
        with open(manifest_path, 'r') as f:
            for line in f:
                # Expand environment variables first
                line = os.path.expandvars(line)
                # Remove comments starting with // or #
                line = line.split('//')[0].split('#')[0].strip()
                if not line:
                    continue
                # Ignore compiler flags like +incdir+, -v, etc.
                if line.startswith('+') or line.startswith('-'):
                    continue
                
                path = line
                if not os.path.isabs(path):
                    # Check if path exists relative to CWD, otherwise resolve relative to the manifest directory
                    if not os.path.exists(path) and os.path.exists(os.path.join(manifest_dir, path)):
                        path = os.path.join(manifest_dir, path)
                files.append(path)
    except Exception as e:
        print(f"Error reading manifest file {manifest_path}: {e}")
        sys.exit(1)
    return files

def main():
    parser = argparse.ArgumentParser(description="SV ND Scribe: SystemVerilog NaturalDocs Linter")
    parser.add_argument("files", nargs="*", help="SystemVerilog files to lint (.sv, .svh)")
    parser.add_argument("-f", "--file-list", help="Read files to lint from a .f manifest file")
    parser.add_argument("-c", "--config", help="Path to project/root configuration file (JSON)")
    parser.add_argument("-o", "--log-file", default="linter.log", help="Write lint results to a log file (default: linter.log)")
    parser.add_argument("--json", action="store_true", help="Output lint results in JSON format")
    parser.add_argument("--fail-on-warnings", action="store_true", help="Return non-zero exit code on warnings")
    parser.add_argument("--status", action="store_true", help="Check linter environment and dependencies")
    
    args = parser.parse_args()
    
    if args.status:
        if "SVND_SCRIBE_HOME" not in os.environ:
            print("Error: SVND_SCRIBE_HOME environment variable is missing. It is required for external tool integrations (like the VS Code extension).")
            sys.exit(1)
            
        config_mgr = ConfigManager(config_file=args.config)
        linter_config = config_mgr.get_linter_config("naturaldoc_linter")
        registry = get_registry()
        linter_instance = registry.get_linter("naturaldoc_linter", config=linter_config)
        if not linter_instance:
            print("Error: naturaldoc_linter is unavailable. Is verible-verilog-syntax installed and in your PATH?")
            sys.exit(1)
        else:
            print("OK: Linter dependencies satisfied and SVND_SCRIBE_HOME is set.")
            sys.exit(0)
            
    files_to_lint = []
    if args.file_list:
        files_to_lint.extend(parse_manifest_file(args.file_list))
    if args.files:
        files_to_lint.extend(args.files)
        
    if not files_to_lint:
        parser.error("No input files specified. Provide files as arguments or use -f/--file-list.")
    
    config_mgr = ConfigManager(config_file=args.config)
    linter_config = config_mgr.get_linter_config("naturaldoc_linter")

    registry = get_registry()
    linter_instance = registry.get_linter("naturaldoc_linter", config=linter_config)
    
    if not linter_instance:
        print("Error: naturaldoc_linter is unavailable. Is verible-verilog-syntax installed and in your PATH?")
        sys.exit(1)
        
    result = linter_instance.lint_files(files_to_lint)
    
    # Print results
    if args.json:
        print(result.format_json(), end="")
    else:
        print(result.format_report(), end="")
    
    # Write log file if requested
    if args.log_file:
        result.write_log(args.log_file)
        if not args.json:
            print(f"Log written to: {args.log_file}")
            
    # Exit with appropriate code
    if result.error_count > 0 or result.files_failed > 0:
        sys.exit(1)
    if args.fail_on_warnings and result.warning_count > 0:
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
