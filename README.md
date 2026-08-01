# SV ND Scribe
SV ND Scribe is a SystemVerilog toolkit that combines NaturalDocs-based documentation rules, a static linter for detecting issues in source files, a VS Code extension for real-time in-editor feedback, and an AI agent that helps resolve issues identified by the linter.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Running the Linter](#running-the-linter)
  - [Makefile Usage](#makefile-usage)
  - [Standalone CLI Execution](#standalone-cli-execution)
  - [Manifest File Format (.f)](#manifest-file-format-f)
  - [Usage in Python](#usage-in-python)
- [Linting Rules](#linting-rules)
- [VS Code Extension](#vs-code-extension)
  - [Option 1: Install from the pre-built .vsix](#option-1-install-from-the-pre-built-vsix)
  - [Option 2: Build and install from source](#option-2-build-and-install-from-source)
  - [Extension Configuration](#extension-configuration)
- [AI Agent](#ai-agent-todo)

## Prerequisites

To use the static linter, you must have the following installed:

1. **Python 3** (3.7+)
2. **Verible** - specifically the `verible-verilog-syntax` executable.
   - You can download Verible from the [ChipsAlliance GitHub releases page](https://github.com/chipsalliance/verible/releases).
   - Ensure the executable (`verible-verilog-syntax` or `verible-verilog-syntax.exe`) is available in your system's `PATH`.
   - Alternatively, you can specify its location by setting the `VERIBLE_HOME` environment variable to the directory where it's installed (the linter will look in `$VERIBLE_HOME/bin/` and `$VERIBLE_HOME/`).
   - *Note: If you're running this in WSL, a Windows installation of Verible (.exe) in your PATH is fully supported.*
3. **SVND_SCRIBE_HOME** (Mandatory)
   - Set this environment variable to the root directory of this downloaded repository.
   - The VS Code extension and other tools require this variable to locate the linter scripts and configurations.

## Running the Linter

### Makefile Usage

A `Makefile` is provided in the `makedir/` directory for convenient project-level automation. Run all targets from inside `makedir/`:

```bash
cd makedir
make <target>
```

| Target      | Description |
|-------------|-------------|
| `all`       | Runs both `nd` (NaturalDocs generation) and `lint` (production files). |
| `nd`        | Generates NaturalDocs HTML documentation from `docs/nd_config/`. Requires `ND_HOME` to be set. |
| `lint`      | Lints the production template files listed in `template_sv.f`. Exits non-zero on errors. |
| `lint_bad`  | Lints the negative-test files in `test_bad_sv.f`. Used to verify that all rules are triggered. |
| `status`    | Checks the linter environment and verifies all dependencies are satisfied. |
| `vscode`    | Compiles and packages the VS Code extension into a `.vsix` file. |
| `help`      | Displays a formatted summary of all Makefile targets and configurable variables. |

**Variables** (can be overridden on the command line):

| Variable     | Default          | Description |
|--------------|------------------|-------------|
| `ND_HOME`    | *(env var)*      | Path to the NaturalDocs installation directory (must contain the `NaturalDocs` executable). |
| `PYTHON`     | `python3`        | Python interpreter to use when running the linter. |
| `LOG_FILE`   | `linter.log`     | Output log file for the `lint` target. |
| `LOG_BAD_FILE` | `linter_bad.log` | Output log file for the `lint_bad` target. |

**Example:**
```bash
# Generate docs + lint production files
make all

# Lint with a custom Python path and log file
make lint PYTHON=/usr/bin/python3.11 LOG_FILE=my_run.log

# Verify all negative-test rules fire
make lint_bad
```

### Standalone CLI Execution

You can run the linter directly from the command line against your source files by executing `python3 -m linter` or `linter/linter.py`.

```bash
# Display help information
python3 -m linter --help

# Check linter environment and dependencies
python3 -m linter --status

# Run against one or more files
python3 -m linter example/good_example.sv path/to/other_file.sv

# Run in batch mode using a .f manifest file
python3 -m linter -f example/manifest.f

# Run with a custom JSON configuration file
python3 -m linter -f example/manifest.f -c configs/lint_config.json

# Output results in JSON format
python3 -m linter -f example/manifest.f --json
```

### Manifest File Format (.f)

The `.f` manifest file allows batch processing. The parser supports:
* One file path per line (resolved relative to the command execution directory or the manifest file directory).
* Environment variable expansion (e.g. `$MY_PROJECT/src/file.sv`).
* Inline and block comments starting with `//` or `#`.
* Ignoring compiler flags (lines starting with `+` or `-`).

This script also works if you invoke it from outside the project directory:

```bash
# Run from any directory
python3 -m linter -f /path/to/manifest.f
```

### Usage in Python

See [linter/PYTHON_USAGE.md](linter/PYTHON_USAGE.md) for a guide on integrating the linter into your own Python scripts.

## Linting Rules

The linter enforces 40 rules across two categories: **Wellknown (WKL)** style/formatting rules (8 rules) and **NaturalDocs (ND)** documentation rules (32 rules).

See the full rule reference: [linter/rules/RULES.md](linter/rules/RULES.md)

## VS Code Extension

A pre-built VS Code extension is included in the `vscode/` directory. It provides real-time in-editor diagnostics for SystemVerilog files by running the linter on every file save.

### Option 1: Install from the pre-built .vsix

The packaged extension file is located at `vscode/sv-nd-scribe-vscode-0.1.0.vsix`.

**Via VS Code UI:**
1. Open VS Code.
2. Press `Ctrl+Shift+P` (macOS: `Cmd+Shift+P`) to open the Command Palette.
3. Type and select **`Extensions: Install from VSIX...`**.
4. Browse to `sv-nd-scribe/vscode/sv-nd-scribe-vscode-0.1.0.vsix` and click **Install**.
5. Reload VS Code when prompted.

**Via the command line:**
```bash
code --install-extension /path/to/sv-nd-scribe/vscode/sv-nd-scribe-vscode-0.1.0.vsix
```

### Option 2: Build and install from source

If you want to rebuild the `.vsix` from source (requires Node.js):
```bash
cd vscode
npx -y @vscode/vsce package
code --install-extension sv-nd-scribe-vscode-0.1.0.vsix
```

### Extension Configuration

After installation, configure the extension via VS Code Settings (`Ctrl+,`) by searching for `sv-nd-scribe`:

| Setting | Default | Description |
|---|---|---|
| `sv-nd-scribe.linterPath` | `""` | Absolute path to `linter.py`. If empty, it automatically falls back to `$SVND_SCRIBE_HOME/linter/linter.py`. |
| `sv-nd-scribe.pythonPath` | `python3` | Path to your Python interpreter |
| `sv-nd-scribe.runOn` | `onSave` | When to trigger linting: `onSave` or `onOpen` |

### Extension Commands

In addition to automatically linting in the background, you can manually trigger the following actions via the VS Code Command Palette (`Ctrl+Shift+P`):

- **`SV_Scribe: Lint`**: Lints the currently active SystemVerilog file immediately.
- **`SV_Scribe: Clear`**: Clears any diagnostic underlines from the current document.
- **`SV_Scribe: Lint_All`**: Runs the linter across every SystemVerilog file you currently have open in your workspace.
- **`SV_Scribe: Status`** (alias: **`SV_Scribe: Verify linter installation`**): Verifies your environment by checking if the linter script exists and if its dependencies are satisfied.

## AI Agent *(TODO)*

> **TODO**: This section is planned and not yet implemented.

SV ND Scribe includes an AI agent component that will automatically analyze linter violations and suggest or apply fixes directly in your SystemVerilog source files.

**Planned capabilities:**

- Parse linter output and triage violations by rule and severity
- Propose NaturalDocs comment blocks for undocumented constructs
- Auto-generate missing file headers, group headings, and inline documentation
- Interactive mode: review and accept/reject each suggested fix
- Batch mode: apply all safe fixes automatically
