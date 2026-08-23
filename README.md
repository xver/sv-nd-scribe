# Welcome to sv-nd-scribe - NaturalDocs and Linting for SystemVerilog! ![](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)

![sv-nd-scribe Logo](scribe_logo.jpg)

Never write undocumented or unformatted SystemVerilog again.

The **sv-nd-scribe** toolkit combines NaturalDocs-based documentation rules, a static linter for detecting issues in source files, a VS Code extension for real-time in-editor feedback, and an AI agent that helps resolve issues identified by the linter. **sv-nd-scribe** is available under the MIT License and can be used without restriction in both open-source and commercial applications.

Also, check out other open-source projects by IC Verimeter.

- [The Shunt](https://github.com/xver/Shunt): An Open Source Client/Server TCP/IP socket-based communication library designed for integrating SystemVerilog simulations with external applications in C, SystemC, and Python.
- [SVDB Gateway](https://github.com/xver/svdb_gateway): A bridge between SystemVerilog and SQLite databases, allowing SystemVerilog code to interact with SQLite through the Direct Programming Interface (DPI).
- [icecream_sv](https://github.com/xver/icecream_sv): IceCream for SystemVerilog!

## Why use sv-nd-scribe?

* **Consistent Documentation**: Enforce NaturalDocs rules across your SystemVerilog files.
* **Real-time Feedback**: Use the VS Code extension for on-the-fly linting and quick-fixes.
* **Lightweight & Portable**: Standard Python implementation, fits seamlessly into Makefiles.
* **AI Assistance**: AI agent with deterministic and LLM-assisted options to resolve issues and generate missing comments automatically.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Running the Linter](#running-the-linter)
  - [Makefile Usage](#makefile-usage)
  - [Standalone CLI Execution](#standalone-cli-execution)
  - [Manifest File Format (.f)](#manifest-file-format-f)
  - [Usage in Python](#usage-in-python)
- [Linting Rules](#linting-rules)
- [VS Code Extension](#vs-code-extension)
  - [Option 1: Install from Extension View (TODO)](#option-1-install-from-extension-view-todo)
  - [Option 2: Install from the pre-built .vsix](#option-2-install-from-the-pre-built-vsix)
  - [Extension Configuration](#extension-configuration)
- [AI Agent](#ai-agent)
- [Support](#support)

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

For full details, see the [VS Code Extension README](vscode/README.md).

A pre-built VS Code extension is included in the `vscode/` directory. It provides real-time in-editor diagnostics for SystemVerilog files by running the linter on every file save.

### Option 1: Install from Extension View *(TODO)*

> **TODO**: The extension is not yet published.

Once published, you will be able to download and install the extension directly from IDEs (VS Code, Antigravity, Cursor, etc.) by searching for **SV ND Scribe** in the Extensions view (`Ctrl+Shift+X`) and clicking **Install**.

### Option 2: Install from the pre-built .vsix

The packaged extension file is located at `vscode/sv-nd-scribe-vscode-*.vsix`.

**Via VS Code UI:**
1. Open VS Code.
2. Press `Ctrl+Shift+P` (macOS: `Cmd+Shift+P`) to open the Command Palette.
3. Type and select **`Extensions: Install from VSIX...`**.
4. Browse to `sv-nd-scribe/vscode/sv-nd-scribe-vscode-*.vsix` and click **Install**.
5. Reload VS Code when prompted.

**Via the command line:**
```bash
code --install-extension /path/to/sv-nd-scribe/vscode/sv-nd-scribe-vscode-*.vsix
```

### Extension Configuration

After installation, configure the extension via VS Code Settings (`Ctrl+,`) by searching for `sv-nd-scribe`:

| Setting | Default | Description |
|---|---|---|
| `sv-nd-scribe.linterPath` | `""` | Absolute path to `linter.py`. If empty, it automatically falls back to `$SVND_SCRIBE_HOME/linter/linter.py`. |
| `sv-nd-scribe.pythonPath` | `python3` | Path to your Python interpreter |
| `sv-nd-scribe.runOn` | `onSave` | When to trigger linting: `onSave` or `onOpen` |
| `sv-nd-scribe.agentLlmProvider` | `none` | LLM backend selection for AI quick-fixes (`none`, `openai`, `ollama`) |
| `sv-nd-scribe.agentLlmModel` | `""` | Model name override (e.g. `llama3.2`, `gpt-4o-mini`) |
| `sv-nd-scribe.agentFixMode` | `interactive` | Default fix mode for agent command execution (`interactive`, `batch`, `dryRun`) |
| `sv-nd-scribe.agentBackup` | `auto` | Backup strategy when modifying files (`auto`, `always`, `never`) |
| `sv-nd-scribe.agentShowDiffPreview` | `true` | Show diff preview panel before applying AI fixes |

### Extension Commands

In addition to automatically linting in the background, you can manually trigger the following actions via the VS Code Command Palette (`Ctrl+Shift+P`):

- **`SV_Scribe: Lint`**: Lints the currently active SystemVerilog file immediately.
- **`SV_Scribe: Clear`**: Clears any diagnostic underlines from the current document.
- **`SV_Scribe: Lint_All`**: Runs the linter across every SystemVerilog file you currently have open in your workspace.
- **`SV_Scribe: Status`** (alias: **`SV_Scribe: Verify linter installation`**): Verifies your environment by checking if the linter script exists and if its dependencies are satisfied.
- **`SV_Scribe: Fix Current File`**: Runs the AI Agent to analyze and fix issues in the active document.
- **`SV_Scribe: Batch Fix Current File`**: Applies all safe deterministic fixes to the active document without prompting.
- **`SV_Scribe: Show Agent Status`**: Displays the AI agent status, backend LLM provider, and loaded rules/skills.

## AI Agent

The **SV ND Scribe AI Agent** automatically analyzes linter violations and applies or proposes NaturalDocs documentation and formatting fixes directly in SystemVerilog source files. It features a portable, multi-LLM backend (`none`, `openai`, `ollama`) and data-driven rule/skill definitions.

### CLI Usage

```bash
# Deterministic batch fix (CI mode, no backup files)
python3 -m agent --llm none --batch --no-backup -f manifest.f

# Check agent connectivity and status
python3 -m agent --status

# Preview proposed fixes without writing to disk
python3 -m agent --llm none --dry-run file.sv
```

### VS Code Quick-Fixes

When editing SystemVerilog files in VS Code, clicking the lightbulb icon (`Ctrl+.`) on any diagnostic presents quick-fixes:
- **`💡 SV_Scribe: Fix (deterministic)`**: Instantly applies deterministic formatting/comment fixes without calling an LLM.
- **`🤖 SV_Scribe: Fix with AI (<provider>)`**: Uses configured LLM backend for intelligent description generation.

## Support

For assistance with integration or customization, contact us at [icshunt.help@gmail.com](mailto:icshunt.help@gmail.com).

Report bugs to [Issues](https://github.com/xver/sv-nd-scribe/issues).

---

![img](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![img](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)
Copyright (c) 2026 IC Verimeter
